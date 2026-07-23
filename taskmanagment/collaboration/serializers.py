# collaboration/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from .models import Comment, Mention, Notification, ActivityLog, Reaction


# ========================================
# . Comment Serializer
# ========================================

class CommentSerializer(serializers.ModelSerializer):
    """Comment Serializer"""
    author_username = serializers.ReadOnlyField(source='author.username')
    author_full_name = serializers.SerializerMethodField()
    author_profile_picture = serializers.SerializerMethodField()
    reply_count = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()
    content_object_type = serializers.SerializerMethodField()
    content_object_repr = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = [
            'id', 'author', 'author_username', 'author_full_name', 
            'author_profile_picture', 'parent', 'content', 
            'attachment', 'reply_count', 'is_owner',
            'content_object_type', 'content_object_repr',
            'created_at', 'updated_at', 'is_edited', 'is_deleted'
        ]
        read_only_fields = ['id', 'author', 'created_at', 'updated_at', 'is_edited']

    def get_author_full_name(self, obj):
        """Author """
        return f"{obj.author.first_name} {obj.author.last_name}".strip() or obj.author.username

    def get_author_profile_picture(self, obj):
        """Author URL"""
        if hasattr(obj.author, 'profile') and obj.author.profile.profile_picture:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.author.profile.profile_picture.url)
            return obj.author.profile.profile_picture.url
        return None

    def get_reply_count(self, obj):
        """Number of replies"""
        return obj.reply_count

    def get_is_owner(self, obj):
        """ """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.is_owner(request.user)
        return False

    def get_content_object_type(self, obj):
        """ """
        if obj.content_object:
            return obj.content_object._meta.verbose_name
        return None

    def get_content_object_repr(self, obj):
        """ """
        return str(obj.content_object) if obj.content_object else None


class CommentCreateSerializer(serializers.ModelSerializer):
    """Comment Serializer"""
    content_type = serializers.CharField(write_only=True)
    object_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Comment
        fields = ['content', 'parent', 'attachment', 'content_type', 'object_id']

    def validate_content_type(self, value):
        """Content Type """
        try:
            app_label, model = value.split('.', 1)
            content_type = ContentType.objects.get(app_label=app_label, model=model)
            return content_type
        except ContentType.DoesNotExist:
            raise serializers.ValidationError(f"Invalid content type: {value}")

    def create(self, validated_data):
        """ """
        content_type = validated_data.pop('content_type')
        object_id = validated_data.pop('object_id')
        validated_data['author'] = self.context['request'].user
        validated_data['content_object'] = content_type.get_object_for_this_type(id=object_id)
        return super().create(validated_data)


class CommentUpdateSerializer(serializers.ModelSerializer):
    """Comment Serializer"""
    class Meta:
        model = Comment
        fields = ['content', 'attachment']

    def update(self, instance, validated_data):
        """ """
        instance.content = validated_data.get('content', instance.content)
        instance.attachment = validated_data.get('attachment', instance.attachment)
        instance.is_edited = True
        instance.save()
        return instance


# ========================================
# . Mention Serializer
# ========================================

class MentionSerializer(serializers.ModelSerializer):
    """Mention Serializer"""
    mentioned_user_username = serializers.ReadOnlyField(source='mentioned_user.username')
    mentioned_user_full_name = serializers.SerializerMethodField()
    mentioned_by_username = serializers.ReadOnlyField(source='mentioned_by.username')
    mentioned_by_full_name = serializers.SerializerMethodField()
    content_object_type = serializers.SerializerMethodField()
    content_object_repr = serializers.SerializerMethodField()
    is_read_display = serializers.SerializerMethodField()

    class Meta:
        model = Mention
        fields = [
            'id', 'mentioned_user', 'mentioned_user_username', 'mentioned_user_full_name',
            'mentioned_by', 'mentioned_by_username', 'mentioned_by_full_name',
            'context', 'context_url', 'is_read', 'is_read_display', 'read_at',
            'content_object_type', 'content_object_repr', 'created_at'
        ]
        read_only_fields = ['id', 'mentioned_by', 'created_at']

    def get_mentioned_user_full_name(self, obj):
        return f"{obj.mentioned_user.first_name} {obj.mentioned_user.last_name}".strip() or obj.mentioned_user.username

    def get_mentioned_by_full_name(self, obj):
        return f"{obj.mentioned_by.first_name} {obj.mentioned_by.last_name}".strip() or obj.mentioned_by.username

    def get_content_object_type(self, obj):
        if obj.content_object:
            return obj.content_object._meta.verbose_name
        return None

    def get_content_object_repr(self, obj):
        return str(obj.content_object) if obj.content_object else None

    def get_is_read_display(self, obj):
        return "Read" if obj.is_read else "Unread"


class MentionCreateSerializer(serializers.ModelSerializer):
    """Mention Serializer"""
    content_type = serializers.CharField(write_only=True)
    object_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Mention
        fields = ['mentioned_user', 'context', 'context_url', 'content_type', 'object_id']

    def validate_content_type(self, value):
        try:
            app_label, model = value.split('.', 1)
            content_type = ContentType.objects.get(app_label=app_label, model=model)
            return content_type
        except ContentType.DoesNotExist:
            raise serializers.ValidationError(f"Invalid content type: {value}")

    def create(self, validated_data):
        content_type = validated_data.pop('content_type')
        object_id = validated_data.pop('object_id')
        validated_data['mentioned_by'] = self.context['request'].user
        validated_data['content_object'] = content_type.get_object_for_this_type(id=object_id)
        return super().create(validated_data)


# ========================================
# . Notification Serializer
# ========================================

class NotificationSerializer(serializers.ModelSerializer):
    """Notification Serializer"""
    recipient_username = serializers.ReadOnlyField(source='recipient.username')
    recipient_full_name = serializers.SerializerMethodField()
    created_by_username = serializers.ReadOnlyField(source='created_by.username')
    notification_type_display = serializers.ReadOnlyField(source='get_notification_type_display')
    priority_display = serializers.ReadOnlyField(source='get_priority_display')
    is_read_display = serializers.SerializerMethodField()
    time_ago = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'id', 'recipient', 'recipient_username', 'recipient_full_name',
            'notification_type', 'notification_type_display',
            'title', 'message', 'priority', 'priority_display',
            'action_url', 'is_read', 'is_read_display', 'read_at',
            'is_sent', 'sent_at', 'created_by', 'created_by_username',
            'time_ago', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def get_recipient_full_name(self, obj):
        return f"{obj.recipient.first_name} {obj.recipient.last_name}".strip() or obj.recipient.username

    def get_is_read_display(self, obj):
        return "Read" if obj.is_read else "Unread"

    def get_time_ago(self, obj):
        """ """
        now = timezone.now()
        diff = now - obj.created_at
        seconds = diff.total_seconds()
        
        if seconds < 60:
            return "Just now"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        elif seconds < 86400:
            hours = int(seconds // 3600)
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif seconds < 604800:
            days = int(seconds // 86400)
            return f"{days} day{'s' if days > 1 else ''} ago"
        else:
            weeks = int(seconds // 604800)
            return f"{weeks} week{'s' if weeks > 1 else ''} ago"


class NotificationCreateSerializer(serializers.ModelSerializer):
    """Notification Serializer"""
    content_type = serializers.CharField(write_only=True, required=False)
    object_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Notification
        fields = [
            'recipient', 'notification_type', 'title', 'message',
            'priority', 'action_url', 'content_type', 'object_id'
        ]

    def validate_content_type(self, value):
        if value:
            try:
                app_label, model = value.split('.', 1)
                return ContentType.objects.get(app_label=app_label, model=model)
            except ContentType.DoesNotExist:
                raise serializers.ValidationError(f"Invalid content type: {value}")
        return None

    def create(self, validated_data):
        content_type = validated_data.pop('content_type', None)
        object_id = validated_data.pop('object_id', None)
        validated_data['created_by'] = self.context['request'].user
        
        if content_type and object_id:
            validated_data['content_object'] = content_type.get_object_for_this_type(id=object_id)
        
        return super().create(validated_data)


class NotificationMarkReadSerializer(serializers.Serializer):
    """Notification Read Serializer"""
    notification_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="Notification IDs to mark as read"
    )
    mark_all = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Mark all notifications as read"
    )


# ========================================
# . ActivityLog Serializer
# ========================================

class ActivityLogSerializer(serializers.ModelSerializer):
    """ActivityLog Serializer"""
    actor_username = serializers.ReadOnlyField(source='actor.username')
    actor_full_name = serializers.SerializerMethodField()
    action_type_display = serializers.ReadOnlyField(source='get_action_type_display')
    content_object_type = serializers.SerializerMethodField()
    content_object_repr = serializers.SerializerMethodField()
    organization_name = serializers.ReadOnlyField(source='organization.name')
    time_ago = serializers.SerializerMethodField()

    class Meta:
        model = ActivityLog
        fields = [
            'id', 'actor', 'actor_username', 'actor_full_name',
            'action_type', 'action_type_display', 'action_description',
            'content_object_type', 'content_object_repr',
            'object_name', 'object_repr', 'changes',
            'ip_address', 'user_agent', 'request_method', 'request_path',
            'organization', 'organization_name',
            'time_ago', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def get_actor_full_name(self, obj):
        if obj.actor:
            return f"{obj.actor.first_name} {obj.actor.last_name}".strip() or obj.actor.username
        return None

    def get_content_object_type(self, obj):
        if obj.content_object:
            return obj.content_object._meta.verbose_name
        return None

    def get_content_object_repr(self, obj):
        return str(obj.content_object) if obj.content_object else None

    def get_time_ago(self, obj):
        now = timezone.now()
        diff = now - obj.created_at
        seconds = diff.total_seconds()
        
        if seconds < 60:
            return "Just now"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        elif seconds < 86400:
            hours = int(seconds // 3600)
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        else:
            days = int(seconds // 86400)
            return f"{days} day{'s' if days > 1 else ''} ago"


class ActivityLogCreateSerializer(serializers.ModelSerializer):
    """ActivityLog Serializer"""
    content_type = serializers.CharField(write_only=True, required=False)
    object_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = ActivityLog
        fields = [
            'action_type', 'action_description', 'content_type', 'object_id',
            'object_name', 'object_repr', 'changes', 'ip_address',
            'user_agent', 'request_method', 'request_path', 'organization'
        ]

    def validate_content_type(self, value):
        if value:
            try:
                app_label, model = value.split('.', 1)
                return ContentType.objects.get(app_label=app_label, model=model)
            except ContentType.DoesNotExist:
                raise serializers.ValidationError(f"Invalid content type: {value}")
        return None

    def create(self, validated_data):
        content_type = validated_data.pop('content_type', None)
        object_id = validated_data.pop('object_id', None)
        validated_data['actor'] = self.context['request'].user
        
        if content_type and object_id:
            validated_data['content_object'] = content_type.get_object_for_this_type(id=object_id)
        
        return super().create(validated_data)


# ========================================
# . Reaction Serializer
# ========================================

class ReactionSerializer(serializers.ModelSerializer):
    """Reaction Serializer"""
    user_username = serializers.ReadOnlyField(source='user.username')
    user_full_name = serializers.SerializerMethodField()
    reaction_type_display = serializers.ReadOnlyField(source='get_reaction_type_display')
    content_object_type = serializers.SerializerMethodField()
    content_object_repr = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = Reaction
        fields = [
            'id', 'user', 'user_username', 'user_full_name',
            'reaction_type', 'reaction_type_display',
            'content_object_type', 'content_object_repr',
            'is_owner', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def get_user_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username

    def get_content_object_type(self, obj):
        if obj.content_object:
            return obj.content_object._meta.verbose_name
        return None

    def get_content_object_repr(self, obj):
        return str(obj.content_object) if obj.content_object else None

    def get_is_owner(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.user == request.user
        return False


class ReactionCreateSerializer(serializers.ModelSerializer):
    """Reaction Serializer"""
    content_type = serializers.CharField(write_only=True)
    object_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Reaction
        fields = ['reaction_type', 'content_type', 'object_id']

    def validate_content_type(self, value):
        try:
            app_label, model = value.split('.', 1)
            return ContentType.objects.get(app_label=app_label, model=model)
        except ContentType.DoesNotExist:
            raise serializers.ValidationError(f"Invalid content type: {value}")

    def create(self, validated_data):
        content_type = validated_data.pop('content_type')
        object_id = validated_data.pop('object_id')
        validated_data['user'] = self.context['request'].user
        # Use content_type and object_id for lookups instead of content_object
        validated_data['content_type'] = content_type
        validated_data['object_id'] = object_id

        # 
        reaction, created = Reaction.objects.get_or_create(
            user=validated_data['user'],
            content_type=content_type,
            object_id=object_id,
            defaults={'reaction_type': validated_data.get('reaction_type')}
        )
        if not created:
            reaction.reaction_type = validated_data['reaction_type']
            reaction.save()
        return reaction


class ReactionStatsSerializer(serializers.Serializer):
    """Reaction """
    reaction_type = serializers.CharField()
    reaction_type_display = serializers.CharField()
    count = serializers.IntegerField()
    users = serializers.ListField(child=serializers.CharField())


# ========================================
# . DashboardSerializer
# ========================================

class CollaborationStatsSerializer(serializers.Serializer):
    """Collaboration """
    total_comments = serializers.IntegerField()
    total_mentions = serializers.IntegerField()
    total_notifications = serializers.IntegerField()
    total_reactions = serializers.IntegerField()
    unread_notifications = serializers.IntegerField()
    recent_comments = CommentSerializer(many=True)
    recent_activities = ActivityLogSerializer(many=True)
    reaction_stats = ReactionStatsSerializer(many=True)