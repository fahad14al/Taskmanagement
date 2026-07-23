# workspace/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .models import (
    Organization, Department, Team, TeamMember,
    Project, ProjectMember, Sprint,
    Task, SubTask, Checklist, ChecklistItem,
    Ticket, Attachment
)
from accounts.models import Role, Permission, Profile

# ========================================
# 1. Role, Permission Serializer
# ========================================

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name', 'get_name_display', 'description', 'created_at']
        read_only_fields = ['id', 'created_at']

class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['id', 'name', 'get_name_display', 'description']
        read_only_fields = ['id']

# ========================================
# 2. Profile Serializer
# ========================================

class ProfileSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only=True)
    role_id = serializers.PrimaryKeyRelatedField(
        source='role', 
        queryset=Role.objects.all(), 
        write_only=True, 
        required=False
    )
    permissions = PermissionSerializer(many=True, read_only=True)
    permission_ids = serializers.PrimaryKeyRelatedField(
        source='permissions', 
        queryset=Permission.objects.all(), 
        many=True, 
        write_only=True, 
        required=False
    )

    class Meta:
        model = Profile
        fields = [
            'id', 'phone', 'address', 'profile_picture', 
            'role', 'role_id', 'permissions', 'permission_ids',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

# ========================================
# 3. User Serializer (Registration and Profile)
# ========================================

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password2 = serializers.CharField(
        write_only=True, 
        required=True, 
        style={'input_type': 'password'},
        label="Confirm Password"
    )
    profile = ProfileSerializer(required=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'password2', 'profile']
        extra_kwargs = {
            'email': {'required': True, 'allow_blank': False},
            'username': {'required': True, 'allow_blank': False}
        }

    def validate(self, attrs):
        """Checks if passwords match"""
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        """Creates user and sets profile"""
        profile_data = validated_data.pop('profile', {})
        validated_data.pop('password2')  # password2 not needed
        
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
        
        # Update profile
        profile = user.profile
        
        if 'role' in profile_data and profile_data['role']:
            profile.role = profile_data['role']
        
        if 'permissions' in profile_data:
            profile.permissions.set(profile_data['permissions'])
        
        if 'phone' in profile_data:
            profile.phone = profile_data.get('phone', '')
        if 'address' in profile_data:
            profile.address = profile_data.get('address', '')
        
        profile.save()
        return user

    def to_representation(self, instance):
        """To show profile data in response"""
        data = super().to_representation(instance)
        data['profile'] = ProfileSerializer(instance.profile).data
        return data

class UserProfileSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'profile']
        read_only_fields = ['id', 'username', 'email']

class UserUpdateSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(required=False)
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'profile']
    
    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', {})
        
        # User update
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.email = validated_data.get('email', instance.email)
        instance.save()
        
        # Profile update
        profile = instance.profile
        if profile_data:
            if 'phone' in profile_data:
                profile.phone = profile_data.get('phone', profile.phone)
            if 'address' in profile_data:
                profile.address = profile_data.get('address', profile.address)
            if 'role' in profile_data:
                profile.role = profile_data.get('role', profile.role)
            if 'permissions' in profile_data:
                profile.permissions.set(profile_data.get('permissions', []))
            profile.save()
        
        return instance

# ========================================
# 4. Organization Serializer
# ========================================

class OrganizationListSerializer(serializers.ModelSerializer):
    """Organization summary info"""
    created_by_username = serializers.ReadOnlyField(source='created_by.username')
    
    class Meta:
        model = Organization
        fields = ['id', 'name', 'slug', 'logo', 'email', 'phone', 'is_active', 'created_by_username', 'created_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class OrganizationDetailSerializer(serializers.ModelSerializer):
    """Organization detail info"""
    created_by_username = serializers.ReadOnlyField(source='created_by.username')
    departments_count = serializers.SerializerMethodField()
    projects_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Organization
        fields = [
            'id', 'name', 'slug', 'description', 'logo', 'website', 
            'email', 'phone', 'address', 'created_by', 'created_by_username',
            'departments_count', 'projects_count', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_departments_count(self, obj):
        return obj.departments.filter(is_active=True).count()
    
    def get_projects_count(self, obj):
        return obj.projects.filter(is_active=True).count()

class OrganizationCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = [
            'name', 'slug', 'description', 'logo', 'website', 
            'email', 'phone', 'address', 'is_active'
        ]
    
    def validate_slug(self, value):
        """Checks if slug is unique"""
        if Organization.objects.filter(slug=value).exists():
            raise serializers.ValidationError("This slug is already in use.")
        return value

# ========================================
# 5. Department Serializer
# ========================================

class DepartmentSerializer(serializers.ModelSerializer):
    organization_name = serializers.ReadOnlyField(source='organization.name')
    head_username = serializers.ReadOnlyField(source='head.username')
    teams_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Department
        fields = [
            'id', 'name', 'description', 'organization', 'organization_name',
            'head', 'head_username', 'teams_count', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_teams_count(self, obj):
        return obj.teams.filter(is_active=True).count()

# ========================================
# 6. Team Serializer
# ========================================

class TeamSerializer(serializers.ModelSerializer):
    department_name = serializers.ReadOnlyField(source='department.name')
    lead_username = serializers.ReadOnlyField(source='lead.username')
    members_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Team
        fields = [
            'id', 'name', 'description', 'department', 'department_name',
            'lead', 'lead_username', 'members_count', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_members_count(self, obj):
        return obj.members.filter(is_active=True).count()

class TeamDetailSerializer(TeamSerializer):
    """ (Members )"""
    members = serializers.SerializerMethodField()
    
    class Meta(TeamSerializer.Meta):
        fields = TeamSerializer.Meta.fields + ['members']
    
    def get_members(self, obj):
        members = obj.members.filter(is_active=True)
        return TeamMemberSerializer(members, many=True).data

# ========================================
# 7. TeamMember Serializer
# ========================================

class TeamMemberSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source='user.username')
    user_email = serializers.ReadOnlyField(source='user.email')
    full_name = serializers.SerializerMethodField()
    role_display = serializers.ReadOnlyField(source='get_role_display')
    
    class Meta:
        model = TeamMember
        fields = [
            'id', 'team', 'user', 'username', 'user_email', 'full_name',
            'role', 'role_display', 'joined_at', 'is_active'
        ]
        read_only_fields = ['id', 'joined_at']
    
    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username

# ========================================
# 8. Project Serializer
# ========================================

class ProjectListSerializer(serializers.ModelSerializer):
    """Project summary info"""
    organization_name = serializers.ReadOnlyField(source='organization.name')
    project_manager_username = serializers.ReadOnlyField(source='project_manager.username')
    status_display = serializers.ReadOnlyField(source='get_status_display')
    priority_display = serializers.ReadOnlyField(source='get_priority_display')
    
    class Meta:
        model = Project
        fields = [
            'id', 'name', 'slug', 'organization', 'organization_name',
            'status', 'status_display', 'priority', 'priority_display',
            'progress', 'project_manager', 'project_manager_username',
            'start_date', 'end_date', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class ProjectDetailSerializer(serializers.ModelSerializer):
    """Project detail info"""
    organization_name = serializers.ReadOnlyField(source='organization.name')
    department_name = serializers.ReadOnlyField(source='department.name')
    team_name = serializers.ReadOnlyField(source='team.name')
    project_manager_username = serializers.ReadOnlyField(source='project_manager.username')
    status_display = serializers.ReadOnlyField(source='get_status_display')
    priority_display = serializers.ReadOnlyField(source='get_priority_display')
    
    members_count = serializers.SerializerMethodField()
    tasks_count = serializers.SerializerMethodField()
    sprints_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = [
            'id', 'name', 'slug', 'description', 'organization', 'organization_name',
            'department', 'department_name', 'team', 'team_name',
            'status', 'status_display', 'priority', 'priority_display',
            'progress', 'project_manager', 'project_manager_username',
            'start_date', 'end_date', 'actual_end_date',
            'members_count', 'tasks_count', 'sprints_count',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_members_count(self, obj):
        return obj.members.filter(is_active=True).count()
    
    def get_tasks_count(self, obj):
        return obj.tasks.filter(is_active=True).count()
    
    def get_sprints_count(self, obj):
        return obj.sprints.count()

class ProjectCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = [
            'name', 'slug', 'description', 'organization', 'department', 'team',
            'status', 'priority', 'start_date', 'end_date', 'project_manager', 'is_active'
        ]
    
    def validate(self, data):
        """Checks if start date is before end date"""
        if data.get('start_date') and data.get('end_date') and data['start_date'] > data['end_date']:
            raise serializers.ValidationError({
                'end_date': 'End date must be after start date.'
            })
        return data
    
    def validate_slug(self, value):
        if Project.objects.filter(slug=value).exists():
            raise serializers.ValidationError("This slug is already in use.")
        return value

# ========================================
# 9. ProjectMember Serializer
# ========================================

class ProjectMemberSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source='user.username')
    user_email = serializers.ReadOnlyField(source='user.email')
    full_name = serializers.SerializerMethodField()
    role_display = serializers.ReadOnlyField(source='get_role_display')
    
    class Meta:
        model = ProjectMember
        fields = [
            'id', 'project', 'user', 'username', 'user_email', 'full_name',
            'role', 'role_display', 'joined_at', 'is_active'
        ]
        read_only_fields = ['id', 'joined_at']
    
    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username

# ========================================
# 10. Sprint Serializer
# ========================================

class SprintSerializer(serializers.ModelSerializer):
    project_name = serializers.ReadOnlyField(source='project.name')
    status_display = serializers.ReadOnlyField(source='get_status_display')
    progress_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = Sprint
        fields = [
            'id', 'name', 'goal', 'project', 'project_name',
            'start_date', 'end_date', 'actual_end_date',
            'status', 'status_display',
            'total_story_points', 'completed_story_points',
            'progress_percentage', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_progress_percentage(self, obj):
        """Calculates progress percentage"""
        if obj.total_story_points > 0:
            return int((obj.completed_story_points / obj.total_story_points) * 100)
        return 0

class SprintCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sprint
        fields = [
            'name', 'goal', 'project', 'start_date', 'end_date', 'status',
            'total_story_points', 'completed_story_points'
        ]
    
    def validate(self, data):
        """Checks if start date is before end date"""
        if data.get('start_date') and data.get('end_date') and data['start_date'] > data['end_date']:
            raise serializers.ValidationError({
                'end_date': 'End date must be after start date.'
            })
        return data

# ========================================
# 11. Task Serializer
# ========================================

class TaskListSerializer(serializers.ModelSerializer):
    """Task summary info"""
    project_name = serializers.ReadOnlyField(source='project.name')
    sprint_name = serializers.ReadOnlyField(source='sprint.name')
    assignee_username = serializers.ReadOnlyField(source='assignee.username')
    status_display = serializers.ReadOnlyField(source='get_status_display')
    priority_display = serializers.ReadOnlyField(source='get_priority_display')
    task_type_display = serializers.ReadOnlyField(source='get_task_type_display')
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'project', 'project_name', 'sprint', 'sprint_name',
            'task_type', 'task_type_display', 'status', 'status_display',
            'priority', 'priority_display', 'assignee', 'assignee_username',
            'story_points', 'due_date', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class TaskDetailSerializer(serializers.ModelSerializer):
    """Task detail info"""
    project_name = serializers.ReadOnlyField(source='project.name')
    sprint_name = serializers.ReadOnlyField(source='sprint.name')
    assignee_username = serializers.ReadOnlyField(source='assignee.username')
    reporter_username = serializers.ReadOnlyField(source='reporter.username')
    parent_task_title = serializers.ReadOnlyField(source='parent_task.title')
    status_display = serializers.ReadOnlyField(source='get_status_display')
    priority_display = serializers.ReadOnlyField(source='get_priority_display')
    task_type_display = serializers.ReadOnlyField(source='get_task_type_display')
    
    subtasks_count = serializers.SerializerMethodField()
    checklists_count = serializers.SerializerMethodField()
    tickets_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'project', 'project_name',
            'sprint', 'sprint_name', 'parent_task', 'parent_task_title',
            'task_type', 'task_type_display', 'status', 'status_display',
            'priority', 'priority_display', 'assignee', 'assignee_username',
            'reporter', 'reporter_username', 'story_points',
            'time_estimated', 'time_spent',
            'due_date', 'start_date', 'completed_date',
            'subtasks_count', 'checklists_count', 'tickets_count',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_subtasks_count(self, obj):
        return obj.subtasks.count()
    
    def get_checklists_count(self, obj):
        return obj.checklists.count()
    
    def get_tickets_count(self, obj):
        return obj.tickets.count()

class TaskCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'project', 'sprint', 'parent_task',
            'task_type', 'status', 'priority', 'assignee', 'reporter',
            'story_points', 'time_estimated', 'time_spent',
            'due_date', 'start_date', 'completed_date', 'is_active'
        ]

# ========================================
# 12. SubTask Serializer
# ========================================

class SubTaskSerializer(serializers.ModelSerializer):
    task_title = serializers.ReadOnlyField(source='task.title')
    assignee_username = serializers.ReadOnlyField(source='assignee.username')
    status_display = serializers.ReadOnlyField(source='get_status_display')
    
    class Meta:
        model = SubTask
        fields = [
            'id', 'title', 'description', 'task', 'task_title',
            'status', 'status_display', 'assignee', 'assignee_username',
            'due_date', 'completed_date', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

# ========================================
# 13. Checklist Serializer
# ========================================

class ChecklistItemSerializer(serializers.ModelSerializer):
    checked_by_username = serializers.ReadOnlyField(source='checked_by.username')
    
    class Meta:
        model = ChecklistItem
        fields = [
            'id', 'content', 'is_checked', 'checked_by', 'checked_by_username',
            'checked_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'checked_at', 'created_at', 'updated_at']

class ChecklistSerializer(serializers.ModelSerializer):
    task_title = serializers.ReadOnlyField(source='task.title')
    items = ChecklistItemSerializer(many=True, read_only=True)
    items_count = serializers.SerializerMethodField()
    completed_items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Checklist
        fields = [
            'id', 'title', 'task', 'task_title', 'items',
            'items_count', 'completed_items_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_items_count(self, obj):
        return obj.items.count()
    
    def get_completed_items_count(self, obj):
        return obj.items.filter(is_checked=True).count()

class ChecklistCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Checklist
        fields = ['title', 'task']

# ========================================
# . Ticket Serializer
# ========================================

class TicketListSerializer(serializers.ModelSerializer):
    """Ticket summary info"""
    project_name = serializers.ReadOnlyField(source='project.name')
    task_title = serializers.ReadOnlyField(source='task.title')
    assignee_username = serializers.ReadOnlyField(source='assignee.username')
    reporter_username = serializers.ReadOnlyField(source='reporter.username')
    status_display = serializers.ReadOnlyField(source='get_status_display')
    priority_display = serializers.ReadOnlyField(source='get_priority_display')
    ticket_type_display = serializers.ReadOnlyField(source='get_ticket_type_display')
    
    class Meta:
        model = Ticket
        fields = [
            'id', 'title', 'project', 'project_name', 'task', 'task_title',
            'ticket_type', 'ticket_type_display', 'status', 'status_display',
            'priority', 'priority_display', 'assignee', 'assignee_username',
            'reporter', 'reporter_username', 'due_date', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class TicketDetailSerializer(serializers.ModelSerializer):
    """Ticket detail info"""
    project_name = serializers.ReadOnlyField(source='project.name')
    task_title = serializers.ReadOnlyField(source='task.title')
    assignee_username = serializers.ReadOnlyField(source='assignee.username')
    reporter_username = serializers.ReadOnlyField(source='reporter.username')
    resolver_username = serializers.ReadOnlyField(source='resolver.username')
    status_display = serializers.ReadOnlyField(source='get_status_display')
    priority_display = serializers.ReadOnlyField(source='get_priority_display')
    ticket_type_display = serializers.ReadOnlyField(source='get_ticket_type_display')
    
    class Meta:
        model = Ticket
        fields = [
            'id', 'title', 'description', 'project', 'project_name',
            'task', 'task_title', 'ticket_type', 'ticket_type_display',
            'status', 'status_display', 'priority', 'priority_display',
            'reporter', 'reporter_username', 'assignee', 'assignee_username',
            'resolver', 'resolver_username',
            'due_date', 'resolved_date', 'closed_date',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class TicketCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = [
            'title', 'description', 'project', 'task', 'ticket_type',
            'status', 'priority', 'assignee', 'reporter', 'resolver',
            'due_date', 'resolved_date', 'closed_date'
        ]

# ========================================
# 15. Attachment Serializer
# ========================================

class AttachmentSerializer(serializers.ModelSerializer):
    uploaded_by_username = serializers.ReadOnlyField(source='uploaded_by.username')
    file_url = serializers.SerializerMethodField()
    file_size_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Attachment
        fields = [
            'id', 'file', 'file_url', 'filename', 'file_size', 'file_size_display',
            'file_type', 'description', 'content_type', 'object_id',
            'uploaded_by', 'uploaded_by_username', 'uploaded_at', 'updated_at'
        ]
        read_only_fields = ['id', 'file_size', 'uploaded_at', 'updated_at']
    
    def get_file_url(self, obj):
        """Returns file URL"""
        if obj.file:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.file.url) if request else obj.file.url
        return None
    
    def get_file_size_display(self, obj):
        """Formats file size for human readability"""
        if obj.file_size < 1024:
            return f"{obj.file_size} B"
        elif obj.file_size < 1024 * 1024:
            return f"{obj.file_size / 1024:.2f} KB"
        elif obj.file_size < 1024 * 1024 * 1024:
            return f"{obj.file_size / (1024 * 1024):.2f} MB"
        else:
            return f"{obj.file_size / (1024 * 1024 * 1024):.2f} GB"

class AttachmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = [
            'file', 'filename', 'file_type', 'description',
            'content_type', 'object_id'
        ]
    
    def create(self, validated_data):
        """Creates attachment and sets user"""
        validated_data['uploaded_by'] = self.context['request'].user
        return super().create(validated_data)

# ========================================
# 16. Dashboardand Report Serializer
# ========================================

class DashboardStatsSerializer(serializers.Serializer):
    """To display dashboard statistics"""
    total_organizations = serializers.IntegerField()
    total_projects = serializers.IntegerField()
    total_tasks = serializers.IntegerField()
    total_tickets = serializers.IntegerField()
    total_users = serializers.IntegerField()
    completed_tasks = serializers.IntegerField()
    active_projects = serializers.IntegerField()
    overdue_tasks = serializers.IntegerField()
    
    organization_stats = serializers.JSONField(required=False)
    task_status_stats = serializers.JSONField(required=False)
    project_status_stats = serializers.JSONField(required=False)

class OrganizationStatsSerializer(serializers.Serializer):
    """Organization based statistics"""
    organization_id = serializers.IntegerField()
    organization_name = serializers.CharField()
    total_projects = serializers.IntegerField()
    total_tasks = serializers.IntegerField()
    total_members = serializers.IntegerField()

# ========================================
# 17. Login and Token Serializer
# ========================================

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})

class TokenResponseSerializer(serializers.Serializer):
    token = serializers.CharField()
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField()
    role = serializers.CharField(allow_null=True)
    permissions = serializers.ListField(child=serializers.CharField())

# ========================================
# 18. Activity Log Serializer
# ========================================

class ActivityLogSerializer(serializers.Serializer):
    """ ( )"""
    id = serializers.IntegerField()
    user = serializers.CharField()
    action = serializers.CharField()
    model_name = serializers.CharField()
    object_id = serializers.IntegerField()
    object_repr = serializers.CharField()
    changes = serializers.JSONField()
    timestamp = serializers.DateTimeField()