# collaboration/models.py
from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from workspace.models import Project, Task, Ticket, Organization

# ========================================
# 1. Comment Model
# ========================================

class Comment(models.Model):
    """
    User comments linked to model
    (Task, Ticket, Project, )
    """
    # Generic Foreign Key - 
    content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name="Content Type"
    )
    object_id = models.PositiveIntegerField(
        verbose_name="Object ID"
    )
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Comment details
    author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='comments',
        verbose_name="Author"
    )
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='replies',
        verbose_name="Parent Comment"
    )
    content = models.TextField(
        verbose_name="Comment Content"
    )
    
    # Optional attachment
    attachment = models.FileField(
        upload_to='comments/attachments/%Y/%m/%d/',
        blank=True, 
        null=True,
        verbose_name="Attachment"
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="Created At"
    )
    updated_at = models.DateTimeField(
        auto_now=True, 
        verbose_name="Updated At"
    )
    is_edited = models.BooleanField(
        default=False, 
        verbose_name="Is Edited"
    )
    is_deleted = models.BooleanField(
        default=False, 
        verbose_name="Is Deleted"
    )
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = "Comment"
        verbose_name_plural = "Comments"

    def __str__(self):
        return f"Comment by {self.author.username} on {self.created_at}"

    def save(self, *args, **kwargs):
        if self.pk:
            # If updating
            original = Comment.objects.get(pk=self.pk)
            if original.content != self.content:
                self.is_edited = True
        super().save(*args, **kwargs)

    @property
    def reply_count(self):
        """Number of replies"""
        return self.replies.filter(is_deleted=False).count()

    def is_owner(self, user):
        """Check if user is comment owner"""
        return self.author == user


# ========================================
# 2. Mention Model
# ========================================

class Mention(models.Model):
    """
    User mentions linked to model
    (Comment, Task, Ticket, )
    """
    # Generic Foreign Key
    content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE,
        related_name='mentions',
        verbose_name="Content Type"
    )
    object_id = models.PositiveIntegerField(
        verbose_name="Object ID"
    )
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Mention details
    mentioned_user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='mentions_received',
        verbose_name="Mentioned User"
    )
    mentioned_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='mentions_given',
        verbose_name="Mentioned By"
    )
    
    # Mention context
    context = models.TextField(
        blank=True, 
        null=True,
        verbose_name="Context"
    )
    context_url = models.URLField(
        blank=True, 
        null=True,
        verbose_name="Context URL"
    )
    
    # 
    is_read = models.BooleanField(
        default=False, 
        verbose_name="Is Read"
    )
    read_at = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name="Read At"
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="Created At"
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['mentioned_user', 'is_read']),
        ]
        verbose_name = "Mention"
        verbose_name_plural = "Mentions"

    def __str__(self):
        return f"{self.mentioned_by} mentioned {self.mentioned_user}"

    def mark_as_read(self):
        """Mark mention as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()


# ========================================
# 3. Notification Model
# ========================================

class Notification(models.Model):
    """
    Notifications for user events
    """
    NOTIFICATION_TYPES = [
        ('comment', 'New Comment'),
        ('mention', 'Mention'),
        ('task_assigned', 'Task Assigned'),
        ('task_status', 'Task Status Changed'),
        ('ticket_created', 'New Ticket'),
        ('ticket_resolved', 'Ticket Resolved'),
        ('project_created', 'New Project'),
        ('project_completed', 'Project Completed'),
        ('team_added', 'Added to Team'),
        ('role_changed', 'Role Changed'),
        ('deadline_approaching', 'Deadline Approaching'),
        ('system', 'System Notification'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    # Recipient
    recipient = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='notifications',
        verbose_name="Recipient"
    )
    
    # Notification Info
    notification_type = models.CharField(
        max_length=30, 
        choices=NOTIFICATION_TYPES,
        verbose_name="Notification Type"
    )
    title = models.CharField(
        max_length=255, 
        verbose_name="Title"
    )
    message = models.TextField(
        verbose_name="Message"
    )
    priority = models.CharField(
        max_length=20, 
        choices=PRIORITY_CHOICES, 
        default='medium',
        verbose_name="Priority"
    )
    
    # Link/Action URL
    action_url = models.URLField(
        blank=True, 
        null=True,
        verbose_name="Action URL"
    )
    
    # Related Object (Generic Foreign Key)
    content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE,
        null=True, 
        blank=True,
        related_name='notifications',
        verbose_name="Content Type"
    )
    object_id = models.PositiveIntegerField(
        null=True, 
        blank=True,
        verbose_name="Object ID"
    )
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Status
    is_read = models.BooleanField(
        default=False, 
        verbose_name="Is Read"
    )
    read_at = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name="Read At"
    )
    is_sent = models.BooleanField(
        default=False, 
        verbose_name="Is Sent"
    ) # Email/Push 
    sent_at = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name="Sent At"
    )
    
    # Created By (Who triggered this notification)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL,
        null=True, 
        blank=True,
        related_name='notifications_created',
        verbose_name="Created By"
    )
    
    # Timestamp
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="Created At"
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['created_at']),
            models.Index(fields=['recipient', 'created_at']),
        ]
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

    def __str__(self):
        return f"{self.title} - {self.recipient.username}"

    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()

    def mark_as_sent(self):
        """Mark notification as sent"""
        if not self.is_sent:
            self.is_sent = True
            self.sent_at = timezone.now()
            self.save()


# ========================================
# 4. ActivityLog Model
# ========================================

class ActivityLog(models.Model):
    """
    Activity log audit trail
    """
    ACTION_TYPES = [
        ('create', 'Created'),
        ('update', 'Updated'),
        ('delete', 'Deleted'),
        ('view', 'Viewed'),
        ('assign', 'Assigned'),
        ('status_change', 'Status Changed'),
        ('comment', 'Commented'),
        ('mention', 'Mentioned'),
        ('login', 'Logged In'),
        ('logout', 'Logged Out'),
        ('upload', 'Uploaded File'),
        ('download', 'Downloaded File'),
        ('share', 'Shared'),
        ('archive', 'Archived'),
        ('restore', 'Restored'),
    ]
    
    # Actor ( )
    actor = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL,
        null=True, 
        related_name='activities',
        verbose_name="Actor"
    )
    
    # Action Info
    action_type = models.CharField(
        max_length=20, 
        choices=ACTION_TYPES,
        verbose_name="Action Type"
    )
    action_description = models.TextField(
        verbose_name="Action Description"
    )
    
    # Related Object (Generic Foreign Key)
    content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE,
        null=True, 
        blank=True,
        related_name='activity_logs',
        verbose_name="Content Type"
    )
    object_id = models.PositiveIntegerField(
        null=True, 
        blank=True,
        verbose_name="Object ID"
    )
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Object details (JSON)
    object_name = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        verbose_name="Object Name"
    )
    object_repr = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        verbose_name="Object Representation"
    )
    
    # Changes (JSON)
    changes = models.JSONField(
        default=dict, 
        blank=True,
        verbose_name="Changes"
    )
    
    # IP Address & User Agent ( )
    ip_address = models.GenericIPAddressField(
        null=True, 
        blank=True,
        verbose_name="IP Address"
    )
    user_agent = models.TextField(
        blank=True, 
        null=True,
        verbose_name="User Agent"
    )
    
    # Request details
    request_method = models.CharField(
        max_length=10, 
        blank=True, 
        null=True,
        verbose_name="Request Method"
    )
    request_path = models.CharField(
        max_length=500, 
        blank=True, 
        null=True,
        verbose_name="Request Path"
    )
    
    # Organization (for filtering)
    organization = models.ForeignKey(
        Organization, 
        on_delete=models.SET_NULL,
        null=True, 
        blank=True,
        related_name='activity_logs',
        verbose_name="Organization"
    )
    
    # Timestamp
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="Created At"
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['actor', 'created_at']),
            models.Index(fields=['action_type']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = "Activity Log"
        verbose_name_plural = "Activity Logs"

    def __str__(self):
        return f"{self.actor} - {self.action_type} at {self.created_at}"


# ========================================
# 5. Reaction Model
# ========================================

class Reaction(models.Model):
    """
    Reactions like Love Laugh Sad Angry etc
    """
    REACTION_TYPES = [
        ('like', 'Like'),
        ('love', 'Love'),
        ('laugh', 'Laugh'),
        ('sad', 'Sad'),
        ('angry', 'Angry'),
        ('wow', 'Wow'),
        ('applause', 'Applause'),
        ('thumbs_down', 'Dislike'),
        ('rocket', 'Rocket'),
        ('fire', 'Fire'),
    ]
    
    # Generic Foreign Key - (Comment, Task, Ticket, )
    content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE,
        related_name='reactions',
        verbose_name="Content Type"
    )
    object_id = models.PositiveIntegerField(
        verbose_name="Object ID"
    )
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Reaction Info
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='reactions',
        verbose_name="User"
    )
    reaction_type = models.CharField(
        max_length=20, 
        choices=REACTION_TYPES,
        verbose_name="Reaction Type"
    )
    
    # Timestamp
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="Created At"
    )
    updated_at = models.DateTimeField(
        auto_now=True, 
        verbose_name="Updated At"
    )
    
    class Meta:
        # User can react once per object
        unique_together = ['content_type', 'object_id', 'user']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['user']),
        ]
        verbose_name = "Reaction"
        verbose_name_plural = "Reactions"

    def __str__(self):
        return f"{self.user} reacted {self.reaction_type}"


# ========================================
# 6. Signals - Automatic Activity Log
# ========================================

@receiver(post_save, sender=Comment)
def log_comment_activity(sender, instance, created, **kwargs):
    """Activity log on comment creation or update"""
    if created:
        action_type = 'comment'
        description = f"Commented on {instance.content_object}"
    else:
        action_type = 'update'
        description = f"Updated comment on {instance.content_object}"
    
    ActivityLog.objects.create(
        actor=instance.author,
        action_type=action_type,
        action_description=description,
        content_object=instance,
        object_name=instance.content_object._meta.verbose_name,
        object_repr=str(instance.content_object)
    )


@receiver(post_save, sender=Mention)
def log_mention_activity(sender, instance, created, **kwargs):
    """Activity log and notification on mention creation"""
    if created:
        # Activity Log
        ActivityLog.objects.create(
            actor=instance.mentioned_by,
            action_type='mention',
            action_description=f"Mentioned {instance.mentioned_user} in {instance.content_object}",
            content_object=instance.content_object,
            object_name=instance.content_object._meta.verbose_name,
            object_repr=str(instance.content_object)
        )
        
        # Notification
        Notification.objects.create(
            recipient=instance.mentioned_user,
            notification_type='mention',
            title=f"New Mention from {instance.mentioned_by.username}",
            message=f"{instance.mentioned_by.username} mentioned you in a comment/task.",
            created_by=instance.mentioned_by,
            content_object=instance.content_object,
            action_url=instance.context_url
        )


@receiver(post_save, sender=Task)
def log_task_activity(sender, instance, created, **kwargs):
    """Activity log on task creation or update"""
    if created:
        action_type = 'create'
        description = f"Created task: {instance.title}"
    else:
        action_type = 'update'
        description = f"Updated task: {instance.title}"
    
    ActivityLog.objects.create(
        actor=instance.created_by,
        action_type=action_type,
        action_description=description,
        content_object=instance,
        object_name='Task',
        object_repr=instance.title
    )


@receiver(post_save, sender=Ticket)
def log_ticket_activity(sender, instance, created, **kwargs):
    """Activity log on ticket creation or update"""
    if created:
        action_type = 'create'
        description = f"Created ticket: {instance.title}"
    else:
        action_type = 'update'
        description = f"Updated ticket: {instance.title}"
    
    ActivityLog.objects.create(
        actor=instance.created_by,
        action_type=action_type,
        action_description=description,
        content_object=instance,
        object_name='Ticket',
        object_repr=instance.title
    )