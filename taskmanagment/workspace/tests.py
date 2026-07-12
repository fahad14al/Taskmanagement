from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from .models import Department, Organization, Project, Task, Team, Ticket


class WorkspaceEndpointsTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='tester',
            password='Test1234'
        )
        self.organization = Organization.objects.create(
            name='Acme Corp',
            slug='acme-corp',
            description='Test organization',
            created_by=self.user,
        )
        self.department = Department.objects.create(
            organization=self.organization,
            name='Engineering',
            created_by=self.user,
        )
        self.team = Team.objects.create(
            department=self.department,
            name='Platform',
            created_by=self.user,
        )
        self.project = Project.objects.create(
            name='Launch Portal',
            slug='launch-portal',
            description='Project for tests',
            organization=self.organization,
            department=self.department,
            team=self.team,
            start_date='2026-01-01',
            end_date='2026-01-31',
            created_by=self.user,
            project_manager=self.user,
        )
        self.task = Task.objects.create(
            project=self.project,
            title='Create API',
            description='Build endpoint',
            due_date='2026-01-10',
            created_by=self.user,
            reporter=self.user,
            assignee=self.user,
        )
        self.ticket = Ticket.objects.create(
            project=self.project,
            task=self.task,
            title='Login issue',
            description='Users cannot sign in',
            due_date='2026-01-12',
            created_by=self.user,
            reporter=self.user,
            assignee=self.user,
        )

    # Endpoint: GET /api/workspace/organizations/
    def test_organizations_list_requires_authentication(self):
        url = reverse('workspace:organization-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

    # Endpoint: GET /api/workspace/organizations/
    def test_organizations_list_returns_data_for_authenticated_user(self):
        self.client.force_authenticate(self.user)
        url = reverse('workspace:organization-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data), 1)

    # Endpoint: POST /api/workspace/organizations/
    def test_organization_creation_is_supported(self):
        self.client.force_authenticate(self.user)
        url = reverse('workspace:organization-list')
        payload = {
            'name': 'Beta Labs',
            'slug': 'beta-labs',
            'description': 'Another test organization',
            'is_active': True,
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['name'], 'Beta Labs')

    # Endpoint: GET /api/workspace/projects/
    def test_projects_list_returns_data_for_authenticated_user(self):
        self.client.force_authenticate(self.user)
        url = reverse('workspace:project-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data), 1)

    # Endpoint: POST /api/workspace/tasks/
    def test_task_creation_is_supported(self):
        self.client.force_authenticate(self.user)
        url = reverse('workspace:task-list')
        payload = {
            'title': 'Write tests',
            'description': 'Create API tests',
            'project': self.project.id,
            'due_date': '2026-01-15',
            'assignee': self.user.id,
            'reporter': self.user.id,
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['title'], 'Write tests')

    # Endpoint: GET /api/workspace/tickets/
    def test_tickets_list_returns_data_for_authenticated_user(self):
        self.client.force_authenticate(self.user)
        url = reverse('workspace:ticket-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data), 1)
