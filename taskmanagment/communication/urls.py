from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChatRoomViewSet, MessageViewSet, PresenceViewSet

router = DefaultRouter()
router.register(r'rooms', ChatRoomViewSet, basename='chatroom')
router.register(r'messages', MessageViewSet, basename='message')
router.register(r'presence', PresenceViewSet, basename='presence')

app_name = 'communication'

urlpatterns = [
    path('', include(router.urls)),
]
