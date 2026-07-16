from rest_framework.routers import DefaultRouter
from .views import (
    CommentViewSet, NotificationViewSet, ReactionViewSet,
    MentionViewSet, ActivityLogViewSet
)

router = DefaultRouter()
router.register(r'comments', CommentViewSet, basename='comment')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'reactions', ReactionViewSet, basename='reaction')
router.register(r'mentions', MentionViewSet, basename='mention')
router.register(r'activity-logs', ActivityLogViewSet, basename='activitylog')

urlpatterns = router.urls
