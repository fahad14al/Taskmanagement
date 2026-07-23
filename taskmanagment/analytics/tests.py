from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from analytics.models import Report, AnalyticsService


class AnalyticsEndpointsTestCase(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.client.force_authenticate(user=self.user)

    def test_dashboard_endpoints(self):
        # GET /api/analytics/dashboard/
        response = self.client.get('/api/analytics/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('summary', response.data)
        self.assertIn('project_overview', response.data)

        # GET /api/analytics/dashboard/summary/
        response = self.client.get('/api/analytics/dashboard/summary/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('completion_rate', response.data)

        # GET /api/analytics/dashboard/my-summary/
        response = self.client.get('/api/analytics/dashboard/my-summary/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')

    def test_reports_endpoints(self):
        # GET /api/analytics/reports/
        response = self.client.get('/api/analytics/reports/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # POST /api/analytics/reports/
        create_payload = {
            'title': 'Test Report',
            'report_type': 'task_summary',
            'description': 'Description for test report',
            'is_public': True
        }
        response = self.client.post('/api/analytics/reports/', create_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        report_id = response.data['id']

        # POST /api/analytics/reports/generate/
        gen_payload = {
            'report_type': 'task_summary',
            'save_report': True
        }
        response = self.client.post('/api/analytics/reports/generate/', gen_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)

        # GET /api/analytics/reports/{id}/export/
        response = self.client.get(f'/api/analytics/reports/{report_id}/export/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_statistics_endpoints(self):
        # GET /api/analytics/statistics/
        response = self.client.get('/api/analytics/statistics/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tasks', response.data)
        self.assertIn('projects', response.data)

        # GET /api/analytics/statistics/tasks/
        response = self.client.get('/api/analytics/statistics/tasks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # GET /api/analytics/statistics/projects/
        response = self.client.get('/api/analytics/statistics/projects/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # GET /api/analytics/statistics/sprints/
        response = self.client.get('/api/analytics/statistics/sprints/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # GET /api/analytics/statistics/users/
        response = self.client.get('/api/analytics/statistics/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_services_endpoints(self):
        # GET /api/analytics/services/
        response = self.client.get('/api/analytics/services/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # GET /api/analytics/services/health/
        response = self.client.get('/api/analytics/services/health/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('overall_status', response.data)

        # POST /api/analytics/services/export/
        export_payload = {
            'export_type': 'dashboard',
            'format': 'json'
        }
        response = self.client.post('/api/analytics/services/export/', export_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # POST /api/analytics/services/run-aggregation/
        response = self.client.post('/api/analytics/services/run-aggregation/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
