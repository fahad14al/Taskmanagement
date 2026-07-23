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
# . Model Tests
# ========================================

class CommentModelTest(TestCase):
    """Comment """
    
    def setUp(self):
        """ """
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.another_user = User.objects.create_user(
            username='anotheruser',
            password='testpass123'
        )
        
        # Task (ContentType )
        from django.contrib.contenttypes.models import ContentType
        self.content_type = ContentType.objects.get_for_model(User)
        self.object_id = self.user.id
        
    def test_create_comment(self):
        """ """
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
        """ """
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
        """ """
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
        """ """
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
        """is_owner """
        comment = Comment.objects.create(
            author=self.user,
            content='Test comment',
            content_type=self.content_type,
            object_id=self.object_id
        )
        
        self.assertTrue(comment.is_owner(self.user))
        self.assertFalse(comment.is_owner(self.another_user))
        
    def test_comment_str_method(self):
        """__str__ """
        comment = Comment.objects.create(
            author=self.user,
            content='Test comment',
            content_type=self.content_type,
            object_id=self.object_id
        )
        
        expected_str = f"Comment by {self.user.username} on {comment.created_at}"
        self.assertEqual(str(comment), expected_str)


class MentionModelTest(TestCase):
    """Mention """
    
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
        """ """
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
        """ """
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
        """__str__ """
        mention = Mention.objects.create(
            mentioned_user=self.user2,
            mentioned_by=self.user1,
            content_type=self.content_type,
            object_id=self.object_id
        )
        
        expected_str = f"{self.user1} mentioned {self.user2}"
        self.assertEqual(str(mention), expected_str)


class NotificationModelTest(TestCase):
    """Notification """
    
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
        """ """
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
        """ """
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
        """ """
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
        """__str__ """
        notification = Notification.objects.create(
            recipient=self.user,
            notification_type='system',
            title='Test Notification',
            message='Test message'
        )
        
        expected_str = f"Test Notification - {self.user.username}"
        self.assertEqual(str(notification), expected_str)


class ActivityLogModelTest(TestCase):
    """ActivityLog """
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.content_type = ContentType.objects.get_for_model(User)
        self.object_id = self.user.id
        
    def test_create_activity_log(self):
        """ """
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
        """ Changes JSON """
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
        """__str__ """
        log = ActivityLog.objects.create(
            actor=self.user,
            action_type='create',
            action_description='Created a new task'
        )
        
        expected_str = f"{self.user} - create at {log.created_at}"
        self.assertEqual(str(log), expected_str)


class ReactionModelTest(TestCase):
    """Reaction """
    
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
        """ """
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
        """User can react once per object """
        Reaction.objects.create(
            user=self.user,
            reaction_type='like',
            content_type=self.content_type,
            object_id=self.object_id
        )
        
        # 
        with self.assertRaises(Exception):
            Reaction.objects.create(
                user=self.user,
                reaction_type='love',
                content_type=self.content_type,
                object_id=self.object_id
            )
            
    def test_reaction_str_method(self):
        """__str__ """
        reaction = Reaction.objects.create(
            user=self.user,
            reaction_type='like',
            content_type=self.content_type,
            object_id=self.object_id
        )
        
        expected_str = f"{self.user} reacted like"
        self.assertEqual(str(reaction), expected_str)


# ========================================
# . Serializer Tests
# ========================================

class CommentSerializerTest(APITestCase):
    """Comment Serializer """
    
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
        """ """
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
        """Invalid Content Type """
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
        """Comment Serializer """
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
    """Notification Serializer """
    
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
        """ """
        from collaboration.serializers import NotificationSerializer
        
        serializer = NotificationSerializer(self.notification)
        data = serializer.data
        
        self.assertEqual(data['title'], 'Test Notification')
        self.assertEqual(data['message'], 'This is a test notification')
        self.assertEqual(data['recipient_username'], 'testuser')
        self.assertEqual(data['priority_display'], 'High')
        self.assertIn('time_ago', data)
        
    def test_notification_time_ago(self):
        """ Time Ago """
        from collaboration.serializers import NotificationSerializer
        
        # 5 minutes ago
        self.notification.created_at = timezone.now() - timedelta(minutes=5)
        self.notification.save()
        
        serializer = NotificationSerializer(self.notification)
        self.assertEqual(serializer.data['time_ago'], '5 minutes ago')


class ReactionSerializerTest(APITestCase):
    """Reaction Serializer """
    
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
        """Reaction Serializer """
        from collaboration.serializers import ReactionSerializer
        
        serializer = ReactionSerializer(self.reaction, context={'request': self.request})
        data = serializer.data
        
        self.assertEqual(data['reaction_type'], 'like')
        self.assertEqual(data['user_username'], 'testuser')
        self.assertEqual(data['reaction_type_display'], 'Like')
        self.assertIn('is_owner', data)


# ========================================
# . View/API Tests
# ========================================

class CommentAPITest(APITestCase):
    """Comment API """
    
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
        """ API """
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
        """ API """
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
        """ API """
        url = f'{self.comment_url}{self.comment.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.comment.id)
        self.assertEqual(response.data['content'], 'Test comment')
        
    def test_update_comment(self):
        """ API """
        url = f'{self.comment_url}{self.comment.id}/'
        data = {'content': 'Updated content'}
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['content'], 'Updated content')
        self.assertTrue(response.data['is_edited'])
        
    def test_delete_comment(self):
        """ API """
        url = f'{self.comment_url}{self.comment.id}/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
    def test_unauthenticated_comment_access(self):
        """ """
        self.client.credentials()  # Clear authentication
        
        response = self.client.get(self.comment_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class NotificationAPITest(APITestCase):
    """Notification API """
    
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
        """ API """
        response = self.client.get(self.notification_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)
        
    def test_retrieve_notification(self):
        """ API """
        notification = Notification.objects.filter(recipient=self.user).first()
        url = f'{self.notification_url}{notification.id}/'
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], notification.id)
        
    def test_mark_notifications_read(self):
        """ API """
        unread_count = Notification.objects.filter(recipient=self.user, is_read=False).count()
        self.assertEqual(unread_count, 2) # 5 2 
        
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
        """ API """
        notifications = Notification.objects.filter(recipient=self.user, is_read=False)[:2]
        notification_ids = [n.id for n in notifications]
        
        url = f'{self.notification_url}mark-read/'
        data = {'notification_ids': notification_ids}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['marked_count'], 2)
        
    def test_unread_count(self):
        """ API """
        url = f'{self.notification_url}unread-count/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['unread_count'], 2)


class ReactionAPITest(APITestCase):
    """Reaction API """
    
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
        """ API """
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
        """ API """
        data = {
            'reaction_type': 'laugh',
            'content_type': f'{self.content_type.app_label}.{self.content_type.model}',
            'object_id': self.user.id
        }
        
        response = self.client.post(self.reaction_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['reaction_type'], 'laugh')
        
    def test_list_reactions(self):
        """ API """
        response = self.client.get(self.reaction_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
    def test_reaction_stats(self):
        """ API """
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
        """ API """
        url = f'{self.reaction_url}{self.reaction.id}/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class MentionAPITest(APITestCase):
    """Mention API """
    
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
        """ API """
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
        """ API """
        response = self.client.get(self.mention_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
    def test_mark_mention_read(self):
        """ API """
        url = f'{self.mention_url}{self.mention.id}/mark-read/'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_read'])
        self.assertIsNotNone(response.data['read_at'])


class ActivityLogAPITest(APITestCase):
    """ActivityLog API """
    
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
        """ API """
        response = self.client.get(self.log_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)
        
    def test_filter_by_action_type(self):
        """ API """
        url = f'{self.log_url}?action_type=create'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for log in response.data:
            self.assertEqual(log['action_type'], 'create')


# ========================================
# . Signal Tests
# ========================================

class SignalTest(TestCase):
    """Signals """
    
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
        """ """
        initial_log_count = ActivityLog.objects.count()
        
        Comment.objects.create(
            author=self.user,
            content='Test comment',
            content_type=self.content_type,
            object_id=self.user.id
        )
        
        self.assertEqual(ActivityLog.objects.count(), initial_log_count + 1)
        
    def test_mention_signal_creates_activity_log_and_notification(self):
        """Activity log and notification on mention creation """
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
        """Task (Mock )"""
        # Task accounts , 
        # signal 
        pass


# ========================================
# . Integration Tests
# ========================================

class IntegrationTest(APITestCase):
    """ """
    
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
        """ """
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
        """ """
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
        """ """
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