
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
    profile = ProfileSerializer(required=False)  # Profile ডেটা নেওয়ার জন্য

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'profile']

    def create(self, validated_data):
        profile_data = validated_data.pop('profile', {})
        
        # UserCreation
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
        
        # Profile creat or update 
        profile = user.profile  
        
        # Role setting
        if 'role' in profile_data and profile_data['role']:
            profile.role = profile_data['role']
        
        # extract permission IDs and set them
        if 'permissions' in profile_data:
            profile.permissions.set(profile_data['permissions'])
        
        # other profile fields
        if 'phone' in profile_data:
            profile.phone = profile_data.get('phone', '')
        if 'address' in profile_data:
            profile.address = profile_data.get('address', '')
        
        profile.save()
        return user

    def to_representation(self, instance):
        """রেসপন্সে Profile ডেটা দেখানোর জন্য"""
        data = super().to_representation(instance)
        data['profile'] = ProfileSerializer(instance.profile).data
        return data

# user profile serializer for viewing user details along with profile
class UserProfileSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'profile']


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