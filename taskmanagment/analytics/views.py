import csv
import io
from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Avg, Sum, Q, F
from django.contrib.auth.models import User
from django.http import HttpResponse

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from workspace.models import Project, Task, Sprint, Ticket, Department, Team, SubTask
from collaboration.models import ActivityLog, Comment, Notification
from communication.models import ChatRoom, Message

from .models import Report, AnalyticsService
from .serializers import (
    ReportSerializer,
    ReportCreateSerializer,
    GenerateReportSerializer,
    AnalyticsServiceSerializer,
    AnalyticsExportSerializer,
    StatisticsFilterSerializer,
)


class DashboardViewSet(viewsets.ViewSet):
    """
    Dashboardendpoints providing high-level KPI metrics, project status,
    task completion rates, and recent activity overview.
    """
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        """
        GET /api/analytics/dashboard/
        Returns comprehensive workspace dashboard metrics.
        """
        user = request.user

        # Total counts
        total_projects = Project.objects.filter(is_active=True).count()
        total_tasks = Task.objects.filter(is_active=True).count()
        total_tickets = Ticket.objects.count()
        total_users = User.objects.filter(is_active=True).count()
        total_sprints = Sprint.objects.count()

        # Task Status Metrics
        completed_tasks = Task.objects.filter(is_active=True, status='completed').count()
        in_progress_tasks = Task.objects.filter(is_active=True, status='in_progress').count()
        today = timezone.now().date()
        overdue_tasks = Task.objects.filter(
            is_active=True, 
            due_date__lt=today
        ).exclude(status='completed').count()

        completion_rate = round((completed_tasks / total_tasks * 100), 2) if total_tasks > 0 else 0.0

        # Project breakdown
        project_status_counts = dict(
            Project.objects.filter(is_active=True)
            .values('status')
            .annotate(count=Count('id'))
            .values_list('status', 'count')
        )

        # Task priority breakdown
        task_priority_counts = dict(
            Task.objects.filter(is_active=True)
            .values('priority')
            .annotate(count=Count('id'))
            .values_list('priority', 'count')
        )

        # Ticket status breakdown
        ticket_status_counts = dict(
            Ticket.objects.values('status')
            .annotate(count=Count('id'))
            .values_list('status', 'count')
        )

        # Recent activities
        recent_activities = ActivityLog.objects.select_related('actor')[:5]
        activity_data = [
            {
                'id': act.id,
                'actor': act.actor.username if act.actor else 'System',
                'action_type': act.action_type,
                'action_description': act.action_description,
                'created_at': act.created_at,
            }
            for act in recent_activities
        ]

        # User personal metrics
        my_assigned_tasks = Task.objects.filter(assignee=user, is_active=True).exclude(status='completed').count()
        my_completed_tasks = Task.objects.filter(assignee=user, is_active=True, status='completed').count()
        my_tickets = Ticket.objects.filter(assignee=user).exclude(status='closed').count()

        data = {
            'summary': {
                'total_projects': total_projects,
                'total_tasks': total_tasks,
                'total_tickets': total_tickets,
                'total_users': total_users,
                'total_sprints': total_sprints,
                'completed_tasks': completed_tasks,
                'in_progress_tasks': in_progress_tasks,
                'overdue_tasks': overdue_tasks,
                'task_completion_rate': completion_rate,
            },
            'project_overview': {
                'status_breakdown': project_status_counts,
                'average_progress': round(Project.objects.filter(is_active=True).aggregate(avg=Avg('progress'))['avg'] or 0.0, 2),
            },
            'task_overview': {
                'priority_breakdown': task_priority_counts,
                'status_breakdown': dict(
                    Task.objects.filter(is_active=True)
                    .values('status')
                    .annotate(count=Count('id'))
                    .values_list('status', 'count')
                ),
            },
            'ticket_overview': {
                'status_breakdown': ticket_status_counts,
                'open_tickets': Ticket.objects.filter(status='open').count(),
                'resolved_tickets': Ticket.objects.filter(status='resolved').count(),
            },
            'user_metrics': {
                'my_assigned_tasks': my_assigned_tasks,
                'my_completed_tasks': my_completed_tasks,
                'my_pending_tickets': my_tickets,
            },
            'recent_activity': activity_data,
        }
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request):
        """
        GET /api/analytics/dashboard/summary/
        Returns high-level summary KPIs only.
        """
        total_projects = Project.objects.filter(is_active=True).count()
        total_tasks = Task.objects.filter(is_active=True).count()
        completed_tasks = Task.objects.filter(is_active=True, status='completed').count()
        total_tickets = Ticket.objects.count()
        active_sprints = Sprint.objects.filter(status='active').count()

        return Response({
            'total_projects': total_projects,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'pending_tasks': total_tasks - completed_tasks,
            'total_tickets': total_tickets,
            'active_sprints': active_sprints,
            'completion_rate': round((completed_tasks / total_tasks * 100), 2) if total_tasks > 0 else 0.0,
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='my-summary')
    def my_summary(self, request):
        """
        GET /api/analytics/dashboard/my-summary/
        Returns personalized dashboard summary for the logged-in user.
        """
        user = request.user
        tasks_qs = Task.objects.filter(assignee=user, is_active=True)
        tickets_qs = Ticket.objects.filter(assignee=user)

        return Response({
            'user_id': user.id,
            'username': user.username,
            'assigned_tasks_count': tasks_qs.count(),
            'pending_tasks_count': tasks_qs.exclude(status='completed').count(),
            'completed_tasks_count': tasks_qs.filter(status='completed').count(),
            'assigned_tickets_count': tickets_qs.count(),
            'open_tickets_count': tickets_qs.filter(status='open').count(),
        }, status=status.HTTP_200_OK)


class ReportViewSet(viewsets.ModelViewSet):
    """
    CRUD ViewSet for analytical reports + dynamic generation and export functionality.
    """
    permission_classes = [permissions.IsAuthenticated]
    queryset = Report.objects.all().order_by('-created_at')
    serializer_class = ReportSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return ReportCreateSerializer
        return ReportSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return Report.objects.filter(Q(created_by=user) | Q(is_public=True)).order_by('-created_at')
        return Report.objects.none()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        report = serializer.save()
        out = ReportSerializer(report, context={'request': request})
        return Response(out.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='generate')
    def generate(self, request):
        """
        POST /api/analytics/reports/generate/
        Dynamically computes report metrics based on report_type, date ranges, or project parameters.
        Optionally saves the computed report to the DB if save_report=True.
        """
        serializer = GenerateReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        params = serializer.validated_data

        report_type = params.get('report_type', 'task_summary')
        title = params.get('title') or f"Generated {report_type.replace('_', ' ').title()} Report"
        project_id = params.get('project_id')
        start_date = params.get('start_date')
        end_date = params.get('end_date')
        save_report = params.get('save_report', False)

        # Filters
        task_qs = Task.objects.filter(is_active=True)
        project_qs = Project.objects.filter(is_active=True)
        ticket_qs = Ticket.objects.all()

        if project_id:
            task_qs = task_qs.filter(project_id=project_id)
            project_qs = project_qs.filter(id=project_id)
            ticket_qs = ticket_qs.filter(project_id=project_id)

        if start_date:
            task_qs = task_qs.filter(created_at__date__gte=start_date)
            project_qs = project_qs.filter(created_at__date__gte=start_date)
            ticket_qs = ticket_qs.filter(created_at__date__gte=start_date)

        if end_date:
            task_qs = task_qs.filter(created_at__date__lte=end_date)
            project_qs = project_qs.filter(created_at__date__lte=end_date)
            ticket_qs = ticket_qs.filter(created_at__date__lte=end_date)

        # Compute data based on report_type
        if report_type == 'task_summary':
            total = task_qs.count()
            by_status = dict(task_qs.values('status').annotate(count=Count('id')).values_list('status', 'count'))
            by_priority = dict(task_qs.values('priority').annotate(count=Count('id')).values_list('priority', 'count'))
            by_type = dict(task_qs.values('task_type').annotate(count=Count('id')).values_list('task_type', 'count'))
            report_data = {
                'total_tasks': total,
                'completed_count': by_status.get('completed', 0),
                'by_status': by_status,
                'by_priority': by_priority,
                'by_type': by_type,
            }
        elif report_type == 'project_status':
            total = project_qs.count()
            by_status = dict(project_qs.values('status').annotate(count=Count('id')).values_list('status', 'count'))
            avg_progress = project_qs.aggregate(avg=Avg('progress'))['avg'] or 0.0
            report_data = {
                'total_projects': total,
                'average_progress': round(avg_progress, 2),
                'by_status': by_status,
            }
        elif report_type == 'user_productivity':
            user_stats = (
                User.objects.filter(is_active=True)
                .annotate(
                    assigned_tasks_count=Count('assigned_tasks', filter=Q(assigned_tasks__is_active=True)),
                    completed_tasks_count=Count('assigned_tasks', filter=Q(assigned_tasks__is_active=True, assigned_tasks__status='completed')),
                    resolved_tickets_count=Count('resolved_tickets'),
                )
                .values('id', 'username', 'assigned_tasks_count', 'completed_tasks_count', 'resolved_tickets_count')[:20]
            )
            report_data = {
                'users': list(user_stats)
            }
        elif report_type == 'sprint_velocity':
            sprints = Sprint.objects.all()
            if project_id:
                sprints = sprints.filter(project_id=project_id)
            sprint_data = list(sprints.values(
                'id', 'name', 'project__name', 'status', 'total_story_points', 'completed_story_points'
            ))
            report_data = {
                'total_sprints': sprints.count(),
                'sprints': sprint_data,
            }
        elif report_type == 'ticket_resolution':
            total = ticket_qs.count()
            by_status = dict(ticket_qs.values('status').annotate(count=Count('id')).values_list('status', 'count'))
            by_type = dict(ticket_qs.values('ticket_type').annotate(count=Count('id')).values_list('ticket_type', 'count'))
            report_data = {
                'total_tickets': total,
                'resolved_count': by_status.get('resolved', 0) + by_status.get('closed', 0),
                'by_status': by_status,
                'by_type': by_type,
            }
        else: # custom
            report_data = {
                'total_tasks': task_qs.count(),
                'total_projects': project_qs.count(),
                'total_tickets': ticket_qs.count(),
            }

        response_payload = {
            'title': title,
            'report_type': report_type,
            'parameters': {
                'project_id': project_id,
                'start_date': str(start_date) if start_date else None,
                'end_date': str(end_date) if end_date else None,
            },
            'data': report_data,
        }

        if save_report:
            saved_report = Report.objects.create(
                title=title,
                report_type=report_type,
                description=f"Generated report for {report_type}",
                parameters=response_payload['parameters'],
                data=report_data,
                created_by=request.user if request.user.is_authenticated else None,
            )
            response_payload['id'] = saved_report.id
            response_payload['created_at'] = saved_report.created_at

        return Response(response_payload, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='export')
    def export(self, request, pk=None):
        """
        GET /api/analytics/reports/{id}/export/?format=csv|json
        Export a saved report to CSV or JSON format.
        """
        report = self.get_object()
        export_format = request.query_params.get('format', 'json').lower()

        if export_format == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="report_{report.id}.csv"'

            writer = csv.writer(response)
            writer.writerow(['Report ID', report.id])
            writer.writerow(['Title', report.title])
            writer.writerow(['Report Type', report.report_type])
            writer.writerow(['Created At', report.created_at])
            writer.writerow([])
            writer.writerow(['Data Key', 'Data Value'])

            if isinstance(report.data, dict):
                for k, v in report.data.items():
                    writer.writerow([k, str(v)])

            return response

        return Response({
            'report_id': report.id,
            'title': report.title,
            'report_type': report.report_type,
            'data': report.data,
            'parameters': report.parameters,
        })


class StatisticsViewSet(viewsets.ViewSet):
    """
    Statistics endpoints providing detailed statistical aggregations
    for tasks, projects, sprints, users, and workloads.
    """
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        """
        GET /api/analytics/statistics/
        Returns global statistical breakdown across all models.
        """
        filter_serializer = StatisticsFilterSerializer(data=request.query_params)
        filter_serializer.is_valid()
        filters = filter_serializer.validated_data

        project_id = filters.get('project_id')
        sprint_id = filters.get('sprint_id')

        task_qs = Task.objects.filter(is_active=True)
        if project_id:
            task_qs = task_qs.filter(project_id=project_id)
        if sprint_id:
            task_qs = task_qs.filter(sprint_id=sprint_id)

        task_stats = {
            'by_status': list(task_qs.values('status').annotate(count=Count('id'))),
            'by_priority': list(task_qs.values('priority').annotate(count=Count('id'))),
            'by_type': list(task_qs.values('task_type').annotate(count=Count('id'))),
            'total_story_points': task_qs.aggregate(total=Sum('story_points'))['total'] or 0,
        }

        project_stats = {
            'total_projects': Project.objects.filter(is_active=True).count(),
            'by_status': list(Project.objects.filter(is_active=True).values('status').annotate(count=Count('id'))),
            'by_priority': list(Project.objects.filter(is_active=True).values('priority').annotate(count=Count('id'))),
        }

        sprint_stats = {
            'total_sprints': Sprint.objects.count(),
            'by_status': list(Sprint.objects.values('status').annotate(count=Count('id'))),
            'planned_points': Sprint.objects.aggregate(total=Sum('total_story_points'))['total'] or 0,
            'completed_points': Sprint.objects.aggregate(total=Sum('completed_story_points'))['total'] or 0,
        }

        return Response({
            'tasks': task_stats,
            'projects': project_stats,
            'sprints': sprint_stats,
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='tasks')
    def tasks_stats(self, request):
        """
        GET /api/analytics/statistics/tasks/
        Returns task-specific statistical distributions.
        """
        project_id = request.query_params.get('project_id')
        qs = Task.objects.filter(is_active=True)
        if project_id:
            qs = qs.filter(project_id=project_id)

        total = qs.count()
        completed = qs.filter(status='completed').count()

        return Response({
            'total_tasks': total,
            'completed_tasks': completed,
            'completion_rate': round((completed / total * 100), 2) if total > 0 else 0.0,
            'status_distribution': list(qs.values('status').annotate(count=Count('id'))),
            'priority_distribution': list(qs.values('priority').annotate(count=Count('id'))),
            'type_distribution': list(qs.values('task_type').annotate(count=Count('id'))),
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='projects')
    def projects_stats(self, request):
        """
        GET /api/analytics/statistics/projects/
        Returns project progress distributions and metrics.
        """
        qs = Project.objects.filter(is_active=True)
        total = qs.count()
        avg_progress = qs.aggregate(avg=Avg('progress'))['avg'] or 0.0

        return Response({
            'total_projects': total,
            'average_progress': round(avg_progress, 2),
            'status_distribution': list(qs.values('status').annotate(count=Count('id'))),
            'priority_distribution': list(qs.values('priority').annotate(count=Count('id'))),
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='sprints')
    def sprints_stats(self, request):
        """
        GET /api/analytics/statistics/sprints/
        Returns sprint velocity and story point statistics.
        """
        project_id = request.query_params.get('project_id')
        qs = Sprint.objects.all()
        if project_id:
            qs = qs.filter(project_id=project_id)

        total_planned = qs.aggregate(total=Sum('total_story_points'))['total'] or 0
        total_completed = qs.aggregate(total=Sum('completed_story_points'))['total'] or 0
        velocity_rate = round((total_completed / total_planned * 100), 2) if total_planned > 0 else 0.0

        return Response({
            'total_sprints': qs.count(),
            'total_planned_story_points': total_planned,
            'total_completed_story_points': total_completed,
            'velocity_rate': velocity_rate,
            'sprint_list': list(qs.values('id', 'name', 'status', 'total_story_points', 'completed_story_points')),
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='users')
    def users_stats(self, request):
        """
        GET /api/analytics/statistics/users/
        Returns user productivity and workload statistics.
        """
        user_stats = (
            User.objects.filter(is_active=True)
            .annotate(
                assigned_tasks_count=Count('assigned_tasks', filter=Q(assigned_tasks__is_active=True)),
                completed_tasks_count=Count('assigned_tasks', filter=Q(assigned_tasks__is_active=True, assigned_tasks__status='completed')),
                open_tickets_count=Count('assigned_tickets', filter=Q(assigned_tickets__status='open')),
            )
            .values('id', 'username', 'email', 'assigned_tasks_count', 'completed_tasks_count', 'open_tickets_count')
        )
        return Response({'user_statistics': list(user_stats)}, status=status.HTTP_200_OK)


class ServicesViewSet(viewsets.ModelViewSet):
    """
    CRUD & monitoring for analytics services, health checks, background workers, and export services.
    """
    permission_classes = [permissions.IsAuthenticated]
    queryset = AnalyticsService.objects.all().order_by('name')
    serializer_class = AnalyticsServiceSerializer

    def list(self, request, *args, **kwargs):
        """
        GET /api/analytics/services/
        Lists analytics services. Automatically seeds default services if table is empty.
        """
        if not AnalyticsService.objects.exists():
            self._seed_default_services()
        return super().list(request, *args, **kwargs)

    def _seed_default_services(self):
        default_services = [
            {
                'name': 'Data Aggregator Service',
                'service_type': 'aggregator',
                'status': 'healthy',
                'description': 'Aggregates workspace metrics and task statistics periodically.',
                'response_time_ms': 45,
                'error_rate': 0.0,
                'last_run': timezone.now(),
            },
            {
                'name': 'Report Generation Service',
                'service_type': 'reporting',
                'status': 'healthy',
                'description': 'Generates PDF/CSV analytical reports dynamically.',
                'response_time_ms': 120,
                'error_rate': 0.1,
                'last_run': timezone.now(),
            },
            {
                'name': 'Export Service',
                'service_type': 'exporter',
                'status': 'healthy',
                'description': 'Handles data export requests in CSV and JSON formats.',
                'response_time_ms': 85,
                'error_rate': 0.0,
                'last_run': timezone.now(),
            },
            {
                'name': 'System Monitoring Service',
                'service_type': 'monitoring',
                'status': 'healthy',
                'description': 'Monitors response times, error rates, and system health.',
                'response_time_ms': 15,
                'error_rate': 0.0,
                'last_run': timezone.now(),
            },
        ]
        for svc in default_services:
            AnalyticsService.objects.get_or_create(name=svc['name'], defaults=svc)

    @action(detail=False, methods=['get'], url_path='health')
    def health(self, request):
        """
        GET /api/analytics/services/health/
        Returns system monitoring health status summary.
        """
        if not AnalyticsService.objects.exists():
            self._seed_default_services()

        services = AnalyticsService.objects.all()
        total_services = services.count()
        healthy_count = services.filter(status='healthy').count()
        degraded_count = services.filter(status='degraded').count()
        down_count = services.filter(status='down').count()

        overall_status = 'healthy'
        if down_count > 0:
            overall_status = 'down'
        elif degraded_count > 0:
            overall_status = 'degraded'

        avg_response_time = services.aggregate(avg=Avg('response_time_ms'))['avg'] or 0.0
        avg_error_rate = services.aggregate(avg=Avg('error_rate'))['avg'] or 0.0

        return Response({
            'overall_status': overall_status,
            'total_services': total_services,
            'healthy_services': healthy_count,
            'degraded_services': degraded_count,
            'down_services': down_count,
            'avg_response_time_ms': round(avg_response_time, 2),
            'avg_error_rate_percent': round(avg_error_rate, 2),
            'services': AnalyticsServiceSerializer(services, many=True).data,
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='export')
    def export(self, request):
        """
        POST /api/analytics/services/export/
        Triggers data export service for dashboard, tasks, projects, or users statistics.
        """
        serializer = AnalyticsExportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        export_type = data.get('export_type', 'dashboard')
        export_format = data.get('format', 'json')

        # Record activity / service run
        service = AnalyticsService.objects.filter(service_type='exporter').first()
        if service:
            service.last_run = timezone.now()
            service.save(update_fields=['last_run'])

        # Gather dataset
        if export_type == 'tasks':
            dataset = list(Task.objects.filter(is_active=True).values('id', 'title', 'status', 'priority', 'task_type', 'due_date'))
        elif export_type == 'projects':
            dataset = list(Project.objects.filter(is_active=True).values('id', 'name', 'status', 'priority', 'progress'))
        elif export_type == 'sprints':
            dataset = list(Sprint.objects.values('id', 'name', 'status', 'total_story_points', 'completed_story_points'))
        elif export_type == 'users':
            dataset = list(User.objects.filter(is_active=True).values('id', 'username', 'email'))
        else: # dashboard summary
            dataset = [{
                'total_projects': Project.objects.filter(is_active=True).count(),
                'total_tasks': Task.objects.filter(is_active=True).count(),
                'completed_tasks': Task.objects.filter(is_active=True, status='completed').count(),
                'total_tickets': Ticket.objects.count(),
            }]

        if export_format == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="analytics_{export_type}.csv"'
            if dataset:
                writer = csv.DictWriter(response, fieldnames=dataset[0].keys())
                writer.writeheader()
                writer.writerows(dataset)
            return response

        return Response({
            'export_type': export_type,
            'format': export_format,
            'count': len(dataset),
            'results': dataset,
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='run-aggregation')
    def run_aggregation(self, request):
        """
        POST /api/analytics/services/run-aggregation/
        Triggers data aggregation service manually and updates service metrics.
        """
        service = AnalyticsService.objects.filter(service_type='aggregator').first()
        if service:
            service.last_run = timezone.now()
            service.status = 'healthy'
            service.save(update_fields=['last_run', 'status'])

        return Response({
            'message': 'Aggregation service executed successfully.',
            'timestamp': timezone.now(),
            'metrics_updated': {
                'projects': Project.objects.count(),
                'tasks': Task.objects.count(),
                'tickets': Ticket.objects.count(),
            }
        }, status=status.HTTP_200_OK)
