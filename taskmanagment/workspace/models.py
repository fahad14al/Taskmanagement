
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.contenttypes.fields import GenericForeignKey

# ========================================
# 1. Organization
# ========================================

class Organization(models.Model):
    """Company or Organization"""
    name = models.CharField(max_length=255, verbose_name="Organization Name")
    slug = models.SlugField(unique=True, max_length=255, verbose_name="Slug")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    logo = models.ImageField(upload_to='organizations/logos/', blank=True, null=True, verbose_name="Logo")
    website = models.URLField(blank=True, null=True, verbose_name="Website")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Phone")
    address = models.TextField(blank=True, null=True, verbose_name="Address")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_organizations', verbose_name="Created By")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Organization"
        verbose_name_plural = "Organizations"

    def __str__(self):
        return self.name


# ========================================
# 2. Department
# ========================================

class Department(models.Model):
    """Department under Organization"""
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='departments', verbose_name="Organization")
    name = models.CharField(max_length=255, verbose_name="Department Name")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    head = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='headed_departments', verbose_name="Department Head")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_departments', verbose_name="Created By")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")

    class Meta:
        ordering = ['name']
        unique_together = ['organization', 'name']  # Ensure unique department name per organization
        verbose_name = "Department"
        verbose_name_plural = "Departments"

    def __str__(self):
        return f"{self.name} ({self.organization.name})"


# ========================================
# 3. Team
# ========================================

class Team(models.Model):
    """Team under Department"""
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='teams', verbose_name="Department")
    name = models.CharField(max_length=255, verbose_name="Team Name")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    lead = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='led_teams', verbose_name="Team Lead")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_teams', verbose_name="Created By")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")

    class Meta:
        ordering = ['name']
        unique_together = ['department', 'name']  # Ensure unique team name per department
        verbose_name = "Team"
        verbose_name_plural = "Teams"

    def __str__(self):
        return f"{self.name} ({self.department.name})"


# ========================================
# 4. Team Member
# ========================================

class TeamMember(models.Model):
    """Team Member"""
    ROLE_CHOICES = [
        ('lead', 'Team Lead'),
        ('member', 'Member'),
        ('observer', 'Observer'),
    ]
    
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='members', verbose_name="Team")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='team_memberships', verbose_name="Members")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member', verbose_name="Role")
    joined_at = models.DateTimeField(auto_now_add=True, verbose_name="Joined At")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")

    class Meta:
        unique_together = ['team', 'user']  # Ensure unique user per team
        verbose_name = "Team Member"
        verbose_name_plural = "Team Members"

    def __str__(self):
        return f"{self.user.username} - {self.team.name}"


# ========================================
# 5. Project
# ========================================

class Project(models.Model):
    """"""
    STATUS_CHOICES = [
        ('planning', 'Planning'),
        ('active', 'Active'),
        ('on_hold', 'On Hold'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    name = models.CharField(max_length=255, verbose_name="Project Name")
    slug = models.SlugField(unique=True, max_length=255, verbose_name="Slug")
    description = models.TextField(verbose_name="Description")
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='projects', verbose_name="Organization")
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='projects', verbose_name="Department")
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='projects', verbose_name="Team")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planning', verbose_name="Status")
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium', verbose_name="Priority")
    
    start_date = models.DateField(verbose_name="Start Date")
    end_date = models.DateField(verbose_name="End Date")
    actual_end_date = models.DateField(null=True, blank=True, verbose_name="Actual End Date")
    
    progress = models.IntegerField(default=0, verbose_name="Progress Percentage")
    
    project_manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='managed_projects', verbose_name="Project Manager")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_projects', verbose_name="Created By")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Project"
        verbose_name_plural = "Projects"

    def __str__(self):
        return self.name


# ========================================
# 6. Project Member
# ========================================

class ProjectMember(models.Model):
    """Project Member"""
    ROLE_CHOICES = [
        ('project_manager', 'Project Manager'),
        ('developer', 'Developer'),
        ('tester', 'Tester'),
        ('designer', 'Designer'),
        ('devops', 'DevOps'),
        ('stakeholder', 'Stakeholder'),
        ('observer', 'Observer'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='members', verbose_name="Project")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='project_memberships', verbose_name="Members")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='developer', verbose_name="Role")
    joined_at = models.DateTimeField(auto_now_add=True, verbose_name="Joined At")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")

    class Meta:
        unique_together = ['project', 'user']  # Ensure unique user per project
        verbose_name = "Project Member"
        verbose_name_plural = "Project Members"

    def __str__(self):
        return f"{self.user.username} - {self.project.name}"


# ========================================
# 7. Sprint
# ========================================

class Sprint(models.Model):
    """Agile Sprint for Project"""
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='sprints', verbose_name="Project")
    name = models.CharField(max_length=255, verbose_name="Sprint Name")
    goal = models.TextField(verbose_name="Sprint Goal")
    
    start_date = models.DateField(verbose_name="Start Date")
    end_date = models.DateField(verbose_name="End Date")
    actual_end_date = models.DateField(null=True, blank=True, verbose_name="Actual End Date")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned', verbose_name="Status")
    total_story_points = models.IntegerField(default=0, verbose_name="Total Story Points")
    completed_story_points = models.IntegerField(default=0, verbose_name="Completed Story Points")
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_sprints', verbose_name="Created By")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        ordering = ['-start_date']
        unique_together = ['project', 'name']  # Ensure unique sprint name per project
        verbose_name = "Sprint"
        verbose_name_plural = "Sprints"

    def __str__(self):
        return f"{self.name} ({self.project.name})"


# ========================================
# 8. Task
# ========================================

class Task(models.Model):
    """Task for Project or Sprint"""
    TASK_TYPE_CHOICES = [
        ('feature', 'Feature'),
        ('bug', 'Bug Fix'),
        ('improvement', 'Improvement'),
        ('technical_debt', 'Technical Debt'),
        ('research', 'Research'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('backlog', 'Backlog'),
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('review', 'In Review'),
        ('testing', 'In Testing'),
        ('completed', 'Completed'),
        ('blocked', 'Blocked'),
        ('cancelled', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    # Relationships
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks', verbose_name="Project")
    sprint = models.ForeignKey(Sprint, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks', verbose_name="Sprint")
    parent_task = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subtasks', verbose_name="Parent Task")
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks', verbose_name="Assignee")
    reporter = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='reported_tasks', verbose_name="Reporter")
    
    # 
    title = models.CharField(max_length=500, verbose_name="Title")
    description = models.TextField(verbose_name="Description")
    task_type = models.CharField(max_length=20, choices=TASK_TYPE_CHOICES, default='feature', verbose_name="Task Type")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='backlog', verbose_name="Status")
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium', verbose_name="Priority")
    
    # 
    story_points = models.IntegerField(default=0, verbose_name="Story Points")
    time_estimated = models.DurationField(null=True, blank=True, verbose_name="Estimated Time")
    time_spent = models.DurationField(null=True, blank=True, verbose_name="Spent Time")
    
    # 
    due_date = models.DateField(verbose_name="Due Date")
    start_date = models.DateField(null=True, blank=True, verbose_name="Start Date")
    completed_date = models.DateField(null=True, blank=True, verbose_name="Completed Date")
    
    # 
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_tasks', verbose_name="Created By")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Task"
        verbose_name_plural = "Tasks"

    def __str__(self):
        return self.title


# ========================================
# 9. SubTask
# ========================================

class SubTask(models.Model):
    """Subtask for Task"""
    STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('blocked', 'Blocked'),
    ]
    
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='subtask_items', verbose_name="Parent Task")
    title = models.CharField(max_length=500, verbose_name="Title")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo', verbose_name="Status")
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_subtasks', verbose_name="Assignee")
    
    due_date = models.DateField(verbose_name="Due Date")
    completed_date = models.DateField(null=True, blank=True, verbose_name="Completed Date")
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_subtasks', verbose_name="Created By")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        ordering = ['created_at']
        verbose_name = "SubTask"
        verbose_name_plural = "SubTasks"

    def __str__(self):
        return f"{self.title} (Subtask of {self.task.title})"


# ========================================
# 10. Checklist
# ========================================

class Checklist(models.Model):
    """Checklist for Task"""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='checklists', verbose_name="Task")
    title = models.CharField(max_length=500, verbose_name="Checklist Name")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_checklists', verbose_name="Created By")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        ordering = ['created_at']
        verbose_name = "Checklist"
        verbose_name_plural = "Checklists"

    def __str__(self):
        return f"{self.title} ({self.task.title})"


# ========================================
# 11. Checklist Item
# ========================================

class ChecklistItem(models.Model):
    """Checklist Item"""
    checklist = models.ForeignKey(Checklist, on_delete=models.CASCADE, related_name='items', verbose_name="Checklist")
    content = models.TextField(verbose_name="Item Description")
    is_checked = models.BooleanField(default=False, verbose_name="Is Checked")
    checked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='checked_items', verbose_name="Checked By")
    checked_at = models.DateTimeField(null=True, blank=True, verbose_name="Checked At")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        ordering = ['created_at']
        verbose_name = "Checklist Item"
        verbose_name_plural = "Checklist Items"

    def __str__(self):
        return f"{self.content[:50]}..."


# ========================================
# 12. Ticket
# ========================================

class Ticket(models.Model):
    """Support Ticket and Issue Tracking"""
    TICKET_TYPE_CHOICES = [
        ('bug', 'Bug Report'),
        ('support', 'Support Request'),
        ('feature', 'Feature Request'),
        ('question', 'Question'),
        ('feedback', 'Feedback'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('pending', 'Pending'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    # Relationships
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tickets', verbose_name="Project")
    task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets', verbose_name="Relationships ")
    
    # 
    title = models.CharField(max_length=500, verbose_name="Title")
    description = models.TextField(verbose_name="Description")
    ticket_type = models.CharField(max_length=20, choices=TICKET_TYPE_CHOICES, default='bug', verbose_name="Ticket Type")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open', verbose_name="Status")
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium', verbose_name="Priority")
    
    # 
    reporter = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='reported_tickets', verbose_name="Reporter")
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets', verbose_name="Assignee")
    resolver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_tickets', verbose_name="Resolver")
    
    # 
    due_date = models.DateField(verbose_name="Due Date")
    resolved_date = models.DateTimeField(null=True, blank=True, verbose_name="Resolved Date")
    closed_date = models.DateTimeField(null=True, blank=True, verbose_name="Closed Date")
    
    # 
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_tickets', verbose_name="Created By")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Ticket"
        verbose_name_plural = "Tickets"

    def __str__(self):
        return f"[{self.get_ticket_type_display()}] {self.title}"


# ========================================
# 13. Attachment
# ========================================

class Attachment(models.Model):
    """File Attachment for models"""
    # Generic Foreign Key ( )
    content_type = models.ForeignKey('contenttypes.ContentType', on_delete=models.CASCADE, related_name='attachments')
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # GenericForeignKey- 
    # : https://docs.djangoproject.com/en/stable/ref/contrib/contenttypes/
    
    # 
    file = models.FileField(upload_to='attachments/%Y/%m/%d/', verbose_name="File")
    filename = models.CharField(max_length=255, verbose_name="File Name")
    file_size = models.BigIntegerField(default=0, verbose_name="File Size Bytes")
    file_type = models.CharField(max_length=100, blank=True, null=True, verbose_name="File Type")
    
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='uploaded_attachments', verbose_name="Uploaded By")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Uploaded At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = "Attachment"
        verbose_name_plural = "Attachments"

    def __str__(self):
        return self.filename
    
    def save(self, *args, **kwargs):
        """Automatically set file size"""
        if self.file:
            self.file_size = self.file.size
            if not self.filename:
                self.filename = self.file.name
        super().save(*args, **kwargs)