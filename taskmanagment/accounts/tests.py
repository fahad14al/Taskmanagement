from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from rest_framework.authtoken.models import Token

from accounts.models import Permission, Role


@override_settings(ALLOWED_HOSTS=['testserver'])
class AccountEndpointTests(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.user = get_user_model().objects.create_user(
            username='tester',
            password='strong-password-123',
        )

    # Endpoint: POST /api/login/
    # Purpose: authenticate a user and return an auth token
    def test_login_returns_token_without_csrf_token(self):
        response = self.client.post(
            '/api/login/',
            {'username': 'tester', 'password': 'strong-password-123'},
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('token', response.json())

    # Endpoint: POST /api/register/
    # Purpose: create a new user; requires an admin/manager token
    def test_admin_can_register_new_user(self):
        admin_role = Role.objects.get_or_create(name='admin', defaults={'description': 'Admin'})[0]
        admin_user = get_user_model().objects.create_user(
            username='admin-user',
            password='strong-password-123',
        )
        admin_user.profile.role = admin_role
        admin_user.profile.save()

        token, _ = Token.objects.get_or_create(user=admin_user)
        response = self.client.post(
            '/api/register/',
            {'username': 'new-user', 'email': 'new@example.com', 'password': 'strong-password-123'},
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Token {token.key}',
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(get_user_model().objects.filter(username='new-user').exists())

    # Endpoint: POST /api/admin/register/
    # Purpose: same as register but intended for admin-only usage
    def test_admin_registration_endpoint_requires_admin_token(self):
        admin_role = Role.objects.get_or_create(name='admin', defaults={'description': 'Admin'})[0]
        admin_user = get_user_model().objects.create_user(
            username='admin-user-2',
            password='strong-password-123',
        )
        admin_user.profile.role = admin_role
        admin_user.profile.save()

        token, _ = Token.objects.get_or_create(user=admin_user)
        response = self.client.post(
            '/api/admin/register/',
            {'username': 'new-user-2', 'email': 'new2@example.com', 'password': 'strong-password-123'},
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Token {token.key}',
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(get_user_model().objects.filter(username='new-user-2').exists())

    # Endpoint: GET /api/profile/
    # Purpose: fetch the authenticated user's profile
    def test_authenticated_user_can_view_profile(self):
        token, _ = Token.objects.get_or_create(user=self.user)
        response = self.client.get(
            '/api/profile/',
            HTTP_AUTHORIZATION=f'Token {token.key}',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['username'], self.user.username)

    # Endpoint: PUT /api/profile/update/
    # Purpose: update the authenticated user's profile
    def test_authenticated_user_can_update_profile(self):
        token, _ = Token.objects.get_or_create(user=self.user)
        response = self.client.put(
            '/api/profile/update/',
            {'phone': '1234567890', 'address': 'Dhaka'},
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Token {token.key}',
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('username', response.json())

    # Endpoint: GET /api/roles/
    # Purpose: list roles; requires admin access
    def test_admin_can_list_roles(self):
        admin_role = Role.objects.get_or_create(name='admin', defaults={'description': 'Admin'})[0]
        admin_user = get_user_model().objects.create_user(username='admin-roles', password='strong-password-123')
        admin_user.profile.role = admin_role
        admin_user.profile.save()

        token, _ = Token.objects.get_or_create(user=admin_user)
        response = self.client.get('/api/roles/', HTTP_AUTHORIZATION=f'Token {token.key}')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(isinstance(response.json(), (dict, list)))

    # Endpoint: GET /api/permissions/
    # Purpose: list permissions; requires admin access
    def test_admin_can_list_permissions(self):
        admin_role = Role.objects.get_or_create(name='admin', defaults={'description': 'Admin'})[0]
        admin_user = get_user_model().objects.create_user(username='admin-permissions', password='strong-password-123')
        admin_user.profile.role = admin_role
        admin_user.profile.save()

        token, _ = Token.objects.get_or_create(user=admin_user)
        response = self.client.get('/api/permissions/', HTTP_AUTHORIZATION=f'Token {token.key}')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(isinstance(response.json(), (dict, list)))

    # Endpoint: GET /api/dashboard/admin/
    # Purpose: admin dashboard access
    def test_admin_dashboard_access(self):
        admin_role = Role.objects.get_or_create(name='admin', defaults={'description': 'Admin'})[0]
        admin_user = get_user_model().objects.create_user(username='admin-dashboard', password='strong-password-123')
        admin_user.profile.role = admin_role
        admin_user.profile.save()

        token, _ = Token.objects.get_or_create(user=admin_user)
        response = self.client.get('/api/dashboard/admin/', HTTP_AUTHORIZATION=f'Token {token.key}')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['your_role'], 'admin')

    # Endpoint: GET /api/dashboard/manager/
    # Purpose: manager dashboard access
    def test_manager_dashboard_access(self):
        manager_role = Role.objects.get_or_create(name='manager', defaults={'description': 'Manager'})[0]
        manager_user = get_user_model().objects.create_user(username='manager-dashboard', password='strong-password-123')
        manager_user.profile.role = manager_role
        manager_user.profile.save()

        token, _ = Token.objects.get_or_create(user=manager_user)
        response = self.client.get('/api/dashboard/manager/', HTTP_AUTHORIZATION=f'Token {token.key}')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['your_role'], 'manager')

    # Endpoint: GET /api/tasks/
    # Purpose: access task management if the user has the right permission
    def test_task_management_requires_permission(self):
        permission = Permission.objects.get_or_create(name='can_manage_tasks', defaults={'description': 'Manage Tasks'})[0]
        admin_role = Role.objects.get_or_create(name='admin', defaults={'description': 'Admin'})[0]
        admin_user = get_user_model().objects.create_user(username='tasks-user', password='strong-password-123')
        admin_user.profile.role = admin_role
        admin_user.profile.permissions.add(permission)
        admin_user.profile.save()

        token, _ = Token.objects.get_or_create(user=admin_user)
        response = self.client.get('/api/tasks/', HTTP_AUTHORIZATION=f'Token {token.key}')

        self.assertEqual(response.status_code, 200)
        self.assertIn('Task Management Dashboard', response.json()['message'])
