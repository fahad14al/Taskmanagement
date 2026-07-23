# communication/models.py
from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.db.models import Q
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
import uuid


# ========================================
# 1. ChatRoom Model
# ========================================

class ChatRoom(models.Model):
    """
    Chat room for user communication
    """
    ROOM_TYPES = [
        ('direct', 'Direct Message'), # - 
        ('group', 'Group Chat'), # 
        ('project', 'Project Chat'), # - 
        ('team', 'Team Chat'), # - 
        ('channel', 'Channel'), # 
    ]
    
    # 
    room_type = models.CharField(
        max_length=20, 
        choices=ROOM_TYPES, 
        default='direct',
        verbose_name="Room Type"
    )
    name = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        verbose_name="Room Name"
    )
    description = models.TextField(
        blank=True, 
        null=True,
        verbose_name="Description"
    )
    
    # Unique ID for URL usage
    room_id = models.CharField(
        max_length=50, 
        unique=True, 
        db_index=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="Room ID"
    )
    
    # Relationships
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_chat_rooms',
        verbose_name="Created By"
    )
    
    # Generic Foreign Key - (Project, Team, )
    content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE,
        null=True, 
        blank=True,
        related_name='chat_rooms',
        verbose_name="Content Type"
    )
    object_id = models.PositiveIntegerField(
        null=True, 
        blank=True,
        verbose_name="Object ID"
    )
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Members
    members = models.ManyToManyField(
        User, 
        through='ChatRoomMember',
        through_fields=('chat_room', 'user'),
        related_name='chat_rooms',
        verbose_name="Members"
    )
    
    # Admins who can manage room
    admins = models.ManyToManyField(
        User, 
        related_name='admin_chat_rooms',
        blank=True,
        verbose_name="Admins"
    )
    
    # Settings
    is_private = models.BooleanField(
        default=False,
        verbose_name="Is Private"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Is Active"
    )
    is_archived = models.BooleanField(
        default=False,
        verbose_name="Is Archived"
    )
    
    # Avatar icon
    avatar = models.ImageField(
        upload_to='chat/avatars/%Y/%m/',
        blank=True, 
        null=True,
        verbose_name="Avatar"
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
    last_message_at = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name="Last Message At"
    )
    
    class Meta:
        ordering = ['-last_message_at', '-created_at']
        indexes = [
            models.Index(fields=['room_type', 'is_active']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['last_message_at']),
            models.Index(fields=['room_id']),
        ]
        verbose_name = "Chat Room"
        verbose_name_plural = "Chat Rooms"

    def __str__(self):
        if self.name:
            return self.name
        if self.room_type == 'direct':
            members = self.members.all()[:2]
            return f"Chat between {', '.join([m.username for m in members])}"
        return f"{self.get_room_type_display()} Room {self.id}"

    def get_other_member(self, user):
        """Returns other member in direct chat"""
        if self.room_type != 'direct':
            return None
        return self.members.exclude(id=user.id).first()

    def get_member_count(self):
        """Members """
        return self.members.count()

    def get_unread_count(self, user):
        """Unread message count for a user"""
        return MessageRead.objects.filter(
            message__chat_room=self,
            user=user,
            is_read=False
        ).count()

    def get_last_message(self):
        """Returns last message"""
        return self.messages.order_by('-created_at').first()


# ========================================
# 2. ChatRoomMember Model
# ========================================

class ChatRoomMember(models.Model):
    """
      Members - 
    """
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('moderator', 'Moderator'),
        ('member', 'Member'),
    ]
    
    chat_room = models.ForeignKey(
        ChatRoom, 
        on_delete=models.CASCADE,
        related_name='room_members',
        verbose_name="Chat Room"
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='chat_memberships',
        verbose_name="User"
    )
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default='member',
        verbose_name="Role"
    )
    
    # Settings
    is_muted = models.BooleanField(
        default=False,
        verbose_name="Is Muted"
    )
    muted_until = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name="Muted Until"
    )
    
    # Last seen
    last_read_at = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name="Last Read At"
    )
    last_read_message = models.ForeignKey(
        'Message', 
        on_delete=models.SET_NULL,
        null=True, 
        blank=True,
        related_name='read_by_members',
        verbose_name="Last Read Message"
    )
    
    # Join info
    joined_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Joined At"
    )
    invited_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL,
        null=True, 
        blank=True,
        related_name='invited_members',
        verbose_name="Invited By"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Is Active"
    )
    
    class Meta:
        unique_together = ['chat_room', 'user']
        ordering = ['joined_at']
        verbose_name = "Chat Room Member"
        verbose_name_plural = "Chat Room Members"

    def __str__(self):
        return f"{self.user.username} in {self.chat_room}"


# ========================================
# 3. Message Model
# ========================================

class Message(models.Model):
    """
    Messages sent in chat room
    """
    MESSAGE_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('file', 'File'),
        ('audio', 'Audio'),
        ('video', 'Video'),
        ('system', 'System Message'),
        ('notification', 'Notification'),
    ]
    
    # 
    message_id = models.CharField(
        max_length=50, 
        unique=True, 
        db_index=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="Message ID"
    )
    
    # Relationships
    chat_room = models.ForeignKey(
        ChatRoom, 
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name="Chat Room"
    )
    sender = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='sent_messages',
        verbose_name="Sender"
    )
    
    # Parent message for replies or threads
    parent_message = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE,
        null=True, 
        blank=True,
        related_name='replies',
        verbose_name="Parent Message"
    )
    
    # Message content
    message_type = models.CharField(
        max_length=20, 
        choices=MESSAGE_TYPES, 
        default='text',
        verbose_name="Message Type"
    )
    content = models.TextField(
        verbose_name="Content"
    )
    
    # Attachments in JSON format
    attachments = models.JSONField(
        default=list, 
        blank=True,
        verbose_name="Attachments"
    )
    
    # Metadata in JSON
    metadata = models.JSONField(
        default=dict, 
        blank=True,
        verbose_name="Metadata"
    )
    
    # 
    is_edited = models.BooleanField(
        default=False,
        verbose_name="Is Edited"
    )
    is_deleted = models.BooleanField(
        default=False,
        verbose_name="Is Deleted"
    )
    is_pinned = models.BooleanField(
        default=False,
        verbose_name="Is Pinned"
    )
    is_system = models.BooleanField(
        default=False,
        verbose_name="Is System Message"
    )
    
    # Delivery status
    delivered_to = models.ManyToManyField(
        User, 
        related_name='delivered_messages',
        blank=True,
        verbose_name="Delivered To"
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
    deleted_at = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name="Deleted At"
    )
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['chat_room', 'created_at']),
            models.Index(fields=['sender', 'created_at']),
            models.Index(fields=['message_id']),
            models.Index(fields=['is_deleted']),
            models.Index(fields=['parent_message']),
        ]
        verbose_name = "Message"
        verbose_name_plural = "Messages"

    def __str__(self):
        return f"{self.sender.username}: {self.content[:50]}..."

    def get_read_count(self):
        """Returns read count"""
        return self.message_read.filter(is_read=True).count()

    def get_unread_count(self):
        """Returns read count"""
        return self.message_read.filter(is_read=False).count()

    def is_read_by_user(self, user):
        """Whether specific user read message"""
        return self.message_read.filter(user=user, is_read=True).exists()

    def soft_delete(self):
        """Soft deletes message"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()


# ========================================
# 4. MessageRead Model
# ========================================

class MessageRead(models.Model):
    """
    Message read status tracking
    """
    message = models.ForeignKey(
        Message, 
        on_delete=models.CASCADE,
        related_name='message_read',
        verbose_name="Message"
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='read_messages',
        verbose_name="User"
    )
    is_read = models.BooleanField(
        default=False,
        verbose_name="Is Read"
    )
    read_at = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name="Read At"
    )
    delivered_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Delivered At"
    )
    
    class Meta:
        unique_together = ['message', 'user']
        ordering = ['-read_at']
        indexes = [
            models.Index(fields=['message', 'user']),
            models.Index(fields=['is_read']),
        ]
        verbose_name = "Message Read"
        verbose_name_plural = "Message Reads"

    def __str__(self):
        status = "Read" if self.is_read else "Unread"
        return f"{self.user.username} - {status}: {self.message}"

    def mark_as_read(self):
        """Marks message as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()
            return True
        return False


# ========================================
# 5. Presence Model
# ========================================

class Presence(models.Model):
    """
    User online presence status
    """
    STATUS_CHOICES = [
        ('online', 'Online'),
        ('away', 'Away'),
        ('busy', 'Busy'),
        ('offline', 'Offline'),
        ('dnd', 'Do Not Disturb'),
    ]
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        related_name='presence',
        verbose_name="User"
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='offline',
        verbose_name="Status"
    )
    custom_status = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        verbose_name="Custom Status"
    )
    
    # Last activity
    last_activity = models.DateTimeField(
        auto_now=True,
        verbose_name="Last Activity"
    )
    last_seen = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name="Last Seen"
    )
    
    # Device info JSON
    devices = models.JSONField(
        default=list, 
        blank=True,
        verbose_name="Devices"
    )
    
    # Session info
    session_id = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        verbose_name="Session ID"
    )
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
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated At"
    )
    
    class Meta:
        ordering = ['-last_activity']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['last_activity']),
            models.Index(fields=['user', 'status']),
        ]
        verbose_name = "Presence"
        verbose_name_plural = "Presences"

    def __str__(self):
        return f"{self.user.username} - {self.get_status_display()}"

    def is_online(self):
        """Whether user is online"""
        return self.status in ['online', 'away', 'busy', 'dnd']

    def update_status(self, status, custom_status=None):
        """Updates status"""
        self.status = status
        if custom_status is not None:
            self.custom_status = custom_status
        self.last_activity = timezone.now()
        if status == 'offline':
            self.last_seen = timezone.now()
        self.save()

    def update_activity(self):
        """Last activity """
        self.last_activity = timezone.now()
        self.save()


# ========================================
# 6. Signal - Automatic Presence Creation
# ========================================

@receiver(post_save, sender=User)
def create_user_presence(sender, instance, created, **kwargs):
    """Creates Presence when new User created"""
    if created:
        Presence.objects.create(user=instance)


# ========================================
# 7. Signal - Message Read Tracking
# ========================================

@receiver(post_save, sender=Message)
def create_message_read_records(sender, instance, created, **kwargs):
    """ Members MessageRead """
    if created:
        # Members
        members = instance.chat_room.members.exclude(id=instance.sender.id)
        message_reads = [
            MessageRead(message=instance, user=member)
            for member in members
        ]
        MessageRead.objects.bulk_create(message_reads)
        
        # Create read for sender who read own message
        MessageRead.objects.create(
            message=instance,
            user=instance.sender,
            is_read=True,
            read_at=timezone.now()
        )
        
        # Update chat room last_message_at
        chat_room = instance.chat_room
        chat_room.last_message_at = instance.created_at
        chat_room.save(update_fields=['last_message_at'])


# ========================================
# 8. Helper Methods
# ========================================

def get_or_create_direct_chat(user1, user2):
    """
    Creates or returns direct chat between two users
    """
    if user1 == user2:
        raise ValueError("Cannot create chat with self")
    
    # Find direct chat
    chat_room = ChatRoom.objects.filter(
        room_type='direct',
        members=user1
    ).filter(members=user2).first()
    
    if chat_room:
        return chat_room
    
    # Create new direct chat
    chat_room = ChatRoom.objects.create(
        room_type='direct',
        created_by=user1
    )
    
    # ChatRoomMember 
    ChatRoomMember.objects.bulk_create([
        ChatRoomMember(chat_room=chat_room, user=user1, role='admin'),
        ChatRoomMember(chat_room=chat_room, user=user2, role='member'),
    ])
    
    return chat_room


def get_group_chat(name, created_by, members=None):
    """
    Creates group chat
    """
    chat_room = ChatRoom.objects.create(
        room_type='group',
        name=name,
        created_by=created_by
    )
    
    # Add creator as admin
    ChatRoomMember.objects.create(
        chat_room=chat_room,
        user=created_by,
        role='admin'
    )
    chat_room.admins.add(created_by)
    
    # Members 
    if members:
        for user in members:
            if user != created_by:
                ChatRoomMember.objects.create(
                    chat_room=chat_room,
                    user=user,
                    role='member'
                )
    
    return chat_room