# communication/tests.py
from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from datetime import timedelta
import json

from .models import ChatRoom, ChatRoomMember, Message, MessageRead, Presence
from .serializers import (
    ChatRoomListSerializer, ChatRoomDetailSerializer, ChatRoomCreateSerializer,
    MessageSerializer, MessageCreateSerializer, PresenceSerializer,
    ChatRoomMemberSerializer, MessageReadSerializer
)


# ========================================
# . Model Tests
# ========================================

class ChatRoomModelTest(TestCase):
    """ChatRoom """

    def setUp(self):
        self.user1 = User.objects.create_user(
            username='user1',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            password='testpass123'
        )

    def test_create_direct_chat(self):
        """Direct Chat """
        from communication.models import get_or_create_direct_chat

        chat_room = get_or_create_direct_chat(self.user1, self.user2)

        self.assertEqual(chat_room.room_type, 'direct')
        self.assertEqual(chat_room.members.count(), 2)
        self.assertIn(self.user1, chat_room.members.all())
        self.assertIn(self.user2, chat_room.members.all())

    def test_get_or_create_direct_chat_existing(self):
        """ Direct Chat """
        from communication.models import get_or_create_direct_chat

        chat1 = get_or_create_direct_chat(self.user1, self.user2)
        chat2 = get_or_create_direct_chat(self.user1, self.user2)

        self.assertEqual(chat1, chat2)
        self.assertEqual(chat1.members.count(), 2)

    def test_create_group_chat(self):
        """Group Chat """
        from communication.models import get_group_chat

        user3 = User.objects.create_user(username='user3', password='testpass123')
        members = [self.user2, user3]

        chat_room = get_group_chat(
            name='Test Group',
            created_by=self.user1,
            members=members
        )

        self.assertEqual(chat_room.room_type, 'group')
        self.assertEqual(chat_room.name, 'Test Group')
        self.assertEqual(chat_room.members.count(), 3)
        self.assertIn(self.user1, chat_room.admins.all())

    def test_chat_room_str_method(self):
        """__str__ """
        from communication.models import get_or_create_direct_chat

        chat_room = get_or_create_direct_chat(self.user1, self.user2)
        expected_str = f"Chat between {self.user1.username}, {self.user2.username}"
        self.assertEqual(str(chat_room), expected_str)

    def test_get_other_member(self):
        """get_other_member """
        from communication.models import get_or_create_direct_chat

        chat_room = get_or_create_direct_chat(self.user1, self.user2)
        other = chat_room.get_other_member(self.user1)

        self.assertEqual(other, self.user2)

    def test_get_member_count(self):
        """get_member_count """
        from communication.models import get_or_create_direct_chat

        chat_room = get_or_create_direct_chat(self.user1, self.user2)
        self.assertEqual(chat_room.get_member_count(), 2)

    def test_get_unread_count(self):
        """get_unread_count """
        from communication.models import get_or_create_direct_chat

        chat_room = get_or_create_direct_chat(self.user1, self.user2)

        # 
        from communication.models import Message
        message = Message.objects.create(
            chat_room=chat_room,
            sender=self.user1,
            content='Hello'
        )

        # user2- 
        unread_count = chat_room.get_unread_count(self.user2)
        self.assertEqual(unread_count, 1)

        # user1- ( )
        unread_count = chat_room.get_unread_count(self.user1)
        self.assertEqual(unread_count, 0)


class MessageModelTest(TestCase):
    """Message """

    def setUp(self):
        self.user1 = User.objects.create_user(
            username='user1',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            password='testpass123'
        )

        from communication.models import get_or_create_direct_chat
        self.chat_room = get_or_create_direct_chat(self.user1, self.user2)

    def test_create_message(self):
        """Message """
        from communication.models import Message

        message = Message.objects.create(
            chat_room=self.chat_room,
            sender=self.user1,
            content='Test message'
        )

        self.assertEqual(message.sender, self.user1)
        self.assertEqual(message.content, 'Test message')
        self.assertEqual(message.chat_room, self.chat_room)
        self.assertFalse(message.is_edited)
        self.assertFalse(message.is_deleted)

    def test_message_with_attachments(self):
        """Attachment Message """
        from communication.models import Message

        attachments = [
            {'name': 'file1.pdf', 'url': '/media/file1.pdf'},
            {'name': 'image.png', 'url': '/media/image.png'}
        ]

        message = Message.objects.create(
            chat_room=self.chat_room,
            sender=self.user1,
            content='With attachments',
            attachments=attachments
        )

        self.assertEqual(message.attachments, attachments)
        self.assertEqual(len(message.attachments), 2)

    def test_message_read_records_created(self):
        """Message MessageRead """
        from communication.models import Message, MessageRead

        message = Message.objects.create(
            chat_room=self.chat_room,
            sender=self.user1,
            content='Test message'
        )

        # 
        self.assertTrue(MessageRead.objects.filter(
            message=message,
            user=self.user1,
            is_read=True
        ).exists())

        # 
        self.assertTrue(MessageRead.objects.filter(
            message=message,
            user=self.user2,
            is_read=False
        ).exists())

    def test_soft_delete_message(self):
        """Message """
        from communication.models import Message

        message = Message.objects.create(
            chat_room=self.chat_room,
            sender=self.user1,
            content='Test message'
        )

        self.assertFalse(message.is_deleted)

        message.soft_delete()

        self.assertTrue(message.is_deleted)
        self.assertIsNotNone(message.deleted_at)

    def test_message_str_method(self):
        """__str__ """
        from communication.models import Message

        message = Message.objects.create(
            chat_room=self.chat_room,
            sender=self.user1,
            content='Test message'
        )

        expected_str = f"{self.user1.username}: Test message..."
        self.assertEqual(str(message), expected_str)


class PresenceModelTest(TestCase):
    """Presence """

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.presence = self.user.presence

    def test_presence_created_automatically(self):
        """User Presence """
        new_user = User.objects.create_user(
            username='newuser',
            password='testpass123'
        )
        self.assertTrue(hasattr(new_user, 'presence'))
        self.assertEqual(new_user.presence.status, 'offline')

    def test_update_status(self):
        """status """
        self.presence.update_status('online', custom_status='Working')

        self.assertEqual(self.presence.status, 'online')
        self.assertEqual(self.presence.custom_status, 'Working')

    def test_is_online(self):
        """is_online """
        self.presence.status = 'online'
        self.presence.save()

        self.assertTrue(self.presence.is_online())

        self.presence.status = 'offline'
        self.presence.save()

        self.assertFalse(self.presence.is_online())

    def test_update_activity(self):
        """update_activity """
        old_activity = self.presence.last_activity

        # 
        import time
        time.sleep(1)

        self.presence.update_activity()

        self.assertGreater(self.presence.last_activity, old_activity)


# ========================================
# . Serializer Tests
# ========================================

class ChatRoomSerializerTest(APITestCase):
    """ChatRoom Serializer """

    def setUp(self):
        self.user1 = User.objects.create_user(
            username='user1',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user1)

        from rest_framework.test import APIRequestFactory
        factory = APIRequestFactory()
        self.request = factory.get('/')
        self.request.user = self.user1

        from communication.models import get_or_create_direct_chat
        self.chat_room = get_or_create_direct_chat(self.user1, self.user2)

        # Message 
        from communication.models import Message
        self.message = Message.objects.create(
            chat_room=self.chat_room,
            sender=self.user1,
            content='Hello world!'
        )

    def test_chat_room_list_serializer(self):
        """ChatRoomListSerializer """
        serializer = ChatRoomListSerializer(
            self.chat_room,
            context={'request': self.request}
        )
        data = serializer.data

        self.assertEqual(data['id'], self.chat_room.id)
        self.assertEqual(data['room_type'], 'direct')
        self.assertEqual(data['member_count'], 2)
        self.assertIsNotNone(data['last_message'])

    def test_chat_room_detail_serializer(self):
        """ChatRoomDetailSerializer """
        serializer = ChatRoomDetailSerializer(
            self.chat_room,
            context={'request': self.request}
        )
        data = serializer.data

        self.assertEqual(data['id'], self.chat_room.id)
        self.assertEqual(data['member_count'], 2)
        self.assertIn('members', data)
        self.assertIn('recent_messages', data)
        self.assertEqual(len(data['recent_messages']), 1)

    def test_chat_room_create_serializer(self):
        """ChatRoomCreateSerializer """
        from communication.serializers import ChatRoomCreateSerializer

        data = {
            'name': 'Test Group',
            'room_type': 'group',
            'member_ids': [self.user2.id],
            'admin_ids': [self.user2.id]
        }

        serializer = ChatRoomCreateSerializer(
            data=data,
            context={'request': self.request}
        )

        self.assertTrue(serializer.is_valid())
        chat_room = serializer.save()

        self.assertEqual(chat_room.name, 'Test Group')
        self.assertEqual(chat_room.members.count(), 2)  # user1 + user2
        self.assertEqual(chat_room.admins.count(), 2)   # user1 + user2

    def test_chat_room_create_serializer_invalid(self):
        """Invalid ChatRoomCreateSerializer """
        from communication.serializers import ChatRoomCreateSerializer

        data = {
            'name': 'Test Group',
            'room_type': 'group',
            'member_ids': []  # Empty members
        }

        serializer = ChatRoomCreateSerializer(
            data=data,
            context={'request': self.request}
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('member_ids', serializer.errors)


class MessageSerializerTest(APITestCase):
    """Message Serializer """

    def setUp(self):
        self.user1 = User.objects.create_user(
            username='user1',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user1)

        from rest_framework.test import APIRequestFactory
        factory = APIRequestFactory()
        self.request = factory.get('/')
        self.request.user = self.user1

        from communication.models import get_or_create_direct_chat
        self.chat_room = get_or_create_direct_chat(self.user1, self.user2)

    def test_message_serializer(self):
        """MessageSerializer """
        from communication.models import Message

        message = Message.objects.create(
            chat_room=self.chat_room,
            sender=self.user1,
            content='Test message'
        )

        serializer = MessageSerializer(
            message,
            context={'request': self.request}
        )
        data = serializer.data

        self.assertEqual(data['content'], 'Test message')
        self.assertEqual(data['sender_username'], 'user1')
        self.assertEqual(data['read_count'], 1)  # user1
        self.assertIn('time_ago', data)

    def test_message_create_serializer(self):
        """MessageCreateSerializer """
        from communication.serializers import MessageCreateSerializer

        data = {
            'chat_room': self.chat_room.id,
            'content': 'New message from serializer'
        }

        serializer = MessageCreateSerializer(
            data=data,
            context={'request': self.request}
        )

        self.assertTrue(serializer.is_valid())
        message = serializer.save()

        self.assertEqual(message.content, 'New message from serializer')
        self.assertEqual(message.sender, self.user1)

    def test_message_create_serializer_with_attachments(self):
        """Attachment MessageCreateSerializer """
        from communication.serializers import MessageCreateSerializer

        data = {
            'chat_room': self.chat_room.id,
            'content': 'With attachments',
            'attachments': [
                {'name': 'file.pdf', 'url': '/media/file.pdf'}
            ]
        }

        serializer = MessageCreateSerializer(
            data=data,
            context={'request': self.request}
        )

        self.assertTrue(serializer.is_valid())
        message = serializer.save()

        self.assertEqual(message.attachments[0]['name'], 'file.pdf')

    def test_message_create_serializer_empty_content(self):
        """Empty content MessageCreateSerializer """
        from communication.serializers import MessageCreateSerializer

        data = {
            'chat_room': self.chat_room.id,
            'content': ''
        }

        serializer = MessageCreateSerializer(
            data=data,
            context={'request': self.request}
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('content', serializer.errors)


class PresenceSerializerTest(APITestCase):
    """Presence Serializer """

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        from rest_framework.test import APIRequestFactory
        factory = APIRequestFactory()
        self.request = factory.get('/')
        self.request.user = self.user

    def test_presence_serializer(self):
        """PresenceSerializer """
        presence = self.user.presence
        presence.update_status('online')

        serializer = PresenceSerializer(
            presence,
            context={'request': self.request}
        )
        data = serializer.data

        self.assertEqual(data['status'], 'online')
        self.assertEqual(data['username'], 'testuser')
        self.assertTrue(data['is_online'])
        self.assertIn('last_activity_ago', data)

    def test_presence_update_serializer(self):
        """PresenceUpdateSerializer """
        from communication.serializers import PresenceUpdateSerializer

        data = {
            'status': 'busy',
            'custom_status': 'In a meeting'
        }

        serializer = PresenceUpdateSerializer(
            self.user.presence,
            data=data,
            partial=True
        )

        self.assertTrue(serializer.is_valid())
        presence = serializer.save()

        self.assertEqual(presence.status, 'busy')
        self.assertEqual(presence.custom_status, 'In a meeting')


# ========================================
# . API Tests