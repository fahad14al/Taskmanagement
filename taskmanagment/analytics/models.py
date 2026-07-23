from django.db import models
from django.contrib.auth.models import User


class Report(models.Model):
    """
    Model for saving and storing generated analytical reports.
    """
    REPORT_TYPE_CHOICES = [
        ('task_summary', 'Task Summary Report'),
        ('project_status', 'Project Status Report'),
        ('user_productivity', 'User Productivity Report'),
        ('sprint_velocity', 'Sprint Velocity Report'),
        ('ticket_resolution', 'Ticket Resolution Report'),
        ('custom', 'Custom Analytical Report'),
    ]

    title = models.CharField(max_length=255, verbose_name="Report Title")
    report_type = models.CharField(
        max_length=50, 
        choices=REPORT_TYPE_CHOICES, 
        default='task_summary', 
        verbose_name="Report Type"
    )
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    parameters = models.JSONField(default=dict, blank=True, verbose_name="Report Parameters")
    data = models.JSONField(default=dict, blank=True, verbose_name="Computed Report Data")
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='analytics_reports', 
        verbose_name="Created By"
    )
    is_public = models.BooleanField(default=False, verbose_name="Is Public")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Report"
        verbose_name_plural = "Reports"

    def __str__(self):
        return f"{self.title} ({self.get_report_type_display()})"


class AnalyticsService(models.Model):
    """
    Model for tracking status, health metrics, and operations of analytics background services.
    """
    SERVICE_TYPE_CHOICES = [
        ('aggregator', 'Data Aggregation Service'),
        ('exporter', 'Export Service'),
        ('monitoring', 'System Monitoring Service'),
        ('reporting', 'Report Generation Service'),
    ]

    STATUS_CHOICES = [
        ('healthy', 'Healthy'),
        ('degraded', 'Degraded'),
        ('down', 'Down'),
        ('maintenance', 'Maintenance'),
    ]

    name = models.CharField(max_length=255, unique=True, verbose_name="Service Name")
    service_type = models.CharField(
        max_length=50, 
        choices=SERVICE_TYPE_CHOICES, 
        default='aggregator', 
        verbose_name="Service Type"
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='healthy', 
        verbose_name="Status"
    )
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    response_time_ms = models.IntegerField(default=0, verbose_name="Response Time (ms)")
    error_rate = models.FloatField(default=0.0, verbose_name="Error Rate (%)")
    last_run = models.DateTimeField(null=True, blank=True, verbose_name="Last Run Time")
    metadata = models.JSONField(default=dict, blank=True, verbose_name="Metadata")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        ordering = ['name']
        verbose_name = "Analytics Service"
        verbose_name_plural = "Analytics Services"

    def __str__(self):
        return f"{self.name} [{self.get_status_display()}]"
