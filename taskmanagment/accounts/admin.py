# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import Profile, Role, Permission, RolePermission

# role and permission management in admin panel

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'get_name_display', 'description', 'created_at']
    list_filter = ['name']
    search_fields = ['name', 'description']
    ordering = ['name']
    
    def get_name_display(self, obj):
        return obj.get_name_display()  
    get_name_display.short_description = 'Role Name Display'

# Permission model admin

@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'get_name_display', 'description']
    list_filter = ['name']
    search_fields = ['name', 'description']
    ordering = ['name']
    
    def get_name_display(self, obj):
        return obj.get_name_display()
    get_name_display.short_description = 'Permission Display'


# RolePermission only for admin users


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ['id', 'role', 'permission']
    list_filter = ['role', 'permission']
    search_fields = ['role__name', 'permission__name']
    ordering = ['role', 'permission']

# profile model admin with inline in user admin

class ProfileInline(admin.StackedInline):
    """
    User admin page Profile view Inline
    """
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'
    fields = ['role', 'permissions', 'phone', 'address', 'profile_picture']
    filter_horizontal = ['permissions']  #for many-to-many field permissions, use horizontal filter

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'role', 'phone', 'created_at']
    list_filter = ['role', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone']
    raw_id_fields = ['user']  # Search box
    filter_horizontal = ['permissions']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

# user admin customization to include profile inline and role display

class CustomUserAdmin(UserAdmin):
    """
    default UserAdmin adding customisely Profile Inline
    """
    inlines = [ProfileInline] # Profile Inline 
    list_display = ['id', 'username', 'email', 'first_name', 'last_name', 
                   'is_staff', 'is_active', 'get_role']
    list_filter = ['is_staff', 'is_active', 'profile__role'] # Role 
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    
    def get_role(self, obj):
        """view the role of the user in the list display"""
        if hasattr(obj, 'profile') and obj.profile.role:
            return obj.profile.role.get_name_display()
        return '-'
    get_role.short_description = 'Role'
    
    def get_inline_instances(self, request, obj=None):
        """view the inline instances for the user in the admin panel"""
        if not obj:
            return []
        return super().get_inline_instances(request, obj)

# user model unregister and register with custom user admin
admin.site.unregister(User)  # previously registered User model unregister
admin.site.register(User, CustomUserAdmin)  # custom user admin register

# == Admin site header customization(optional)

admin.site.site_header = "My Project Admin Panel"
admin.site.site_title = "My Project Admin"
admin.site.index_title = "Welcome to My Project Admin Panel"