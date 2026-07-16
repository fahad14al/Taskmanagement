# communication/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q
from .models import ChatRoom, ChatRoomMember, Message, MessageRead, Presence


# ========================================
# ১. Presence Serializer
# ========================================

class PresenceSerializer(serializers.ModelSerializer):
    """Presence এর জন্য Serializer"""
    username = serializers.ReadOnlyField(source='user.username')
    full_name = serializers.SerializerMethodField()
    profile_picture = serializers.SerializerMethodField()
    status_display = serializers.ReadOnlyField(source='get_status_display')
    is_online = serializers.SerializerMethodField()
    last_activity_ago = serializers.SerializerMethodField()

    class Meta:
        model = Presence
        fields = [
            'id', 'user', 'username', 'full_name', 'profile_picture',
            'status', 'status_display', 'custom_status', 'is_online',
            'last_activity', 'last_activity_ago', 'last_seen',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username

    def get_profile_picture(self, obj):
        if hasattr(obj.user, 'profile') and obj.user.profile.profile_picture:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.user.profile.profile_picture.url)
            return obj.user.profile.profile_picture.url
        return None

    def get_is_online(self, obj):
        return obj.is_online()

    def get_last_activity_ago(self, obj):
        now = timezone.now()
        diff = now - obj.last_activity
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


class PresenceUpdateSerializer(serializers.ModelSerializer):
    """Presence আপডেট করার জন্য Serializer"""

    class Meta:
        model = Presence
        fields = ['status', 'custom_status']


# ========================================
# ২. ChatRoomMember Serializer
# ========================================

class ChatRoomMemberSerializer(serializers.ModelSerializer):
    """ChatRoomMember এর জন্য Serializer"""
    username = serializers.ReadOnlyField(source='user.username')
    full_name = serializers.SerializerMethodField()
    profile_picture = serializers.SerializerMethodField()
    role_display = serializers.ReadOnlyField(source='get_role_display')
    presence = PresenceSerializer(source='user.presence', read_only=True)
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoomMember
        fields = [
            'id', 'user', 'username', 'full_name', 'profile_picture',
            'role', 'role_display', 'presence', 'unread_count',
            'is_muted', 'muted_until', 'last_read_at', 'joined_at', 'is_active'
        ]
        read_only_fields = ['id', 'joined_at', 'is_active']

    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username

    def get_profile_picture(self, obj):
        if hasattr(obj.user, 'profile') and obj.user.profile.profile_picture:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.user.profile.profile_picture.url)
            return obj.user.profile.profile_picture.url
        return None

    def get_unread_count(self, obj):
        """ইউজারের জন্য আনরিড মেসেজ কাউন্ট"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.chat_room.get_unread_count(request.user)
        return 0


# ========================================
# ৩. MessageRead Serializer
# ========================================

class MessageReadSerializer(serializers.ModelSerializer):
    """MessageRead এর জন্য Serializer"""
    username = serializers.ReadOnlyField(source='user.username')
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = MessageRead
        fields = [
            'id', 'user', 'username', 'full_name',
            'is_read', 'read_at', 'delivered_at'
        ]
        read_only_fields = ['id', 'delivered_at']

    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username


# ========================================
# ৪. Message Serializer
# ========================================

class MessageSerializer(serializers.ModelSerializer):
    """Message এর জন্য Serializer"""
    sender_username = serializers.ReadOnlyField(source='sender.username')
    sender_full_name = serializers.SerializerMethodField()
    sender_profile_picture = serializers.SerializerMethodField()
    message_type_display = serializers.ReadOnlyField(source='get_message_type_display')
    read_count = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    is_read_by_user = serializers.SerializerMethodField()
    reply_to = serializers.SerializerMethodField()
    time_ago = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            'id', 'message_id', 'chat_room', 'sender', 'sender_username',
            'sender_full_name', 'sender_profile_picture', 'parent_message',
            'reply_to', 'message_type', 'message_type_display', 'content',
            'attachments', 'metadata', 'is_edited', 'is_deleted', 'is_pinned',
            'is_system', 'read_count', 'unread_count', 'is_read_by_user',
            'time_ago', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'message_id', 'sender', 'created_at', 'updated_at',
            'is_edited', 'is_deleted'
        ]

    def get_sender_full_name(self, obj):
        return f"{obj.sender.first_name} {obj.sender.last_name}".strip() or obj.sender.username

    def get_sender_profile_picture(self, obj):
        if hasattr(obj.sender, 'profile') and obj.sender.profile.profile_picture:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.sender.profile.profile_picture.url)
            return obj.sender.profile.profile_picture.url
        return None

    def get_read_count(self, obj):
        return obj.get_read_count()

    def get_unread_count(self, obj):
        return obj.get_unread_count()

    def get_is_read_by_user(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.is_read_by_user(request.user)
        return False

    def get_reply_to(self, obj):
        if obj.parent_message:
            return {
                'id': obj.parent_message.id,
                'content': obj.parent_message.content[:100],
                'sender_username': obj.parent_message.sender.username
            }
        return None

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
        elif seconds < 604800:
            days = int(seconds // 86400)
            return f"{days} day{'s' if days > 1 else ''} ago"
        else:
            weeks = int(seconds // 604800)
            return f"{weeks} week{'s' if weeks > 1 else ''} ago"


class MessageCreateSerializer(serializers.ModelSerializer):
    """Message তৈরি করার জন্য Serializer"""

    class Meta:
        model = Message
        fields = [
            'chat_room', 'parent_message', 'message_type',
            'content', 'attachments', 'metadata', 'is_system'
        ]

    def validate_content(self, value):
        if not value and not self.initial_data.get('attachments'):
            raise serializers.ValidationError("Content or attachments required")
        return value

    def create(self, validated_data):
        validated_data['sender'] = self.context['request'].user
        return super().create(validated_data)


class MessageUpdateSerializer(serializers.ModelSerializer):
    """Message আপডেট করার জন্য Serializer"""

    class Meta:
        model = Message
        fields = ['content', 'attachments', 'metadata']

    def update(self, instance, validated_data):
        instance.content = validated_data.get('content', instance.content)
        instance.attachments = validated_data.get('attachments', instance.attachments)
        instance.metadata = validated_data.get('metadata', instance.metadata)
        instance.is_edited = True
        instance.save()
        return instance


# ========================================
# ৫. ChatRoom Serializer
# ========================================

class ChatRoomListSerializer(serializers.ModelSerializer):
    """ChatRoom লিস্টের জন্য Serializer"""
    room_type_display = serializers.ReadOnlyField(source='get_room_type_display')
    member_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    other_member = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = [
            'id', 'room_id', 'name', 'room_type', 'room_type_display',
            'description', 'is_private', 'is_active', 'is_archived',
            'avatar', 'member_count', 'last_message', 'unread_count',
            'other_member', 'last_message_at', 'created_at'
        ]
        read_only_fields = ['id', 'room_id', 'created_at', 'updated_at']

    def get_member_count(self, obj):
        return obj.get_member_count()

    def get_last_message(self, obj):
        last_msg = obj.get_last_message()
        if last_msg:
            return {
                'id': last_msg.id,
                'content': last_msg.content[:100],
                'sender_username': last_msg.sender.username,
                'created_at': last_msg.created_at
            }
        return None

    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.get_unread_count(request.user)
        return 0

    def get_other_member(self, obj):
        """Direct চ্যাটের জন্য অন্য ইউজার"""
        request = self.context.get('request')
        if request and request.user.is_authenticated and obj.room_type == 'direct':
            other = obj.get_other_member(request.user)
            if other:
                return {
                    'id': other.id,
                    'username': other.username,
                    'full_name': f"{other.first_name} {other.last_name}".strip() or other.username,
                    'presence': PresenceSerializer(other.presence).data if hasattr(other, 'presence') else None
                }
        return None


class ChatRoomDetailSerializer(serializers.ModelSerializer):
    """ChatRoom বিস্তারিত তথ্যের জন্য Serializer"""
    room_type_display = serializers.ReadOnlyField(source='get_room_type_display')
    created_by_username = serializers.ReadOnlyField(source='created_by.username')
    members = ChatRoomMemberSerializer(
        source='room_members',
        many=True,
        read_only=True
    )
    admins = serializers.SerializerMethodField()
    recent_messages = serializers.SerializerMethodField()
    member_count = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    content_object_type = serializers.SerializerMethodField()
    content_object_repr = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = [
            'id', 'room_id', 'name', 'room_type', 'room_type_display',
            'description', 'created_by', 'created_by_username',
            'members', 'admins', 'member_count', 'unread_count',
            'is_private', 'is_active', 'is_archived',
            'avatar', 'content_object_type', 'content_object_repr',
            'recent_messages', 'last_message_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'room_id', 'created_at', 'updated_at']

    def get_admins(self, obj):
        admins = obj.admins.all()
        return [
            {
                'id': user.id,
                'username': user.username,
                'full_name': f"{user.first_name} {user.last_name}".strip() or user.username
            }
            for user in admins
        ]

    def get_recent_messages(self, obj):
        messages = obj.messages.filter(is_deleted=False)[:20]
        return MessageSerializer(messages, many=True, context=self.context).data

    def get_member_count(self, obj):
        return obj.get_member_count()

    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.get_unread_count(request.user)
        return 0

    def get_content_object_type(self, obj):
        if obj.content_object:
            return obj.content_object._meta.verbose_name
        return None

    def get_content_object_repr(self, obj):
        return str(obj.content_object) if obj.content_object else None


class ChatRoomCreateSerializer(serializers.ModelSerializer):
    """ChatRoom তৈরি করার জন্য Serializer"""
    member_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=True,
        help_text="List of user IDs to add as members"
    )
    admin_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="List of user IDs to add as admins"
    )
    content_type = serializers.CharField(
        write_only=True,
        required=False,
        help_text="Content type for Generic FK (e.g., 'accounts.project')"
    )
    object_id = serializers.IntegerField(
        write_only=True,
        required=False,
        help_text="Object ID for Generic FK"
    )

    class Meta:
        model = ChatRoom
        fields = [
            'name', 'room_type', 'description', 'is_private',
            'member_ids', 'admin_ids', 'content_type', 'object_id'
        ]

    def validate_member_ids(self, value):
        if not value:
            raise serializers.ValidationError("At least one member is required")
        return value

    def validate_content_type(self, value):
        if value:
            try:
                from django.contrib.contenttypes.models import ContentType
                app_label, model = value.split('.')
                return ContentType.objects.get(app_label=app_label, model=model)
            except:
                raise serializers.ValidationError(f"Invalid content type: {value}")
        return None

    def create(self, validated_data):
        member_ids = validated_data.pop('member_ids')
        admin_ids = validated_data.pop('admin_ids', [])
        content_type = validated_data.pop('content_type', None)
        object_id = validated_data.pop('object_id', None)

        # ChatRoom তৈরি
        validated_data['created_by'] = self.context['request'].user
        chat_room = ChatRoom.objects.create(**validated_data)

        # Content Object সেট
        if content_type and object_id:
            chat_room.content_type = content_type
            chat_room.object_id = object_id
            chat_room.save()

        # সদস্য যোগ করুন
        for user_id in member_ids:
            try:
                user = User.objects.get(id=user_id)
                role = 'admin' if user_id in admin_ids else 'member'
                ChatRoomMember.objects.create(
                    chat_room=chat_room,
                    user=user,
                    role=role
                )
                chat_room.members.add(user)
                if role == 'admin':
                    chat_room.admins.add(user)
            except User.DoesNotExist:
                continue

        # সৃষ্টিকর্তাকে অ্যাডমিন হিসেবে যোগ করুন
        created_by = self.context['request'].user
        if created_by.id not in member_ids:
            ChatRoomMember.objects.create(
                chat_room=chat_room,
                user=created_by,
                role='admin'
            )
            chat_room.members.add(created_by)
            chat_room.admins.add(created_by)

        return chat_room


class ChatRoomUpdateSerializer(serializers.ModelSerializer):
    """ChatRoom আপডেট করার জন্য Serializer"""

    class Meta:
        model = ChatRoom
        fields = ['name', 'description', 'avatar', 'is_private', 'is_archived']


# ========================================
# ৬. ChatRoomMember Manage Serializer
# ========================================

class AddMemberSerializer(serializers.Serializer):
    """ChatRoom এ সদস্য যোগ করার Serializer"""
    user_id = serializers.IntegerField(required=True)
    role = serializers.ChoiceField(
        choices=ChatRoomMember.ROLE_CHOICES,
        default='member'
    )

    def validate_user_id(self, value):
        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")
        return value


class RemoveMemberSerializer(serializers.Serializer):
    """ChatRoom থেকে সদস্য সরানোর Serializer"""
    user_id = serializers.IntegerField(required=True)


# ========================================
# ৭. Dashboard Serializer
# ========================================

class ChatStatsSerializer(serializers.Serializer):
    """Chat পরিসংখ্যান"""
    total_chat_rooms = serializers.IntegerField()
    total_messages = serializers.IntegerField()
    unread_messages = serializers.IntegerField()
    online_users = serializers.IntegerField()
    recent_chats = ChatRoomListSerializer(many=True)
    recent_messages = MessageSerializer(many=True)


# ========================================
# ৮. Helper Serializers
# ========================================

class MarkReadSerializer(serializers.Serializer):
    """মেসেজ রিড মার্ক করার Serializer"""
    message_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="List of message IDs to mark as read"
    )
    chat_room_id = serializers.IntegerField(
        required=False,
        help_text="Mark all messages in this chat room as read"
    )
    mark_all = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Mark all messages as read"
    )

    def validate(self, data):
        if not data.get('message_ids') and not data.get('chat_room_id') and not data.get('mark_all'):
            raise serializers.ValidationError(
                "Either message_ids, chat_room_id, or mark_all is required"
            )
        return data


class TypingIndicatorSerializer(serializers.Serializer):
    """টাইপিং ইন্ডিকেটরের জন্য Serializer"""
    chat_room_id = serializers.IntegerField(required=True)
    is_typing = serializers.BooleanField(required=True)