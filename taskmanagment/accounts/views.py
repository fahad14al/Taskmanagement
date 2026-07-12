
from rest_framework import generics, status, viewsets, serializers
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

# Importing models and serializers
from .models import Profile, Role, Permission
from .serializers import (
    UserRegistrationSerializer, 
    UserProfileSerializer, 
    RoleSerializer, 
    PermissionSerializer,
    LoginRequestSerializer,
    LoginResponseSerializer
)
from drf_spectacular.utils import extend_schema, inline_serializer


from .permissions import (
    IsAdmin, 
    IsManager, 
    IsTeamLead, 
    IsDeveloper, 
    IsTester, 
    IsDevOps, 
    has_permission,
    IsAdminOrManager,
    IsAdminOrTeamLead,
    IsManagerOrTeamLead,
    IsOwner
)

# User Registration Views

@method_decorator(csrf_exempt, name='dispatch')
class PublicRegistrationView(generics.CreateAPIView):
    """
    Registration for permitted users (admin/manager) where users get default Role: 'developer'
    """
    serializer_class = UserRegistrationSerializer
    permission_classes = [IsAuthenticated, IsAdminOrManager] 

    def perform_create(self, serializer):
        user = serializer.save()
        # set default Role 
        try:
            developer_role = Role.objects.get(name='developer')
            user.profile.role = developer_role
            user.profile.save()
        except Role.DoesNotExist:
            # if role doesn't exist, just pass or handle it as needed
            pass
        return user

@method_decorator(csrf_exempt, name='dispatch')
class AdminRegistrationView(generics.CreateAPIView):
    """
    Registration for Admin and Manager users to create new users and manually set Roles and Permissions
    """
    serializer_class = UserRegistrationSerializer
    permission_classes = [IsAuthenticated, IsAdminOrManager]  

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "message": "User created successfully",
                "user": UserProfileSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# user login view

@method_decorator(csrf_exempt, name='dispatch')
class CustomLoginView(APIView):
    """
    Logs in a user with a username and password and provides a token
    """
    permission_classes = [AllowAny]

    @extend_schema(
        request=LoginRequestSerializer,
        responses={
            200: LoginResponseSerializer,
            400: inline_serializer(
                name='LoginErrorResponse',
                fields={
                    'error': serializers.CharField()
                }
            )
        },
        description="Logs in a user with a username and password and provides a token"
    )
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(username=username, password=password)
        if user:
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user_id': user.pk,
                'username': user.username,
                'email': user.email,
                'role': user.profile.role.name if user.profile.role else None,
                'permissions': list(user.profile.permissions.values_list('name', flat=True))
            })
        return Response({'error': 'Invalid username or password'}, status=400)

# user profile view and update view

class UserProfileView(APIView):
    """
    নিজের প্রোফাইল দেখা
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

class UpdateProfileView(APIView):
    """
    নিজের প্রোফাইল আপডেট করা (শুধু মালিক)
    """
    permission_classes = [IsAuthenticated, IsOwner]  # ← এখানে IsOwner ব্যবহার

    def put(self, request):
        user = request.user
        serializer = UserProfileSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

# Role and Permission Management Views only Admin

class RoleViewSet(viewsets.ModelViewSet):
    """
    Role management - only Admin
    """
    queryset = Role.objects.all().order_by('id')
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated, IsAdmin]  # ← এখানে IsAdmin ব্যবহার

class PermissionViewSet(viewsets.ModelViewSet):
    """
    Permission management - only Admin
    """
    queryset = Permission.objects.all().order_by('id')
    serializer_class = PermissionSerializer
    permission_classes = [IsAuthenticated, IsAdmin]  # ← এখানে IsAdmin ব্যবহার

# Role and Permission Management Views only Admin

class AdminDashboardView(APIView):
    """
    only Admin's dashboard
    """
    permission_classes = [IsAuthenticated, IsAdmin]  # ← এখানে IsAdmin ব্যবহার

    def get(self, request):
        return Response({
            "message": "Welcome to Admin Dashboard",
            "your_role": request.user.profile.role.name,
            "total_users": User.objects.count(),
            "total_roles": Role.objects.count(),
            "permissions": list(request.user.profile.permissions.values_list('name', flat=True))
        })

class ManagerDashboardView(APIView):
    """
    only Manager's dashboard
    """
    permission_classes = [IsAuthenticated, IsManager]  # ← এখানে IsManager ব্যবহার

    def get(self, request):
        return Response({
            "message": "Welcome to Manager Dashboard",
            "your_role": request.user.profile.role.name,
            "team_members": User.objects.filter(profile__role__name='developer').count(),
            "permissions": list(request.user.profile.permissions.values_list('name', flat=True))
        })

class TeamLeadDashboardView(APIView):
    """
    Team Lead and higher-level Role's dashboard
    """
    permission_classes = [IsAuthenticated, IsTeamLead | IsManager | IsAdmin]  # ← combined

    def get(self, request):
        return Response({
            "message": "Welcome to Team Lead Dashboard",
            "your_role": request.user.profile.role.name,
            "team_size": 5,  
            "permissions": list(request.user.profile.permissions.values_list('name', flat=True))
        })

class DeveloperDashboardView(APIView):
    """
    only Developer's dashboard
    """
    permission_classes = [IsAuthenticated, IsDeveloper]  # ← এখানে IsDeveloper ব্যবহার

    def get(self, request):
        return Response({
            "message": "Welcome to Developer Dashboard",
            "your_role": request.user.profile.role.name,
            "assigned_tasks": 3,  # উদাহরণ
            "permissions": list(request.user.profile.permissions.values_list('name', flat=True))
        })

class TesterDashboardView(APIView):
    """
    only Tester's dashboard
    """
    permission_classes = [IsAuthenticated, IsTester]  # ← এখানে IsTester ব্যবহার

    def get(self, request):
        return Response({
            "message": "Welcome to Tester Dashboard",
            "your_role": request.user.profile.role.name,
            "test_cases": 10,  
            "permissions": list(request.user.profile.permissions.values_list('name', flat=True))
        })

class DevOpsDashboardView(APIView):
    """
    only DevOps's dashboard
    """
    permission_classes = [IsAuthenticated, IsDevOps]  # ← এখানে IsDevOps ব্যবহার

    def get(self, request):
        return Response({
            "message": "Welcome to DevOps Dashboard",
            "your_role": request.user.profile.role.name,
            "servers": 3,  
            "permissions": list(request.user.profile.permissions.values_list('name', flat=True))
        })

# permission-based views for specific actions

class TaskManagementView(APIView):
    """
    the 'can_manage_tasks' permission is required for these users
    """
    permission_classes = [IsAuthenticated, has_permission('can_manage_tasks')]  # ← এখানে has_permission ব্যবহার

    def get(self, request):
        return Response({
            "message": "Task Management Dashboard",
            "your_role": request.user.profile.role.name if request.user.profile.role else None,
            "your_permissions": list(request.user.profile.permissions.values_list('name', flat=True))
        })

class ProjectManagementView(APIView):
    """
    the 'can_manage_projects' permission is required for these users
    """
    permission_classes = [IsAuthenticated, has_permission('can_manage_projects')]

    def get(self, request):
        return Response({
            "message": "Project Management Dashboard",
            "your_role": request.user.profile.role.name if request.user.profile.role else None
        })

class DeploymentView(APIView):
    """
    DevOps and Admin users only
    """
    permission_classes = [IsAuthenticated, (IsDevOps | IsAdmin)]  # ← combined

    def get(self, request):
        return Response({
            "message": "Deployment Dashboard",
            "your_role": request.user.profile.role.name,
            "can_deploy": request.user.profile.has_permission('can_deploy')
        })

class ReportsView(APIView):
    """
    the 'can_view_reports' permission is required for these users
    """
    permission_classes = [IsAuthenticated, has_permission('can_view_reports')]

    def get(self, request):
        return Response({
            "message": "Reports Dashboard",
            "your_role": request.user.profile.role.name if request.user.profile.role else None,
            "reports": ["Report 1", "Report 2", "Report 3"]
        })

class UserManagementView(APIView):
    """
    Admin and Manager users only (those with the 'can_manage_users' permission)
    """
    permission_classes = [IsAuthenticated, IsAdminOrManager]  

    def get(self, request):
        users = User.objects.all().values('id', 'username', 'email', 'profile__role__name')
        return Response({
            "message": "User Management",
            "users": list(users)
        })

# obj level permission view for user profile update (only owner or admin can update)

class UserDetailView(APIView):
    """
    anyone can view, but only the owner or admin can edit
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        serializer = UserProfileSerializer(user)
        return Response(serializer.data)

    def put(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        # check if the user is the owner or an admin
        is_admin = request.user.profile.role and request.user.profile.role.name == 'admin'
        if request.user.id != user.id and not is_admin:
            return Response(
                {"error": "You are not the owner of this user profile or an admin"},
                status=403
            )
        serializer = UserProfileSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)