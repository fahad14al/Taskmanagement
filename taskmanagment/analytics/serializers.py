from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Report, AnalyticsService


class ReportSerializer(serializers.ModelSerializer):
    created_by_username = serializers.ReadOnlyField(source='created_by.username')
    report_type_display = serializers.CharField(source='get_report_type_display', read_only=True)

    class Meta:
        model = Report
        fields = [
            'id',
            'title',
            'report_type',
            'report_type_display',
            'description',
            'parameters',
            'data',
            'created_by',
            'created_by_username',
            'is_public',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


class ReportCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = [
            'title',
            'report_type',
            'description',
            'parameters',
            'is_public',
        ]

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user if user.is_authenticated else None
        return super().create(validated_data)


class GenerateReportSerializer(serializers.Serializer):
    report_type = serializers.ChoiceField(
        choices=Report.REPORT_TYPE_CHOICES,
        default='task_summary'
    )
    title = serializers.CharField(max_length=255, required=False, allow_blank=True)
    project_id = serializers.IntegerField(required=False, allow_null=True)
    department_id = serializers.IntegerField(required=False, allow_null=True)
    start_date = serializers.DateField(required=False, allow_null=True)
    end_date = serializers.DateField(required=False, allow_null=True)
    save_report = serializers.BooleanField(default=False)


class AnalyticsServiceSerializer(serializers.ModelSerializer):
    service_type_display = serializers.CharField(source='get_service_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = AnalyticsService
        fields = [
            'id',
            'name',
            'service_type',
            'service_type_display',
            'status',
            'status_display',
            'description',
            'response_time_ms',
            'error_rate',
            'last_run',
            'metadata',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AnalyticsExportSerializer(serializers.Serializer):
    EXPORT_FORMAT_CHOICES = [
        ('json', 'JSON'),
        ('csv', 'CSV'),
    ]
    EXPORT_TYPE_CHOICES = [
        ('dashboard', 'DashboardSummary'),
        ('tasks', 'Tasks Statistics'),
        ('projects', 'Projects Statistics'),
        ('sprints', 'Sprint Velocity Statistics'),
        ('users', 'User Productivity'),
    ]

    export_type = serializers.ChoiceField(choices=EXPORT_TYPE_CHOICES, default='dashboard')
    format = serializers.ChoiceField(choices=EXPORT_FORMAT_CHOICES, default='json')
    project_id = serializers.IntegerField(required=False, allow_null=True)
    start_date = serializers.DateField(required=False, allow_null=True)
    end_date = serializers.DateField(required=False, allow_null=True)


class StatisticsFilterSerializer(serializers.Serializer):
    project_id = serializers.IntegerField(required=False, allow_null=True)
    sprint_id = serializers.IntegerField(required=False, allow_null=True)
    start_date = serializers.DateField(required=False, allow_null=True)
    end_date = serializers.DateField(required=False, allow_null=True)
