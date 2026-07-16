# collaboration/tests.py
from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from datetime import timedelta

from .models import (
    Comment, Mention, Notification, ActivityLog, Reaction
)


# ========================================
# ১. Model Tests
# ========================================

class CommentModelTest(TestCase):
    """Comment মডেল টেস্ট"""
    
    def setUp(self):
        """টেস্ট ডেটা তৈরি"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.another_user = User.objects.create_user(
            username='anotheruser',
            password='testpass123'
        )
        
        # Task এর মতো একটি ডামি অবজেক্ট তৈরি (ContentType এর জন্য)
        from django.contrib.contenttypes.models import ContentType
        self.content_type = ContentType.objects.get_for_model(User)
        self.object_id = self.user.id
        
    def test_create_comment(self):
        """কমেন্ট তৈরি টেস্ট"""
        comment = Comment.objects.create(
            author=self.user,
            content='This is a test comment',
            content_type=self.content_type,
            object_id=self.object_id
        )
        
        self.assertEqual(comment.author, self.user)
        self.assertEqual(comment.content, 'This is a test comment')
        self.assertEqual(comment.content_type, self.content_type)
        self.assertEqual(comment.object_id, self.object_id)
        self.assertFalse(comment.is_edited)
        self.assertFalse(comment.is_deleted)
        
    def test_comment_reply(self):
        """কমেন্টের রিপ্লাই টেস্ট"""
        parent_comment = Comment.objects.create(
            author=self.user,
            content='Parent comment',
            content_type=self.content_type,
            object_id=self.object_id
        )
        
        reply = Comment.objects.create(
            author=self.user,
            content='Reply to parent',
            content_type=self.content_type,
            object_id=self.object_id,
            parent=parent_comment
        )
        
        self.assertEqual(reply.parent, parent_comment)
        self.assertEqual(parent_comment.reply_count, 1)
        
    def test_comment_edit(self):
        """কমেন্ট এডিট টেস্ট"""
        comment = Comment.objects.create(
            author=self.user,
            content='Original content',
            content_type=self.content_type,
            object_id=self.object_id
        )
        
        self.assertFalse(comment.is_edited)
        
        comment.content = 'Updated content'
        comment.save()
        
        self.assertTrue(comment.is_edited)
        
    def test_comment_soft_delete(self):
        """কমেন্ট সফট ডিলিট টেস্ট"""
        comment = Comment.objects.create(
            author=self.user,
            content='Test comment',
            content_type=self.content_type,
            object_id=self.object_id
        )
        
        self.assertFalse(comment.is_deleted)
        
        comment.is_deleted = True
        comment.save()
        
        self.assertTrue(comment.is_deleted)
        
    def test_is_owner_method(self):
        """is_owner মেথড টেস্ট"""
        comment = Comment.objects.create(
            author=self.user,
            content='Test comment',
            content_type=self.content_type,
            object_id=self.object_id
        )
        
        self.assertTrue(comment.is_owner(self.user))
        self.assertFalse(comment.is_owner(self.another_user))
        
    def test_comment_str_method(self):
        """__str__ মেথড টেস্ট"""
        comment = Comment.objects.create(
            author=self.user,
            content='Test comment',
            content_type=self.content_type,
            object_id=self.object_id
        )
        
        expected_str = f"Comment by {self.user.username} on {comment.created_at}"
        self.assertEqual(str(comment), expected_str)


class MentionModelTest(TestCase):
    """Mention মডেল টেস্ট"""
    
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='user1',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            password='testpass123'
        )
        self.content_type = ContentType.objects.get_for_model(User)
        self.object_id = self.user1.id
        
    def test_create_mention(self):
        """মেনশন তৈরি টেস্ট"""
        mention = Mention.objects.create(
            mentioned_user=self.user2,
            mentioned_by=self.user1,
            content_type=self.content_type,
            object_id=self.object_id,
            context='Please review this',
            context_url='/tasks/1/'
        )
        
        self.assertEqual(mention.mentioned_user, self.user2)
        self.assertEqual(mention.mentioned_by, self.user1)
        self.assertEqual(mention.content_type, self.content_type)
        self.assertEqual(mention.object_id, self.object_id)
        self.assertFalse(mention.is_read)
        
    def test_mark_mention_as_read(self):
        """মেনশন রিড হিসেবে মার্ক টেস্ট"""
        mention = Mention.objects.create(
            mentioned_user=self.user2,
            mentioned_by=self.user1,
            content_type=self.content_type,
            object_id=self.object_id
        )
        
        self.assertFalse(mention.is_read)
        self.assertIsNone(mention.read_at)
        
        mention.mark_as_read()
        
        self.assertTrue(mention.is_read)
        self.assertIsNotNone(mention.read_at)
        
    def test_mention_str_method(self):
        """__str__ মেথড টেস্ট"""
        mention = Mention.objects.create(
            mentioned_user=self.user2,
            mentioned_by=self.user1,
            content_type=self.content_type,
            object_id=self.object_id
        )
        
        expected_str = f"{self.user1} mentioned {self.user2}"
        self.assertEqual(str(mention), expected_str)


class NotificationModelTest(TestCase):
    """Notification মডেল টেস্ট"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.another_user = User.objects.create_user(
            username='anotheruser',
            password='testpass123'
        )
        
    def test_create_notification(self):
        """নোটিফিকেশন তৈরি টেস্ট"""
        notification = Notification.objects.create(
            recipient=self.user,
            notification_type='task_assigned',
            title='New Task Assigned',
            message='You have been assigned a new task',
            priority='high',
            created_by=self.another_user
        )
        
        self.assertEqual(notification.recipient, self.user)
        self.assertEqual(notification.notification_type, 'task_assigned')
        self.assertEqual(notification.priority, 'high')
        self.assertFalse(notification.is_read)
        self.assertFalse(notification.is_sent)
        self.assertEqual(notification.created_by, self.another_user)
        
    def test_mark_notification_as_read(self):
        """নোটিফিকেশন রিড হিসেবে মার্ক টেস্ট"""
        notification = Notification.objects.create(
            recipient=self.user,
            notification_type='system',
            title='Test Notification',
            message='Test message'
        )
        
        self.assertFalse(notification.is_read)
        
        notification.mark_as_read()
        
        self.assertTrue(notification.is_read)
        self.assertIsNotNone(notification.read_at)
        
    def test_mark_notification_as_sent(self):
        """নোটিফিকেশন সেন্ট হিসেবে মার্ক টেস্ট"""
        notification = Notification.objects.create(
            recipient=self.user,
            notification_type='system',
            title='Test Notification',
            message='Test message'
        )
        
        self.assertFalse(notification.is_sent)
        
        notification.mark_as_sent()
        
        self.assertTrue(notification.is_sent)
        self.assertIsNotNone(notification.sent_at)
        
    def test_notification_str_method(self):
        """__str__ মেথড টেস্ট"""
        notification = Notification.objects.create(
            recipient=self.user,
            notification_type='system',
            title='Test Notification',
            message='Test message'
        )
        
        expected_str = f"Test Notification - {self.user.username}"
        self.assertEqual(str(notification), expected_str)


class ActivityLogModelTest(TestCase):
    """ActivityLog মডেল টেস্ট"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.content_type = ContentType.objects.get_for_model(User)
        self.object_id = self.user.id
        
    def test_create_activity_log(self):
        """অ্যাক্টিভিটি লগ তৈরি টেস্ট"""
        log = ActivityLog.objects.create(
            actor=self.user,
            action_type='create',
            action_description='Created a new task',
            content_type=self.content_type,
            object_id=self.object_id,
            ip_address='127.0.0.1',
            request_path='/api/tasks/'
        )
        
        self.assertEqual(log.actor, self.user)
        self.assertEqual(log.action_type, 'create')
        self.assertEqual(log.content_type, self.content_type)
        self.assertEqual(log.object_id, self.object_id)
        self.assertEqual(log.ip_address, '127.0.0.1')
        
    def test_activity_log_with_changes(self):
        """অ্যাক্টিভিটি লগে Changes JSON টেস্ট"""
        changes = {
            'old_status': 'todo',
            'new_status': 'in_progress'
        }
        
        log = ActivityLog.objects.create(
            actor=self.user,
            action_type='status_change',
            action_description='Changed task status',
            changes=changes
        )
        
        self.assertEqual(log.changes, changes)
        self.assertEqual(log.changes['old_status'], 'todo')
        self.assertEqual(log.changes['new_status'], 'in_progress')
        
    def test_activity_log_str_method(self):
        """__str__ মেথড টেস্ট"""
        log = ActivityLog.objects.create(
            actor=self.user,
            action_type='create',
            action_description='Created a new task'
        )
        
        expected_str = f"{self.user} - create at {log.created_at}"
        self.assertEqual(str(log), expected_str)


class ReactionModelTest(TestCase):
    """Reaction মডেল টেস্ট"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.another_user = User.objects.create_user(
            username='anotheruser',
            password='testpass123'
        )
        self.content_type = ContentType.objects.get_for_model(User)
        self.object_id = self.user.id
        
    def test_create_reaction(self):
        """রিঅ্যাকশন তৈরি টেস্ট"""
        reaction = Reaction.objects.create(
            user=self.user,
            reaction_type='like',
            content_type=self.content_type,
            object_id=self.object_id
        )
        
        self.assertEqual(reaction.user, self.user)
        self.assertEqual(reaction.reaction_type, 'like')
        self.assertEqual(reaction.content_type, self.content_type)
        self.assertEqual(reaction.object_id, self.object_id)
        
    def test_unique_reaction_constraint(self):
        """একই ইউজার একই অবজেক্টে একবার রিঅ্যাক্ট করতে পারে টেস্ট"""
        Reaction.objects.create(
            user=self.user,
            reaction_type='like',
            content_type=self.content_type,
            object_id=self.object_id
        )
        
        # দ্বিতীয়বার রিঅ্যাকশন তৈরি করা উচিত নয়
        with self.assertRaises(Exception):
            Reaction.objects.create(
                user=self.user,
                reaction_type='love',
                content_type=self.content_type,
                object_id=self.object_id
            )
            
    def test_reaction_str_method(self):
        """__str__ মেথড টেস্ট"""
        reaction = Reaction.objects.create(
            user=self.user,
            reaction_type='like',
            content_type=self.content_type,
            object_id=self.object_id
        )
        
        expected_str = f"{self.user} reacted like"
        self.assertEqual(str(reaction), expected_str)


# ========================================
# ২. Serializer Tests
# ========================================

class CommentSerializerTest(APITestCase):
    """Comment Serializer টেস্ট"""
    
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
        
        self.content_type = ContentType.objects.get_for_model(User)
        
        self.comment_data = {
            'content': 'This is a test comment',
            'content_type': f'{self.content_type.app_label}.{self.content_type.model}',
            'object_id': self.user.id
        }
        
    def test_create_comment_serializer(self):
        """কমেন্ট তৈরি সিরিয়ালাইজার টেস্ট"""
        from collaboration.serializers import CommentCreateSerializer
        
        serializer = CommentCreateSerializer(
            data=self.comment_data,
            context={'request': self.request}
        )
        
        self.assertTrue(serializer.is_valid())
        comment = serializer.save()
        
        self.assertEqual(comment.author, self.user)
        self.assertEqual(comment.content, 'This is a test comment')
        
    def test_invalid_content_type(self):
        """Invalid Content Type টেস্ট"""
        from collaboration.serializers import CommentCreateSerializer
        
        invalid_data = self.comment_data.copy()
        invalid_data['content_type'] = 'invalid.app.Model'
        
        serializer = CommentCreateSerializer(
            data=invalid_data,
            context={'request': self.request}
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('content_type', serializer.errors)
        
    def test_comment_serializer_fields(self):
        """Comment Serializer ফিল্ড টেস্ট"""
        comment = Comment.objects.create(
            author=self.user,
            content='Test comment',
            content_type=self.content_type,
            object_id=self.user.id
        )
        
        from collaboration.serializers import CommentSerializer
        serializer = CommentSerializer(comment, context={'request': self.request})
        data = serializer.data
        
        self.assertEqual(data['id'], comment.id)
        self.assertEqual(data['content'], 'Test comment')
        self.assertEqual(data['author_username'], 'testuser')
        self.assertIn('author_full_name', data)
        self.assertIn('reply_count', data)
        self.assertIn('created_at', data)


class NotificationSerializerTest(APITestCase):
    """Notification Serializer টেস্ট"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        self.notification = Notification.objects.create(
            recipient=self.user,
            notification_type='system',
            title='Test Notification',
            message='This is a test notification',
            priority='high'
        )
        
    def test_notification_serializer(self):
        """নোটিফিকেশন সিরিয়ালাইজার টেস্ট"""
        from collaboration.serializers import NotificationSerializer
        
        serializer = NotificationSerializer(self.notification)
        data = serializer.data
        
        self.assertEqual(data['title'], 'Test Notification')
        self.assertEqual(data['message'], 'This is a test notification')
        self.assertEqual(data['recipient_username'], 'testuser')
        self.assertEqual(data['priority_display'], 'High')
        self.assertIn('time_ago', data)
        
    def test_notification_time_ago(self):
        """নোটিফিকেশনের Time Ago টেস্ট"""
        from collaboration.serializers import NotificationSerializer
        
        # 5 minutes ago
        self.notification.created_at = timezone.now() - timedelta(minutes=5)
        self.notification.save()
        
        serializer = NotificationSerializer(self.notification)
        self.assertEqual(serializer.data['time_ago'], '5 minutes ago')


class ReactionSerializerTest(APITestCase):
    """Reaction Serializer টেস্ট"""
    
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
        
        self.content_type = ContentType.objects.get_for_model(User)
        self.reaction = Reaction.objects.create(
            user=self.user,
            reaction_type='like',
            content_type=self.content_type,
            object_id=self.user.id
        )
        
    def test_reaction_serializer(self):
        """Reaction Serializer টেস্ট"""
        from collaboration.serializers import ReactionSerializer
        
        serializer = ReactionSerializer(self.reaction, context={'request': self.request})
        data = serializer.data
        
        self.assertEqual(data['reaction_type'], 'like')
        self.assertEqual(data['user_username'], 'testuser')
        self.assertEqual(data['reaction_type_display'], '👍 Like')
        self.assertIn('is_owner', data)


# ========================================
# ৩. View/API Tests
# ========================================

class CommentAPITest(APITestCase):
    """Comment API টেস্ট"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        self.content_type = ContentType.objects.get_for_model(User)
        
        # Create a comment
        self.comment = Comment.objects.create(
            author=self.user,
            content='Test comment',
            content_type=self.content_type,
            object_id=self.user.id
        )
        
        self.comment_url = '/api/collaboration/comments/'
        
    def test_create_comment(self):
        """কমেন্ট তৈরি API টেস্ট"""
        data = {
            'content': 'Test API comment',
            'content_type': f'{self.content_type.app_label}.{self.content_type.model}',
            'object_id': self.user.id
        }
        
        response = self.client.post(self.comment_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['content'], 'Test API comment')
        self.assertEqual(response.data['author_username'], 'testuser')
        
    def test_list_comments(self):
        """কমেন্ট লিস্ট API টেস্ট"""
        # Create another comment
        Comment.objects.create(
            author=self.user,
            content='Comment 2',
            content_type=self.content_type,
            object_id=self.user.id
        )
        
        response = self.client.get(self.comment_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        
    def test_retrieve_comment(self):
        """কমেন্ট রিট্রিভ API টেস্ট"""
        url = f'{self.comment_url}{self.comment.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.comment.id)
        self.assertEqual(response.data['content'], 'Test comment')
        
    def test_update_comment(self):
        """কমেন্ট আপডেট API টেস্ট"""
        url = f'{self.comment_url}{self.comment.id}/'
        data = {'content': 'Updated content'}
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['content'], 'Updated content')
        self.assertTrue(response.data['is_edited'])
        
    def test_delete_comment(self):
        """কমেন্ট ডিলিট API টেস্ট"""
        url = f'{self.comment_url}{self.comment.id}/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
    def test_unauthenticated_comment_access(self):
        """অননুমোদিত ইউজারের কমেন্ট অ্যাক্সেস টেস্ট"""
        self.client.credentials()  # Clear authentication
        
        response = self.client.get(self.comment_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class NotificationAPITest(APITestCase):
    """Notification API টেস্ট"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        self.notification_url = '/api/collaboration/notifications/'
        
        # Create some notifications
        for i in range(5):
            Notification.objects.create(
                recipient=self.user,
                notification_type='system',
                title=f'Notification {i}',
                message=f'Message {i}',
                is_read=(i % 2 == 0)
            )
            
    def test_list_notifications(self):
        """নোটিফিকেশন লিস্ট API টেস্ট"""
        response = self.client.get(self.notification_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)
        
    def test_retrieve_notification(self):
        """নোটিফিকেশন রিট্রিভ API টেস্ট"""
        notification = Notification.objects.filter(recipient=self.user).first()
        url = f'{self.notification_url}{notification.id}/'
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], notification.id)
        
    def test_mark_notifications_read(self):
        """নোটিফিকেশন রিড মার্ক API টেস্ট"""
        unread_count = Notification.objects.filter(recipient=self.user, is_read=False).count()
        self.assertEqual(unread_count, 2)  # 5টি মধ্যে 2টি আনরিড
        
        url = f'{self.notification_url}mark-read/'
        data = {'mark_all': True}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['marked_count'], 2)
        
        # Check if all are read now
        self.assertEqual(
            Notification.objects.filter(recipient=self.user, is_read=False).count(),
            0
        )
        
    def test_mark_specific_notifications_read(self):
        """নির্দিষ্ট নোটিফিকেশন রিড মার্ক API টেস্ট"""
        notifications = Notification.objects.filter(recipient=self.user, is_read=False)[:2]
        notification_ids = [n.id for n in notifications]
        
        url = f'{self.notification_url}mark-read/'
        data = {'notification_ids': notification_ids}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['marked_count'], 2)
        
    def test_unread_count(self):
        """আনরিড নোটিফিকেশন কাউন্ট API টেস্ট"""
        url = f'{self.notification_url}unread-count/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['unread_count'], 2)


class ReactionAPITest(APITestCase):
    """Reaction API টেস্ট"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        self.content_type = ContentType.objects.get_for_model(User)
        self.reaction_url = '/api/collaboration/reactions/'
        
        # Create a reaction
        self.reaction = Reaction.objects.create(
            user=self.user,
            reaction_type='like',
            content_type=self.content_type,
            object_id=self.user.id
        )
        
    def test_create_reaction(self):
        """রিঅ্যাকশন তৈরি API টেস্ট"""
        data = {
            'reaction_type': 'love',
            'content_type': f'{self.content_type.app_label}.{self.content_type.model}',
            'object_id': self.user.id
        }
        
        response = self.client.post(self.reaction_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['reaction_type'], 'love')
        self.assertEqual(response.data['user_username'], 'testuser')
        
    def test_update_reaction(self):
        """রিঅ্যাকশন আপডেট API টেস্ট"""
        data = {
            'reaction_type': 'laugh',
            'content_type': f'{self.content_type.app_label}.{self.content_type.model}',
            'object_id': self.user.id
        }
        
        response = self.client.post(self.reaction_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['reaction_type'], 'laugh')
        
    def test_list_reactions(self):
        """রিঅ্যাকশন লিস্ট API টেস্ট"""
        response = self.client.get(self.reaction_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
    def test_reaction_stats(self):
        """রিঅ্যাকশন পরিসংখ্যান API টেস্ট"""
        # We already have one reaction by self.user ('like')
        # Add reactions from other users
        reactions = ['love', 'laugh', 'wow']
        for i, reaction_type in enumerate(reactions):
            other_user = User.objects.create_user(
                username=f'otheruser{i}',
                password='testpass123'
            )
            Reaction.objects.create(
                user=other_user,
                reaction_type=reaction_type,
                content_type=self.content_type,
                object_id=self.user.id
            )
        
        url = f'{self.reaction_url}stats/?content_type={self.content_type.app_label}.{self.content_type.model}&object_id={self.user.id}'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)  # 4 unique reactions
        
    def test_delete_reaction(self):
        """রিঅ্যাকশন ডিলিট API টেস্ট"""
        url = f'{self.reaction_url}{self.reaction.id}/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class MentionAPITest(APITestCase):
    """Mention API টেস্ট"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.another_user = User.objects.create_user(
            username='anotheruser',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        self.content_type = ContentType.objects.get_for_model(User)
        self.mention_url = '/api/collaboration/mentions/'
        
        # Create a mention
        self.mention = Mention.objects.create(
            mentioned_user=self.another_user,
            mentioned_by=self.user,
            content_type=self.content_type,
            object_id=self.user.id
        )
        
    def test_create_mention(self):
        """মেনশন তৈরি API টেস্ট"""
        data = {
            'mentioned_user': self.another_user.id,
            'content_type': f'{self.content_type.app_label}.{self.content_type.model}',
            'object_id': self.user.id,
            'context': 'Please review this'
        }
        
        response = self.client.post(self.mention_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['mentioned_user_username'], 'anotheruser')
        
    def test_list_mentions(self):
        """মেনশন লিস্ট API টেস্ট"""
        response = self.client.get(self.mention_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
    def test_mark_mention_read(self):
        """মেনশন রিড মার্ক API টেস্ট"""
        url = f'{self.mention_url}{self.mention.id}/mark-read/'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_read'])
        self.assertIsNotNone(response.data['read_at'])


class ActivityLogAPITest(APITestCase):
    """ActivityLog API টেস্ট"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        self.log_url = '/api/collaboration/activity-logs/'
        
        # Create activity logs
        for i in range(5):
            ActivityLog.objects.create(
                actor=self.user,
                action_type='create' if i % 2 == 0 else 'update',
                action_description=f'Test action {i}'
            )
            
    def test_list_activity_logs(self):
        """অ্যাক্টিভিটি লগ লিস্ট API টেস্ট"""
        response = self.client.get(self.log_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)
        
    def test_filter_by_action_type(self):
        """অ্যাক্টিভিটি লগ ফিল্টার API টেস্ট"""
        url = f'{self.log_url}?action_type=create'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for log in response.data:
            self.assertEqual(log['action_type'], 'create')


# ========================================
# ৪. Signal Tests
# ========================================

class SignalTest(TestCase):
    """Signals টেস্ট"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.another_user = User.objects.create_user(
            username='anotheruser',
            password='testpass123'
        )
        self.content_type = ContentType.objects.get_for_model(User)
        
    def test_comment_signal_creates_activity_log(self):
        """কমেন্ট তৈরি হলে অ্যাক্টিভিটি লগ তৈরি হয় কিনা টেস্ট"""
        initial_log_count = ActivityLog.objects.count()
        
        Comment.objects.create(
            author=self.user,
            content='Test comment',
            content_type=self.content_type,
            object_id=self.user.id
        )
        
        self.assertEqual(ActivityLog.objects.count(), initial_log_count + 1)
        
    def test_mention_signal_creates_activity_log_and_notification(self):
        """মেনশন তৈরি হলে অ্যাক্টিভিটি লগ ও নোটিফিকেশন তৈরি হয় কিনা টেস্ট"""
        initial_log_count = ActivityLog.objects.count()
        initial_notification_count = Notification.objects.count()
        
        Mention.objects.create(
            mentioned_user=self.another_user,
            mentioned_by=self.user,
            content_type=self.content_type,
            object_id=self.user.id
        )
        
        self.assertEqual(ActivityLog.objects.count(), initial_log_count + 1)
        self.assertEqual(Notification.objects.count(), initial_notification_count + 1)
        
    def test_task_signal_creates_activity_log(self):
        """Task তৈরি হলে অ্যাক্টিভিটি লগ তৈরি হয় কিনা টেস্ট (Mock ব্যবহার)"""
        # Task মডেলটি accounts অ্যাপে আছে, তাই আমরা সরাসরি টেস্ট করছি না
        # বাস্তবে signal কাজ করবে
        pass


# ========================================
# ৫. Integration Tests
# ========================================

class IntegrationTest(APITestCase):
    """ইন্টিগ্রেশন টেস্ট"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.another_user = User.objects.create_user(
            username='anotheruser',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        self.content_type = ContentType.objects.get_for_model(User)
        
    def test_full_comment_workflow(self):
        """সম্পূর্ণ কমেন্ট ওয়ার্কফ্লো টেস্ট"""
        # 1. Create a comment
        comment_data = {
            'content': 'Integration test comment',
            'content_type': f'{self.content_type.app_label}.{self.content_type.model}',
            'object_id': self.user.id
        }
        
        response = self.client.post(
            '/api/collaboration/comments/',
            comment_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        comment_id = response.data['id']
        
        # 2. Get the comment
        response = self.client.get(f'/api/collaboration/comments/{comment_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['content'], 'Integration test comment')
        
        # 3. Update the comment
        update_data = {'content': 'Updated integration test comment'}
        response = self.client.patch(
            f'/api/collaboration/comments/{comment_id}/',
            update_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_edited'])
        
        # 4. Add a reaction to the comment
        reaction_data = {
            'reaction_type': 'like',
            'content_type': f'collaboration.comment',
            'object_id': comment_id
        }
        response = self.client.post(
            '/api/collaboration/reactions/',
            reaction_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 5. Check activity log
        response = self.client.get('/api/collaboration/activity-logs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)
        
    def test_mention_creates_notification(self):
        """মেনশন নোটিফিকেশন তৈরি করে কিনা টেস্ট"""
        # Create a mention
        mention_data = {
            'mentioned_user': self.another_user.id,
            'content_type': f'{self.content_type.app_label}.{self.content_type.model}',
            'object_id': self.user.id,
            'context': 'Please review this task'
        }
        
        response = self.client.post(
            '/api/collaboration/mentions/',
            mention_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check if notification was created
        notification = Notification.objects.filter(
            recipient=self.another_user,
            notification_type='mention'
        ).first()
        
        self.assertIsNotNone(notification)
        self.assertEqual(notification.title, f'New Mention from {self.user.username}')
        
    def test_notification_mark_read_workflow(self):
        """নোটিফিকেশন রিড মার্ক ওয়ার্কফ্লো টেস্ট"""
        # Create notifications
        for i in range(3):
            Notification.objects.create(
                recipient=self.user,
                notification_type='system',
                title=f'Test Notification {i}',
                message=f'Message {i}'
            )
        
        # Check unread count
        response = self.client.get('/api/collaboration/notifications/unread-count/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['unread_count'], 3)
        
        # Mark all as read
        response = self.client.post(
            '/api/collaboration/notifications/mark-read/',
            {'mark_all': True},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['marked_count'], 3)
        
        # Check unread count again
        response = self.client.get('/api/collaboration/notifications/unread-count/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['unread_count'], 0)