# accounts/models.py
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# Role and Permission models for user management and access control
class Role(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('team_lead', 'Team Lead'),
        ('developer', 'Developer'),
        ('tester', 'Tester'),
        ('devops', 'DevOps'),
    ]
    name = models.CharField(max_length=20, choices=ROLE_CHOICES, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.get_name_display()

class Permission(models.Model):
    PERMISSION_CHOICES = [
        ('can_view_dashboard', 'Dashboard '),
        ('can_manage_users', 'Manage Users'),
        ('can_manage_projects', 'Manage Projects'),
        ('can_manage_tasks', 'Manage Tasks'),
        ('can_manage_roles', 'Manage Roles'),
        ('can_view_reports', 'View Reports'),
        ('can_delete_data', 'Delete Data'),
        ('can_deploy', 'Deploy'),
        ('can_access_server', 'Access Server'),
        ('can_view_logs', 'View Logs'),
    ]
    name = models.CharField(max_length=50, choices=PERMISSION_CHOICES, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.get_name_display()

class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('role', 'permission')

    def __str__(self):
        return f"{self.role} - {self.permission}"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    permissions = models.ManyToManyField(Permission, blank=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def has_permission(self, perm_name):
        """check if the user has a specific permission either directly or through their role"""
        if self.role:
            role_permissions = RolePermission.objects.filter(role=self.role, permission__name=perm_name)
            if role_permissions.exists():
                return True
        return self.permissions.filter(name=perm_name).exists()

#Signal: Create Profile when new User is created (as before)
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()