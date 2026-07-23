from django.contrib import admin
from .models import Report, AnalyticsService


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'report_type', 'created_by', 'is_public', 'created_at')
    list_filter = ('report_type', 'is_public', 'created_at')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(AnalyticsService)
class AnalyticsServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'service_type', 'status', 'response_time_ms', 'error_rate', 'last_run', 'is_active')
    list_filter = ('service_type', 'status', 'is_active')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
