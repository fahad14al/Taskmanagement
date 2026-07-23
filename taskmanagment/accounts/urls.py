
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'roles', RoleViewSet)
router.register(r'permissions', PermissionViewSet)

urlpatterns = [
    # authentication views
    path('login/', CustomLoginView.as_view(), name='login'),
    
    # registration views
    path('register/', PublicRegistrationView.as_view(), name='public-register'),
    path('admin/register/', AdminRegistrationView.as_view(), name='admin-register'),
    
    # profile and user detail views
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('profile/update/', UpdateProfileView.as_view(), name='profile-update'),
    path('user/<int:user_id>/', UserDetailView.as_view(), name='user-detail'),
    
    # Role Permission
    path('', include(router.urls)),
    
    # Role based dashboard views
    path('dashboard/admin/', AdminDashboardView.as_view(), name='admin-dashboard'),
    path('dashboard/manager/', ManagerDashboardView.as_view(), name='manager-dashboard'),
    path('dashboard/teamlead/', TeamLeadDashboardView.as_view(), name='teamlead-dashboard'),
    path('dashboard/developer/', DeveloperDashboardView.as_view(), name='developer-dashboard'),
    path('dashboard/tester/', TesterDashboardView.as_view(), name='tester-dashboard'),
    path('dashboard/devops/', DevOpsDashboardView.as_view(), name='devops-dashboard'),
    
    #permission based views
    path('tasks/', TaskManagementView.as_view(), name='task-management'),
    path('projects/', ProjectManagementView.as_view(), name='project-management'),
    path('deploy/', DeploymentView.as_view(), name='deployment'),
    path('reports/', ReportsView.as_view(), name='reports'),
    path('users/manage/', UserManagementView.as_view(), name='user-management'),
]