# collaboration/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Comment, Mention, Notification, ActivityLog, Reaction


# ========================================
# . Comment Admin
# ========================================

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'author', 'content_preview', 'content_object_display',
        'parent_display', 'reply_count', 'is_edited', 'is_deleted',
        'created_at'
    ]
    list_filter = ['is_edited', 'is_deleted', 'created_at', 'author']
    search_fields = ['content', 'author__username', 'author__email']
    readonly_fields = ['id', 'created_at', 'updated_at']
    raw_id_fields = ['author', 'parent']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Comment Information', {
            'fields': ('author', 'parent', 'content')
        }),
        ('Attachment', {
            'fields': ('attachment',)
        }),
        ('Related Object', {
            'fields': ('content_type', 'object_id')
        }),
        ('Status', {
            'fields': ('is_edited', 'is_deleted')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def content_preview(self, obj):
        """ """
        if len(obj.content) > 50:
            return f"{obj.content[:50]}..."
        return obj.content
    content_preview.short_description = "Content Preview"
    
    def content_object_display(self, obj):
        """ """
        if obj.content_object:
            return format_html(
                '<span style="color: blue;">{} ({})</span>',
                str(obj.content_object),
                obj.content_object._meta.verbose_name
            )
        return "-"
    content_object_display.short_description = "Content Object"
    
    def parent_display(self, obj):
        """ """
        if obj.parent:
            return format_html(
                '<a href="/admin/collaboration/comment/{}/change/">{}</a>',
                obj.parent.id,
                obj.parent.content[:30] + "..."
            )
        return "-"
    parent_display.short_description = "Parent Comment"
    
    def reply_count(self, obj):
        """Number of replies"""
        return obj.reply_count
    reply_count.short_description = "Replies"
    
    actions = ['soft_delete_comments', 'restore_comments']
    
    def soft_delete_comments(self, request, queryset):
        queryset.update(is_deleted=True)
        self.message_user(request, f"{queryset.count()} comments marked as deleted.")
    soft_delete_comments.short_description = "Soft delete selected comments"
    
    def restore_comments(self, request, queryset):
        queryset.update(is_deleted=False)
        self.message_user(request, f"{queryset.count()} comments restored.")
    restore_comments.short_description = "Restore selected comments"


# ========================================
# . Mention Admin
# ========================================

@admin.register(Mention)
class MentionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'mentioned_by', 'mentioned_user', 'content_object_display',
        'is_read', 'read_at_display', 'created_at'
    ]
    list_filter = ['is_read', 'created_at']
    search_fields = ['mentioned_by__username', 'mentioned_user__username']
    readonly_fields = ['id', 'created_at']
    raw_id_fields = ['mentioned_user', 'mentioned_by']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Mention Information', {
            'fields': ('mentioned_user', 'mentioned_by')
        }),
        ('Context', {
            'fields': ('context', 'context_url')
        }),
        ('Related Object', {
            'fields': ('content_type', 'object_id')
        }),
        ('Status', {
            'fields': ('is_read', 'read_at')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def content_object_display(self, obj):
        """ """
        if obj.content_object:
            return format_html(
                '<span style="color: green;">{} ({})</span>',
                str(obj.content_object),
                obj.content_object._meta.verbose_name
            )
        return "-"
    content_object_display.short_description = "Content Object"
    
    def read_at_display(self, obj):
        """ """
        if obj.read_at:
            return obj.read_at.strftime("%Y-%m-%d %H:%M")
        return "-"
    read_at_display.short_description = "Read At"
    
    actions = ['mark_as_read']
    
    def mark_as_read(self, request, queryset):
        for mention in queryset:
            mention.mark_as_read()
        self.message_user(request, f"{queryset.count()} mentions marked as read.")
    mark_as_read.short_description = "Mark selected mentions as read"


# ========================================
# . Notification Admin
# ========================================

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'title_preview', 'recipient', 'notification_type_display',
        'priority_display', 'is_read', 'is_sent', 'created_at'
    ]
    list_filter = ['notification_type', 'priority', 'is_read', 'is_sent', 'created_at']
    search_fields = ['title', 'message', 'recipient__username']
    readonly_fields = ['id', 'created_at']
    raw_id_fields = ['recipient', 'created_by']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Notification Information', {
            'fields': ('recipient', 'notification_type', 'title', 'message')
        }),
        ('Priority & Status', {
            'fields': ('priority', 'is_read', 'read_at', 'is_sent', 'sent_at')
        }),
        ('Action', {
            'fields': ('action_url',)
        }),
        ('Related Object', {
            'fields': ('content_type', 'object_id')
        }),
        ('Created By', {
            'fields': ('created_by',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def title_preview(self, obj):
        """ """
        if len(obj.title) > 40:
            return f"{obj.title[:40]}..."
        return obj.title
    title_preview.short_description = "Title"
    
    def notification_type_display(self, obj):
        """ """
        return format_html(
            '<span style="background-color: #007bff; color: white; padding: 2px 8px; border-radius: 12px;">{}</span>',
            obj.get_notification_type_display()
        )
    notification_type_display.short_description = "Type"
    
    def priority_display(self, obj):
        """ """
        colors = {
            'low': '#28a745',
            'medium': '#ffc107',
            'high': '#fd7e14',
            'critical': '#dc3545'
        }
        color = colors.get(obj.priority, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 12px;">{}</span>',
            color,
            obj.get_priority_display()
        )
    priority_display.short_description = "Priority"
    
    actions = ['mark_as_read', 'mark_as_sent']
    
    def mark_as_read(self, request, queryset):
        for notification in queryset:
            notification.mark_as_read()
        self.message_user(request, f"{queryset.count()} notifications marked as read.")
    mark_as_read.short_description = "Mark selected as read"
    
    def mark_as_sent(self, request, queryset):
        for notification in queryset:
            notification.mark_as_sent()
        self.message_user(request, f"{queryset.count()} notifications marked as sent.")
    mark_as_sent.short_description = "Mark selected as sent"


# ========================================
# . ActivityLog Admin
# ========================================

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'actor_display', 'action_type_display',
        'action_description_short', 'content_object_display',
        'organization_display', 'created_at'
    ]
    list_filter = ['action_type', 'created_at', 'organization']
    search_fields = [
        'action_description', 'actor__username', 
        'object_name', 'object_repr', 'request_path'
    ]
    readonly_fields = ['id', 'created_at']
    raw_id_fields = ['actor', 'organization']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Action Information', {
            'fields': ('actor', 'action_type', 'action_description')
        }),
        ('Related Object', {
            'fields': ('content_type', 'object_id', 'object_name', 'object_repr')
        }),
        ('Changes', {
            'fields': ('changes',),
            'classes': ('collapse',)
        }),
        ('Request Details', {
            'fields': ('ip_address', 'user_agent', 'request_method', 'request_path'),
            'classes': ('collapse',)
        }),
        ('Organization', {
            'fields': ('organization',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def actor_display(self, obj):
        """Actor """
        if obj.actor:
            return format_html(
                '<a href="/admin/auth/user/{}/change/">{}</a>',
                obj.actor.id,
                obj.actor.username
            )
        return "System"
    actor_display.short_description = "Actor"
    
    def action_type_display(self, obj):
        """Action Type """
        colors = {
            'create': '#28a745',
            'update': '#007bff',
            'delete': '#dc3545',
            'view': '#6c757d',
            'assign': '#fd7e14',
            'status_change': '#ffc107',
            'comment': '#17a2b8',
            'mention': '#e83e8c',
            'login': '#20c997',
            'logout': '#6f42c1',
            'upload': '#5cb85c',
            'download': '#5bc0de',
            'share': '#f0ad4e',
            'archive': '#d9534f',
            'restore': '#5cb85c',
        }
        color = colors.get(obj.action_type, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 12px;">{}</span>',
            color,
            obj.get_action_type_display()
        )
    action_type_display.short_description = "Action"
    
    def action_description_short(self, obj):
        """Action Description """
        if len(obj.action_description) > 50:
            return f"{obj.action_description[:50]}..."
        return obj.action_description
    action_description_short.short_description = "Description"
    
    def content_object_display(self, obj):
        """ """
        if obj.content_object:
            return format_html(
                '<span style="color: purple;">{} ({})</span>',
                str(obj.content_object),
                obj.content_object._meta.verbose_name
            )
        return "-"
    content_object_display.short_description = "Content Object"
    
    def organization_display(self, obj):
        """Organization """
        if obj.organization:
            return obj.organization.name
        return "-"
    organization_display.short_description = "Organization"
    
    def has_delete_permission(self, request, obj=None):
        """Delete - Admin """
        return False
    
    def has_add_permission(self, request):
        """Add - """
        return False
    
    def has_change_permission(self, request, obj=None):
        """Change - """
        return False


# ========================================
# . Reaction Admin
# ========================================

@admin.register(Reaction)
class ReactionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'reaction_type_display', 'content_object_display',
        'created_at'
    ]
    list_filter = ['reaction_type', 'created_at']
    search_fields = ['user__username', 'content_type__app_label']
    readonly_fields = ['id', 'created_at', 'updated_at']
    raw_id_fields = ['user']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Reaction Information', {
            'fields': ('user', 'reaction_type')
        }),
        ('Related Object', {
            'fields': ('content_type', 'object_id')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def reaction_type_display(self, obj):
        """Reaction Type """
        emojis = {
            'like': 'Like',
            'love': 'Love',
            'laugh': 'Laugh',
            'sad': 'Sad',
            'angry': 'Angry',
            'wow': 'Wow',
            'applause': 'Applause',
            'thumbs_down': 'Dislike',
            'rocket': 'Rocket',
            'fire': 'Fire',
        }
        emoji = emojis.get(obj.reaction_type, '')
        return format_html(
            '{} <span style="font-size: 14px;">{}</span>',
            emoji,
            obj.get_reaction_type_display()
        )
    reaction_type_display.short_description = "Reaction"
    
    def content_object_display(self, obj):
        """ """
        if obj.content_object:
            return format_html(
                '<span style="color: orange;">{} ({})</span>',
                str(obj.content_object),
                obj.content_object._meta.verbose_name
            )
        return "-"
    content_object_display.short_description = "Content Object"
    
    actions = ['delete_selected_reactions']


# ========================================
# . Admin Panel Customization
# ========================================

admin.site.site_header = "Collaboration Admin Panel"
admin.site.site_title = "Collaboration Admin"
admin.site.index_title = "Welcome to Collaboration Admin Panel"