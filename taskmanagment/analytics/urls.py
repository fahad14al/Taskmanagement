from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DashboardViewSet, ReportViewSet, StatisticsViewSet, ServicesViewSet

router = DefaultRouter()
router.register(r'dashboard', DashboardViewSet, basename='dashboard')
router.register(r'reports', ReportViewSet, basename='report')
router.register(r'statistics', StatisticsViewSet, basename='statistics')
router.register(r'services', ServicesViewSet, basename='service')

app_name = 'analytics'

urlpatterns = [
    path('', include(router.urls)),
]
