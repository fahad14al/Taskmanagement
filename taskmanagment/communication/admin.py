# communication/admin.py
from django.contrib import admin
from .models import ChatRoom, ChatRoomMember, Message, MessageRead, Presence

class ChatRoomMemberInline(admin.TabularInline):
    model = ChatRoomMember
    extra = 1

@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'room_type', 'is_active', 'member_count', 'last_message_at']
    list_filter = ['room_type', 'is_active', 'is_private']
    search_fields = ['name', 'room_id']
    filter_horizontal = ['admins']
    readonly_fields = ['room_id', 'created_at', 'updated_at']
    inlines = [ChatRoomMemberInline]
    
    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = 'Members'

@admin.register(ChatRoomMember)
class ChatRoomMemberAdmin(admin.ModelAdmin):
    list_display = ['chat_room', 'user', 'role', 'is_active', 'joined_at']
    list_filter = ['role', 'is_active']
    search_fields = ['chat_room__name', 'user__username']

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'sender', 'chat_room', 'content_short', 'message_type', 'created_at']
    list_filter = ['message_type', 'is_edited', 'is_deleted', 'is_pinned']
    search_fields = ['content', 'sender__username']
    readonly_fields = ['message_id', 'created_at', 'updated_at']
    
    def content_short(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_short.short_description = 'Content'

@admin.register(MessageRead)
class MessageReadAdmin(admin.ModelAdmin):
    list_display = ['message', 'user', 'is_read', 'read_at']
    list_filter = ['is_read']
    search_fields = ['user__username']
    readonly_fields = ['delivered_at']

@admin.register(Presence)
class PresenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'status', 'last_activity', 'is_online']
    list_filter = ['status']
    search_fields = ['user__username']
    readonly_fields = ['created_at', 'updated_at']
    
    def is_online(self, obj):
        return obj.is_online()
    is_online.boolean = True