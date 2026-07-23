
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile, Role, Permission

#Role and Permission Serializer
class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name', 'description']

class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['id', 'name', 'description']

#Profile Serializer
class ProfileSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only=True)
    role_id = serializers.PrimaryKeyRelatedField(
        source='role', queryset=Role.objects.all(), write_only=True, required=False
    )
    permissions = PermissionSerializer(many=True, read_only=True)
    permission_ids = serializers.PrimaryKeyRelatedField(
        source='permissions', queryset=Permission.objects.all(), 
        many=True, write_only=True, required=False
    )

    class Meta:
        model = Profile
        fields = ['phone', 'address', 'profile_picture', 'role', 'role_id', 
                 'permissions', 'permission_ids']

# User Registration Serializer
class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    profile = ProfileSerializer(required=False) # Profile 

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'profile']

    def create(self, validated_data):
        profile_data = validated_data.pop('profile', None) or {}

        # UserCreation
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )

        # Profile create or update
        profile = user.profile

        # Role setting
        if isinstance(profile_data, dict):
            if profile_data.get('role'):
                profile.role = profile_data['role']

            # extract permission IDs and set them
            permissions = profile_data.get('permissions')
            if permissions:
                profile.permissions.set(permissions)

            # other profile fields
            if profile_data.get('phone') is not None:
                profile.phone = profile_data.get('phone', '')
            if profile_data.get('address') is not None:
                profile.address = profile_data.get('address', '')

        profile.save()
        return user

    def to_representation(self, instance):
        """ Profile """
        data = super().to_representation(instance)
        data['profile'] = ProfileSerializer(instance.profile).data
        return data

# user profile serializer for viewing user details along with profile
class UserProfileSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'profile']

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', None)
        
        # Update User fields
        instance.username = validated_data.get('username', instance.username)
        instance.email = validated_data.get('email', instance.email)
        instance.save()
        
        # Update Profile fields
        if profile_data is not None:
            profile = instance.profile
            if 'phone' in profile_data:
                profile.phone = profile_data.get('phone', profile.phone)
            if 'address' in profile_data:
                profile.address = profile_data.get('address', profile.address)
            if 'role' in profile_data:
                profile.role = profile_data.get('role', profile.role)
            if 'permissions' in profile_data:
                profile.permissions.set(profile_data.get('permissions', []))
            profile.save()
            
        return instance


# Serializer for login request
class LoginRequestSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )


# Serializer for login response
class LoginResponseSerializer(serializers.Serializer):
    token = serializers.CharField()
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField()
    role = serializers.CharField(allow_null=True)
    permissions = serializers.ListField(child=serializers.CharField())
