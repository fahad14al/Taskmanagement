# accounts/permissions.py
from rest_framework.permissions import BasePermission


# Role wise Permissions

class IsAdmin(BasePermission):
    """only for Admin users"""
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.profile.role and 
            request.user.profile.role.name == 'admin'
        )

class IsManager(BasePermission):
    """only for Manager users"""
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.profile.role and 
            request.user.profile.role.name == 'manager'
        )

class IsTeamLead(BasePermission):
    """only for Team Lead users"""
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.profile.role and 
            request.user.profile.role.name == 'team_lead'
        )

class IsDeveloper(BasePermission):
    """only for Developer users"""
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.profile.role and 
            request.user.profile.role.name == 'developer'
        )

class IsTester(BasePermission):
    """only for Tester users"""
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.profile.role and 
            request.user.profile.role.name == 'tester'
        )

class IsDevOps(BasePermission):
    """only for DevOps users"""
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.profile.role and 
            request.user.profile.role.name == 'devops'
        )

#combination of roles

class IsAdminOrManager(BasePermission):
    """only for Admin or Manager users"""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if not request.user.profile.role:
            return False
        return request.user.profile.role.name in ['admin', 'manager']

class IsAdminOrTeamLead(BasePermission):
    """only for Admin or Team Lead users"""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if not request.user.profile.role:
            return False
        return request.user.profile.role.name in ['admin', 'team_lead']

class IsManagerOrTeamLead(BasePermission):
    """only for Manager or Team Lead users"""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if not request.user.profile.role:
            return False
        return request.user.profile.role.name in ['manager', 'team_lead']

# permission based permissions

class HasPermission(BasePermission):
    """only checks if the user has a specific permission"""
    def __init__(self, permission_name):
        self.permission_name = permission_name

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.profile.has_permission(self.permission_name)

#function based permission decorator

def has_permission(permission_name):
    """
    Decorator to check if the user has a specific permission.
    Usage:
    permission_classes = [has_permission('can_manage_tasks')]
    """
    class PermissionChecker(BasePermission):
        def has_permission(self, request, view):
            if not request.user or not request.user.is_authenticated:
                return False
            return request.user.profile.has_permission(permission_name)
    return PermissionChecker

#object level permissions

class IsOwner(BasePermission):
    """
    Checks if the user is the owner of the object
    (e.g., can only edit their own profile)
    """
    def has_object_permission(self, request, view, obj):
        # obj and User instance 
        if hasattr(obj, 'user'):
            return obj.user == request.user
        # if obj is not a User instance
        return obj == request.user

class IsAdminOrOwner(BasePermission):
    """
    Checks if the user is either an admin or the owner of the object
    """
    def has_object_permission(self, request, view, obj):
        if request.user.profile.role.name == 'admin':
            return True
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return obj == request.user

# 6. Dynamic Permission (Custom Logic)


class DynamicPermission(BasePermission):
    """
    Checks permissions dynamically
    
    usage:
    permission_classes = [DynamicPermission('can_manage_projects')]
    """
    def __init__(self, permission_name=None):
        self.permission_name = permission_name

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # if a permission name is provided
        if self.permission_name:
            return request.user.profile.has_permission(self.permission_name)
        
        # otherwise check the view's required_permission attribute
        if hasattr(view, 'required_permission'):
            return request.user.profile.has_permission(view.required_permission)
        
        return False