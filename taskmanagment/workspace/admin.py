# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import (
    Organization, Department, Team, TeamMember,
    Project, ProjectMember, Sprint,
    Task, SubTask, Checklist, ChecklistItem,
    Ticket, Attachment, Role, Permission, RolePermission, Profile
)

# ========================================
# ১. Role, Permission, RolePermission Admin
# ========================================

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'get_name_display', 'description', 'created_at']
    list_filter = ['name']
    search_fields = ['name', 'description']
    ordering = ['name']
    readonly_fields = ['created_at']
    
    def get_name_display(self, obj):
        return obj.get_name_display()
    get_name_display.short_description = 'Role Name Display'

@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'get_name_display', 'description']
    list_filter = ['name']
    search_fields = ['name', 'description']
    ordering = ['name']
    readonly_fields = ['id']
    
    def get_name_display(self, obj):
        return obj.get_name_display()
    get_name_display.short_description = 'Permission Display'

@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ['id', 'role', 'permission']
    list_filter = ['role', 'permission']
    search_fields = ['role__name', 'permission__name']
    ordering = ['role', 'permission']

# ========================================
# ২. Profile Admin (User-এর সাথে Inline)
# ========================================

class ProfileInline(admin.StackedInline):
    """User অ্যাডমিন পেজের ভিতরে Profile দেখানোর জন্য Inline"""
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'
    fields = ['role', 'permissions', 'phone', 'address', 'profile_picture']
    filter_horizontal = ['permissions']

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'role', 'phone', 'created_at']
    list_filter = ['role', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone']
    raw_id_fields = ['user']
    filter_horizontal = ['permissions']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

# ========================================
# ৩. Custom User Admin (Profile Inline সহ)
# ========================================

class CustomUserAdmin(UserAdmin):
    """ডিফল্ট UserAdmin-কে কাস্টমাইজ করে Profile Inline যোগ করা"""
    inlines = [ProfileInline]
    list_display = ['id', 'username', 'email', 'first_name', 'last_name', 
                   'is_staff', 'is_active', 'get_role', 'get_organization']
    list_filter = ['is_staff', 'is_active', 'profile__role']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    
    def get_role(self, obj):
        """ইউজারের Role দেখানোর জন্য"""
        if hasattr(obj, 'profile') and obj.profile.role:
            return obj.profile.role.get_name_display()
        return '-'
    get_role.short_description = 'Role'
    
    def get_organization(self, obj):
        """ইউজারের Organization দেখানোর জন্য"""
        # ইউজার যে অর্গানাইজেশনের সাথে যুক্ত তা দেখান
        orgs = Organization.objects.filter(created_by=obj)
        if orgs.exists():
            return ', '.join([org.name for org in orgs[:3]])
        return '-'
    get_organization.short_description = 'Organization'

# ইউজার মডেল রি-রেজিস্টার করুন
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# ========================================
# ৪. Organization Admin
# ========================================

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'slug', 'email', 'phone', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'slug', 'email', 'phone']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'logo')
        }),
        ('Contact Information', {
            'fields': ('website', 'email', 'phone', 'address')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at', 'is_active')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        obj.save()

# ========================================
# ৫. Department Admin
# ========================================

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'organization', 'head', 'is_active', 'created_at']
    list_filter = ['organization', 'is_active', 'created_at']
    search_fields = ['name', 'organization__name']
    ordering = ['organization', 'name']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Department Information', {
            'fields': ('organization', 'name', 'description', 'head')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at', 'is_active')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        obj.save()

# ========================================
# ৬. Team Admin
# ========================================

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'department', 'lead', 'member_count', 'is_active', 'created_at']
    list_filter = ['department', 'is_active', 'created_at']
    search_fields = ['name', 'department__name']
    ordering = ['department', 'name']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Team Information', {
            'fields': ('department', 'name', 'description', 'lead')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at', 'is_active')
        }),
    )
    
    def member_count(self, obj):
        """টিমের সদস্য সংখ্যা দেখানোর জন্য"""
        return obj.members.filter(is_active=True).count()
    member_count.short_description = 'Members Count'
    
    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        obj.save()

# ========================================
# ৭. TeamMember Admin
# ========================================

@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ['id', 'team', 'user', 'role', 'joined_at', 'is_active']
    list_filter = ['team', 'role', 'is_active']
    search_fields = ['team__name', 'user__username', 'user__email']
    ordering = ['-joined_at']
    readonly_fields = ['joined_at']
    fieldsets = (
        ('Membership Information', {
            'fields': ('team', 'user', 'role')
        }),
        ('Metadata', {
            'fields': ('joined_at', 'is_active')
        }),
    )

# ========================================
# ৮. Project Admin
# ========================================

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'slug', 'organization', 'status', 'priority', 
                   'progress', 'project_manager', 'start_date', 'end_date']
    list_filter = ['status', 'priority', 'organization', 'department', 'is_active']
    search_fields = ['name', 'slug', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    fieldsets = (
        ('Project Information', {
            'fields': ('name', 'slug', 'description', 'organization', 'department', 'team')
        }),
        ('Timeline', {
            'fields': ('start_date', 'end_date', 'actual_end_date')
        }),
        ('Status & Priority', {
            'fields': ('status', 'priority', 'progress')
        }),
        ('People', {
            'fields': ('project_manager', 'created_by')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'is_active')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        obj.save()

# ========================================
# ৯. ProjectMember Admin
# ========================================

@admin.register(ProjectMember)
class ProjectMemberAdmin(admin.ModelAdmin):
    list_display = ['id', 'project', 'user', 'role', 'joined_at', 'is_active']
    list_filter = ['project', 'role', 'is_active']
    search_fields = ['project__name', 'user__username', 'user__email']
    ordering = ['-joined_at']
    readonly_fields = ['joined_at']

# ========================================
# ১০. Sprint Admin
# ========================================

@admin.register(Sprint)
class SprintAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'project', 'status', 'start_date', 'end_date', 
                   'total_story_points', 'completed_story_points']
    list_filter = ['status', 'project', 'start_date']
    search_fields = ['name', 'project__name', 'goal']
    ordering = ['-start_date']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Sprint Information', {
            'fields': ('project', 'name', 'goal')
        }),
        ('Timeline', {
            'fields': ('start_date', 'end_date', 'actual_end_date')
        }),
        ('Progress', {
            'fields': ('status', 'total_story_points', 'completed_story_points')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        obj.save()

# ========================================
# ১১. Task Admin
# ========================================

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'project', 'sprint', 'status', 'priority', 
                   'task_type', 'assignee', 'story_points', 'due_date']
    list_filter = ['status', 'priority', 'task_type', 'project', 'sprint', 'is_active']
    search_fields = ['title', 'description', 'project__name']
    list_editable = ['status', 'priority', 'assignee']  # ইনলাইন এডিট
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    raw_id_fields = ['assignee', 'reporter', 'created_by']
    fieldsets = (
        ('Task Information', {
            'fields': ('title', 'description', 'project', 'sprint', 'parent_task')
        }),
        ('Type & Status', {
            'fields': ('task_type', 'status', 'priority')
        }),
        ('Timeline', {
            'fields': ('due_date', 'start_date', 'completed_date')
        }),
        ('Estimation', {
            'fields': ('story_points', 'time_estimated', 'time_spent')
        }),
        ('People', {
            'fields': ('assignee', 'reporter', 'created_by')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'is_active')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        obj.save()

# ========================================
# ১২. SubTask Admin
# ========================================

@admin.register(SubTask)
class SubTaskAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'task', 'status', 'assignee', 'due_date']
    list_filter = ['status', 'task']
    search_fields = ['title', 'task__title']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['assignee', 'created_by']
    ordering = ['-created_at']

# ========================================
# ১৩. Checklist Admin
# ========================================

@admin.register(Checklist)
class ChecklistAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'task', 'item_count', 'created_at']
    search_fields = ['title', 'task__title']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    def item_count(self, obj):
        """চেকলিস্টের আইটেম সংখ্যা দেখানোর জন্য"""
        return obj.items.count()
    item_count.short_description = 'Items Count'

# ========================================
# ১৪. ChecklistItem Admin
# ========================================

@admin.register(ChecklistItem)
class ChecklistItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'content_short', 'checklist', 'is_checked', 'checked_by', 'checked_at']
    list_filter = ['is_checked', 'checklist']
    search_fields = ['content', 'checklist__title']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    def content_short(self, obj):
        """কন্টেন্টের প্রথম ৫০ অক্ষর দেখানোর জন্য"""
        return f"{obj.content[:50]}..." if len(obj.content) > 50 else obj.content
    content_short.short_description = 'Content'

# ========================================
# ১৫. Ticket Admin
# ========================================

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'project', 'ticket_type', 'status', 'priority', 
                   'assignee', 'due_date', 'created_at']
    list_filter = ['status', 'priority', 'ticket_type', 'project']
    search_fields = ['title', 'description', 'project__name']
    list_editable = ['status', 'priority', 'assignee']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    raw_id_fields = ['assignee', 'reporter', 'resolver', 'created_by']
    fieldsets = (
        ('Ticket Information', {
            'fields': ('title', 'description', 'project', 'task')
        }),
        ('Type & Status', {
            'fields': ('ticket_type', 'status', 'priority')
        }),
        ('People', {
            'fields': ('reporter', 'assignee', 'resolver')
        }),
        ('Timeline', {
            'fields': ('due_date', 'resolved_date', 'closed_date')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        obj.save()

# ========================================
# ১৬. Attachment Admin
# ========================================

@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'filename', 'file_size_display', 'content_type', 'object_id', 
                   'uploaded_by', 'uploaded_at']
    list_filter = ['content_type', 'uploaded_at']
    search_fields = ['filename', 'description', 'uploaded_by__username']
    readonly_fields = ['uploaded_at', 'updated_at', 'file_size']
    ordering = ['-uploaded_at']
    raw_id_fields = ['uploaded_by']
    
    def file_size_display(self, obj):
        """ফাইল সাইজ মানব-পাঠযোগ্য ফরম্যাটে দেখানোর জন্য"""
        if obj.file_size < 1024:
            return f"{obj.file_size} B"
        elif obj.file_size < 1024 * 1024:
            return f"{obj.file_size / 1024:.2f} KB"
        elif obj.file_size < 1024 * 1024 * 1024:
            return f"{obj.file_size / (1024 * 1024):.2f} MB"
        else:
            return f"{obj.file_size / (1024 * 1024 * 1024):.2f} GB"
    file_size_display.short_description = 'File Size'
    
    def delete_queryset(self, request, queryset):
        """অ্যাটাচমেন্ট ডিলিট করার সময় ফাইলও ডিলিট করা"""
        for obj in queryset:
            obj.file.delete()
        super().delete_queryset(request, queryset)

# ========================================
# ১৭. অ্যাডমিন সাইট কাস্টমাইজেশন
# ========================================

admin.site.site_header = "Project Management System Admin"
admin.site.site_title = "Project Management Admin"
admin.site.index_title = "Welcome to Project Management Admin Panel"

# ========================================
# ১৮. অ্যাকশন (Bulk Actions) - অপশনাল
# ========================================

@admin.action(description='Mark selected tasks as completed')
def mark_tasks_completed(modeladmin, request, queryset):
    queryset.update(status='completed', completed_date=timezone.now().date())

@admin.action(description='Mark selected projects as active')
def mark_projects_active(modeladmin, request, queryset):
    queryset.update(status='active')

# টাস্ক অ্যাডমিনে অ্যাকশন যোগ করুন
TaskAdmin.actions = [mark_tasks_completed]
ProjectAdmin.actions = [mark_projects_active]