from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import ChatRoom, ChatRoomMember, Message, MessageRead, Presence
from .serializers import (
    ChatRoomListSerializer,
    ChatRoomDetailSerializer,
    ChatRoomCreateSerializer,
    MessageSerializer,
    MessageCreateSerializer,
    PresenceSerializer,
    ChatRoomMemberSerializer,
    MessageReadSerializer,
)


class ChatRoomViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = ChatRoom.objects.filter(is_active=True).order_by('-last_message_at', '-created_at')

    def get_serializer_class(self):
        if self.action == 'create':
            return ChatRoomCreateSerializer
        if self.action == 'retrieve':
            return ChatRoomDetailSerializer
        return ChatRoomListSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return ChatRoom.objects.filter(members=user, is_active=True).order_by('-last_message_at', '-created_at')
        return ChatRoom.objects.none()


class MessageViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Message.objects.filter(is_deleted=False).order_by('created_at')
    serializer_class = MessageSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return MessageCreateSerializer
        return MessageSerializer

    def get_queryset(self):
        user = self.request.user
        qs = Message.objects.filter(is_deleted=False).order_by('created_at')
        room_id = self.request.query_params.get('room_id')
        if room_id:
            qs = qs.filter(chat_room__room_id=room_id)
        if user and user.is_authenticated:
            return qs.filter(chat_room__members=user)
        return qs.none()


class PresenceViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Presence.objects.all().order_by('-last_activity')
    serializer_class = PresenceSerializer

    @action(detail=False, methods=['get'], url_path='me')
    def my_presence(self, request):
        presence, _ = Presence.objects.get_or_create(user=request.user)
        return Response(PresenceSerializer(presence, context={'request': request}).data)
