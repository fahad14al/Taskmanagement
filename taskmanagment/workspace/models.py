
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.contenttypes.fields import GenericForeignKey

# ========================================
# ১. অর্গানাইজেশন (Organization)
# ========================================

class Organization(models.Model):
    """কোম্পানি বা প্রতিষ্ঠান"""
    name = models.CharField(max_length=255, verbose_name="প্রতিষ্ঠানের নাম")
    slug = models.SlugField(unique=True, max_length=255, verbose_name="স্লাগ")
    description = models.TextField(blank=True, null=True, verbose_name="বিবরণ")
    logo = models.ImageField(upload_to='organizations/logos/', blank=True, null=True, verbose_name="লোগো")
    website = models.URLField(blank=True, null=True, verbose_name="ওয়েবসাইট")
    email = models.EmailField(blank=True, null=True, verbose_name="ইমেইল")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="ফোন")
    address = models.TextField(blank=True, null=True, verbose_name="ঠিকানা")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_organizations', verbose_name="তৈরি করেছেন")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="তৈরির তারিখ")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="আপডেটের তারিখ")
    is_active = models.BooleanField(default=True, verbose_name="সক্রিয়")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Organization"
        verbose_name_plural = "Organizations"

    def __str__(self):
        return self.name


# ========================================
# ২. ডিপার্টমেন্ট (Department)
# ========================================

class Department(models.Model):
    """অর্গানাইজেশনের অধীনে ডিপার্টমেন্ট"""
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='departments', verbose_name="প্রতিষ্ঠান")
    name = models.CharField(max_length=255, verbose_name="ডিপার্টমেন্টের নাম")
    description = models.TextField(blank=True, null=True, verbose_name="বিবরণ")
    head = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='headed_departments', verbose_name="ডিপার্টমেন্ট প্রধান")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_departments', verbose_name="তৈরি করেছেন")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="তৈরির তারিখ")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="আপডেটের তারিখ")
    is_active = models.BooleanField(default=True, verbose_name="সক্রিয়")

    class Meta:
        ordering = ['name']
        unique_together = ['organization', 'name']  # একই অর্গানাইজেশনে ডুপ্লিকেট ডিপার্টমেন্ট নাম না হয়
        verbose_name = "Department"
        verbose_name_plural = "Departments"

    def __str__(self):
        return f"{self.name} ({self.organization.name})"


# ========================================
# ৩. টিম (Team)
# ========================================

class Team(models.Model):
    """ডিপার্টমেন্টের অধীনে টিম"""
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='teams', verbose_name="ডিপার্টমেন্ট")
    name = models.CharField(max_length=255, verbose_name="টিমের নাম")
    description = models.TextField(blank=True, null=True, verbose_name="বিবরণ")
    lead = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='led_teams', verbose_name="টিম লিড")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_teams', verbose_name="তৈরি করেছেন")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="তৈরির তারিখ")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="আপডেটের তারিখ")
    is_active = models.BooleanField(default=True, verbose_name="সক্রিয়")

    class Meta:
        ordering = ['name']
        unique_together = ['department', 'name']  # একই ডিপার্টমেন্টে ডুপ্লিকেট টিম নাম না হয়
        verbose_name = "Team"
        verbose_name_plural = "Teams"

    def __str__(self):
        return f"{self.name} ({self.department.name})"


# ========================================
# ৪. টিম মেম্বার (TeamMember)
# ========================================

class TeamMember(models.Model):
    """টিমের সদস্য"""
    ROLE_CHOICES = [
        ('lead', 'Team Lead'),
        ('member', 'Member'),
        ('observer', 'Observer'),
    ]
    
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='members', verbose_name="টিম")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='team_memberships', verbose_name="সদস্য")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member', verbose_name="ভূমিকা")
    joined_at = models.DateTimeField(auto_now_add=True, verbose_name="যোগদানের তারিখ")
    is_active = models.BooleanField(default=True, verbose_name="সক্রিয়")

    class Meta:
        unique_together = ['team', 'user']  # একই টিমে একই ইউজার একবার
        verbose_name = "Team Member"
        verbose_name_plural = "Team Members"

    def __str__(self):
        return f"{self.user.username} - {self.team.name}"


# ========================================
# ৫. প্রজেক্ট (Project)
# ========================================

class Project(models.Model):
    """প্রজেক্ট"""
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
    
    name = models.CharField(max_length=255, verbose_name="প্রজেক্টের নাম")
    slug = models.SlugField(unique=True, max_length=255, verbose_name="স্লাগ")
    description = models.TextField(verbose_name="বিবরণ")
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='projects', verbose_name="প্রতিষ্ঠান")
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='projects', verbose_name="ডিপার্টমেন্ট")
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='projects', verbose_name="টিম")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planning', verbose_name="স্ট্যাটাস")
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium', verbose_name="প্রায়োরিটি")
    
    start_date = models.DateField(verbose_name="শুরুর তারিখ")
    end_date = models.DateField(verbose_name="শেষের তারিখ")
    actual_end_date = models.DateField(null=True, blank=True, verbose_name="প্রকৃত শেষের তারিখ")
    
    progress = models.IntegerField(default=0, verbose_name="অগ্রগতি (%)")
    
    project_manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='managed_projects', verbose_name="প্রজেক্ট ম্যানেজার")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_projects', verbose_name="তৈরি করেছেন")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="তৈরির তারিখ")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="আপডেটের তারিখ")
    is_active = models.BooleanField(default=True, verbose_name="সক্রিয়")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Project"
        verbose_name_plural = "Projects"

    def __str__(self):
        return self.name


# ========================================
# ৬. প্রজেক্ট মেম্বার (ProjectMember)
# ========================================

class ProjectMember(models.Model):
    """প্রজেক্টের সদস্য"""
    ROLE_CHOICES = [
        ('project_manager', 'Project Manager'),
        ('developer', 'Developer'),
        ('tester', 'Tester'),
        ('designer', 'Designer'),
        ('devops', 'DevOps'),
        ('stakeholder', 'Stakeholder'),
        ('observer', 'Observer'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='members', verbose_name="প্রজেক্ট")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='project_memberships', verbose_name="সদস্য")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='developer', verbose_name="ভূমিকা")
    joined_at = models.DateTimeField(auto_now_add=True, verbose_name="যোগদানের তারিখ")
    is_active = models.BooleanField(default=True, verbose_name="সক্রিয়")

    class Meta:
        unique_together = ['project', 'user']  # একই প্রজেক্টে একই ইউজার একবার
        verbose_name = "Project Member"
        verbose_name_plural = "Project Members"

    def __str__(self):
        return f"{self.user.username} - {self.project.name}"


# ========================================
# ৭. স্প্রিন্ট (Sprint)
# ========================================

class Sprint(models.Model):
    """প্রজেক্টের স্প্রিন্ট (Agile Sprint)"""
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='sprints', verbose_name="প্রজেক্ট")
    name = models.CharField(max_length=255, verbose_name="স্প্রিন্টের নাম")
    goal = models.TextField(verbose_name="স্প্রিন্টের লক্ষ্য")
    
    start_date = models.DateField(verbose_name="শুরুর তারিখ")
    end_date = models.DateField(verbose_name="শেষের তারিখ")
    actual_end_date = models.DateField(null=True, blank=True, verbose_name="প্রকৃত শেষের তারিখ")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned', verbose_name="স্ট্যাটাস")
    total_story_points = models.IntegerField(default=0, verbose_name="মোট স্টোরি পয়েন্ট")
    completed_story_points = models.IntegerField(default=0, verbose_name="সম্পন্ন স্টোরি পয়েন্ট")
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_sprints', verbose_name="তৈরি করেছেন")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="তৈরির তারিখ")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="আপডেটের তারিখ")

    class Meta:
        ordering = ['-start_date']
        unique_together = ['project', 'name']  # একই প্রজেক্টে ডুপ্লিকেট স্প্রিন্ট নাম না হয়
        verbose_name = "Sprint"
        verbose_name_plural = "Sprints"

    def __str__(self):
        return f"{self.name} ({self.project.name})"


# ========================================
# ৮. টাস্ক (Task)
# ========================================

class Task(models.Model):
    """প্রজেক্ট বা স্প্রিন্টের টাস্ক"""
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
    
    # সম্পর্ক
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks', verbose_name="প্রজেক্ট")
    sprint = models.ForeignKey(Sprint, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks', verbose_name="স্প্রিন্ট")
    parent_task = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subtasks', verbose_name="প্যারেন্ট টাস্ক")
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks', verbose_name="দায়িত্বপ্রাপ্ত")
    reporter = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='reported_tasks', verbose_name="রিপোর্টার")
    
    # মৌলিক তথ্য
    title = models.CharField(max_length=500, verbose_name="শিরোনাম")
    description = models.TextField(verbose_name="বিবরণ")
    task_type = models.CharField(max_length=20, choices=TASK_TYPE_CHOICES, default='feature', verbose_name="টাস্কের ধরন")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='backlog', verbose_name="স্ট্যাটাস")
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium', verbose_name="প্রায়োরিটি")
    
    # পরিমাপ
    story_points = models.IntegerField(default=0, verbose_name="স্টোরি পয়েন্ট")
    time_estimated = models.DurationField(null=True, blank=True, verbose_name="আনুমানিক সময়")
    time_spent = models.DurationField(null=True, blank=True, verbose_name="ব্যয়িত সময়")
    
    # তারিখ
    due_date = models.DateField(verbose_name="শেষ তারিখ")
    start_date = models.DateField(null=True, blank=True, verbose_name="শুরুর তারিখ")
    completed_date = models.DateField(null=True, blank=True, verbose_name="সম্পন্নের তারিখ")
    
    # মেটাডেটা
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_tasks', verbose_name="তৈরি করেছেন")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="তৈরির তারিখ")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="আপডেটের তারিখ")
    is_active = models.BooleanField(default=True, verbose_name="সক্রিয়")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Task"
        verbose_name_plural = "Tasks"

    def __str__(self):
        return self.title


# ========================================
# ৯. সাবটাস্ক (SubTask)
# ========================================

class SubTask(models.Model):
    """টাস্কের সাবটাস্ক"""
    STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('blocked', 'Blocked'),
    ]
    
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='subtask_items', verbose_name="প্যারেন্ট টাস্ক")
    title = models.CharField(max_length=500, verbose_name="শিরোনাম")
    description = models.TextField(blank=True, null=True, verbose_name="বিবরণ")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo', verbose_name="স্ট্যাটাস")
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_subtasks', verbose_name="দায়িত্বপ্রাপ্ত")
    
    due_date = models.DateField(verbose_name="শেষ তারিখ")
    completed_date = models.DateField(null=True, blank=True, verbose_name="সম্পন্নের তারিখ")
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_subtasks', verbose_name="তৈরি করেছেন")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="তৈরির তারিখ")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="আপডেটের তারিখ")

    class Meta:
        ordering = ['created_at']
        verbose_name = "SubTask"
        verbose_name_plural = "SubTasks"

    def __str__(self):
        return f"{self.title} (Subtask of {self.task.title})"


# ========================================
# ১০. চেকলিস্ট (Checklist)
# ========================================

class Checklist(models.Model):
    """টাস্কের চেকলিস্ট"""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='checklists', verbose_name="টাস্ক")
    title = models.CharField(max_length=500, verbose_name="চেকলিস্টের নাম")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_checklists', verbose_name="তৈরি করেছেন")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="তৈরির তারিখ")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="আপডেটের তারিখ")

    class Meta:
        ordering = ['created_at']
        verbose_name = "Checklist"
        verbose_name_plural = "Checklists"

    def __str__(self):
        return f"{self.title} ({self.task.title})"


# ========================================
# ১১. চেকলিস্ট আইটেম (ChecklistItem)
# ========================================

class ChecklistItem(models.Model):
    """চেকলিস্টের আইটেম"""
    checklist = models.ForeignKey(Checklist, on_delete=models.CASCADE, related_name='items', verbose_name="চেকলিস্ট")
    content = models.TextField(verbose_name="আইটেমের বিবরণ")
    is_checked = models.BooleanField(default=False, verbose_name="চেক করা হয়েছে?")
    checked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='checked_items', verbose_name="চেক করেছেন")
    checked_at = models.DateTimeField(null=True, blank=True, verbose_name="চেকের তারিখ")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="তৈরির তারিখ")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="আপডেটের তারিখ")

    class Meta:
        ordering = ['created_at']
        verbose_name = "Checklist Item"
        verbose_name_plural = "Checklist Items"

    def __str__(self):
        return f"{self.content[:50]}..."


# ========================================
# ১২. টিকেট (Ticket)
# ========================================

class Ticket(models.Model):
    """সাপোর্ট টিকেট / ইস্যু ট্র্যাকিং"""
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
    
    # সম্পর্ক
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tickets', verbose_name="প্রজেক্ট")
    task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets', verbose_name="সম্পর্কিত টাস্ক")
    
    # মৌলিক তথ্য
    title = models.CharField(max_length=500, verbose_name="শিরোনাম")
    description = models.TextField(verbose_name="বিবরণ")
    ticket_type = models.CharField(max_length=20, choices=TICKET_TYPE_CHOICES, default='bug', verbose_name="টিকেটের ধরন")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open', verbose_name="স্ট্যাটাস")
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium', verbose_name="প্রায়োরিটি")
    
    # ব্যক্তি
    reporter = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='reported_tickets', verbose_name="রিপোর্টার")
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets', verbose_name="দায়িত্বপ্রাপ্ত")
    resolver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_tickets', verbose_name="সমাধানকারী")
    
    # তারিখ
    due_date = models.DateField(verbose_name="শেষ তারিখ")
    resolved_date = models.DateTimeField(null=True, blank=True, verbose_name="সমাধানের তারিখ")
    closed_date = models.DateTimeField(null=True, blank=True, verbose_name="বন্ধের তারিখ")
    
    # মেটাডেটা
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_tickets', verbose_name="তৈরি করেছেন")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="তৈরির তারিখ")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="আপডেটের তারিখ")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Ticket"
        verbose_name_plural = "Tickets"

    def __str__(self):
        return f"[{self.get_ticket_type_display()}] {self.title}"


# ========================================
# ১৩. অ্যাটাচমেন্ট (Attachment)
# ========================================

class Attachment(models.Model):
    """ফাইল অ্যাটাচমেন্ট (যেকোনো মডেলের সাথে)"""
    # Generic Foreign Key (যেকোনো মডেলের সাথে সংযুক্ত করা যাবে)
    content_type = models.ForeignKey('contenttypes.ContentType', on_delete=models.CASCADE, related_name='attachments')
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # GenericForeignKey-র জন্য
    # থেকে: https://docs.djangoproject.com/en/stable/ref/contrib/contenttypes/
    
    # মৌলিক তথ্য
    file = models.FileField(upload_to='attachments/%Y/%m/%d/', verbose_name="ফাইল")
    filename = models.CharField(max_length=255, verbose_name="ফাইলের নাম")
    file_size = models.BigIntegerField(default=0, verbose_name="ফাইলের সাইজ (বাইট)")
    file_type = models.CharField(max_length=100, blank=True, null=True, verbose_name="ফাইলের ধরন")
    
    description = models.TextField(blank=True, null=True, verbose_name="বিবরণ")
    
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='uploaded_attachments', verbose_name="আপলোড করেছেন")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="আপলোডের তারিখ")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="আপডেটের তারিখ")

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = "Attachment"
        verbose_name_plural = "Attachments"

    def __str__(self):
        return self.filename
    
    def save(self, *args, **kwargs):
        """ফাইল সাইজ অটোমেটিক সেট করা"""
        if self.file:
            self.file_size = self.file.size
            if not self.filename:
                self.filename = self.file.name
        super().save(*args, **kwargs)