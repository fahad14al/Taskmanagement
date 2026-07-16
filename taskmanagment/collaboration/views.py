from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db import models

from .models import Comment, Mention, Notification, ActivityLog, Reaction
from .serializers import (
	CommentSerializer, CommentCreateSerializer, CommentUpdateSerializer,
	MentionSerializer, MentionCreateSerializer,
	NotificationSerializer, NotificationCreateSerializer, NotificationMarkReadSerializer,
	ActivityLogSerializer,
	ReactionSerializer, ReactionCreateSerializer
)


class CommentViewSet(viewsets.ModelViewSet):
	permission_classes = [IsAuthenticated]
	queryset = Comment.objects.filter(is_deleted=False).order_by('-created_at')
	pagination_class = None

	def get_serializer_class(self):
		if self.action == 'create':
			return CommentCreateSerializer
		if self.action in ('update', 'partial_update'):
			return CommentUpdateSerializer
		return CommentSerializer

	def destroy(self, request, *args, **kwargs):
		instance = self.get_object()
		instance.is_deleted = True
		instance.save()
		return Response(status=status.HTTP_204_NO_CONTENT)

	def get_queryset(self):
		# Only return comments relevant to the authenticated user (their own)
		user = getattr(self.request, 'user', None)
		qs = Comment.objects.filter(is_deleted=False).order_by('-created_at')
		if user and user.is_authenticated:
			return qs.filter(author=user)
		return qs.none()

	def create(self, request, *args, **kwargs):
		serializer = self.get_serializer(data=request.data, context={'request': request})
		serializer.is_valid(raise_exception=True)
		comment = serializer.save()
		out = CommentSerializer(comment, context={'request': request})
		return Response(out.data, status=status.HTTP_201_CREATED)

	def partial_update(self, request, *args, **kwargs):
		instance = self.get_object()
		serializer = self.get_serializer(instance, data=request.data, partial=True, context={'request': request})
		serializer.is_valid(raise_exception=True)
		serializer.save()
		out = CommentSerializer(instance, context={'request': request})
		return Response(out.data)


class NotificationViewSet(viewsets.ModelViewSet):
	permission_classes = [IsAuthenticated]
	serializer_class = NotificationSerializer
	pagination_class = None

	def get_queryset(self):
		return Notification.objects.filter(recipient=self.request.user).order_by('-created_at')

	def get_serializer_class(self):
		if self.action == 'create':
			return NotificationCreateSerializer
		return NotificationSerializer

	@action(detail=False, methods=['post'], url_path='mark-read')
	def mark_read(self, request):
		serializer = NotificationMarkReadSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		data = serializer.validated_data
		qs = Notification.objects.filter(recipient=request.user, is_read=False)
		if data.get('notification_ids'):
			qs = qs.filter(id__in=data['notification_ids'])
		marked = qs.update(is_read=True, read_at=timezone.now())
		return Response({'marked_count': marked})

	@action(detail=False, methods=['get'], url_path='unread-count')
	def unread_count(self, request):
		count = Notification.objects.filter(recipient=request.user, is_read=False).count()
		return Response({'unread_count': count})


class ReactionViewSet(viewsets.ModelViewSet):
	permission_classes = [IsAuthenticated]
	queryset = Reaction.objects.all()
	pagination_class = None

	def get_serializer_class(self):
		if self.action == 'create':
			return ReactionCreateSerializer
		return ReactionSerializer

	@action(detail=False, methods=['get'], url_path='stats')
	def stats(self, request):
		content_type = request.query_params.get('content_type')
		object_id = request.query_params.get('object_id')
		if not content_type or not object_id:
			return Response([], status=status.HTTP_200_OK)
		# Simple aggregation
		from django.contrib.contenttypes.models import ContentType
		try:
			app_label, model = content_type.split('.', 1)
			ct = ContentType.objects.get(app_label=app_label, model=model)
		except Exception:
			return Response([], status=status.HTTP_200_OK)
		reactions = Reaction.objects.filter(content_type=ct, object_id=object_id)
		stats = {}
		for r in reactions:
			stats.setdefault(r.reaction_type, {'reaction_type': r.reaction_type, 'reaction_type_display': r.get_reaction_type_display(), 'count': 0, 'users': []})
			stats[r.reaction_type]['count'] += 1
			stats[r.reaction_type]['users'].append(r.user.username)
		return Response(list(stats.values()), status=status.HTTP_200_OK)

	def get_queryset(self):
		user = getattr(self.request, 'user', None)
		qs = Reaction.objects.all().order_by('-created_at')
		if user and user.is_authenticated:
			return qs.filter(user=user)
		return qs.none()

	def create(self, request, *args, **kwargs):
		serializer = self.get_serializer(data=request.data, context={'request': request})
		serializer.is_valid(raise_exception=True)
		reaction = serializer.save()
		out = ReactionSerializer(reaction, context={'request': request})
		return Response(out.data, status=status.HTTP_201_CREATED)


class MentionViewSet(viewsets.ModelViewSet):
	permission_classes = [IsAuthenticated]
	queryset = Mention.objects.all().order_by('-created_at')
	pagination_class = None

	def get_serializer_class(self):
		if self.action == 'create':
			return MentionCreateSerializer
		return MentionSerializer

	@action(detail=True, methods=['post'], url_path='mark-read')
	def mark_read(self, request, pk=None):
		mention = self.get_object()
		mention.mark_as_read()
		return Response(MentionSerializer(mention).data)

	def get_queryset(self):
		user = getattr(self.request, 'user', None)
		qs = Mention.objects.all().order_by('-created_at')
		if user and user.is_authenticated:
			return qs.filter(models.Q(mentioned_user=user) | models.Q(mentioned_by=user))
		return qs.none()

	def create(self, request, *args, **kwargs):
		serializer = self.get_serializer(data=request.data, context={'request': request})
		serializer.is_valid(raise_exception=True)
		mention = serializer.save()
		out = MentionSerializer(mention, context={'request': request})
		return Response(out.data, status=status.HTTP_201_CREATED)


class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
	permission_classes = [IsAuthenticated]
	serializer_class = ActivityLogSerializer
	pagination_class = None

	def get_queryset(self):
		user = getattr(self.request, 'user', None)
		qs = ActivityLog.objects.all().order_by('-created_at')
		if user and user.is_authenticated:
			qs = qs.filter(actor=user)
		action_type = self.request.query_params.get('action_type')
		if action_type:
			qs = qs.filter(action_type=action_type)
		return qs

	# list uses default behaviour; pagination disabled above so tests receive lists

