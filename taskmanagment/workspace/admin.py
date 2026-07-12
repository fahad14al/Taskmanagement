from django.contrib import admin

from .models import (
    Attachment,
    Checklist,
    ChecklistItem,
    Department,
    Organization,
    Project,
    ProjectMember,
    Sprint,
    SubTask,
    Task,
    Team,
    TeamMember,
    Ticket,
)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'slug', 'email', 'phone', 'is_active', 'created_at']
    search_fields = ['name', 'slug', 'email', 'phone']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'organization', 'head', 'is_active', 'created_at']
    search_fields = ['name', 'organization__name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'department', 'lead', 'is_active', 'created_at']
    search_fields = ['name', 'department__name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ['id', 'team', 'user', 'role', 'joined_at', 'is_active']
    search_fields = ['team__name', 'user__username']
    readonly_fields = ['joined_at']


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'organization', 'status', 'priority', 'progress', 'project_manager']
    search_fields = ['name', 'slug', 'organization__name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ProjectMember)
class ProjectMemberAdmin(admin.ModelAdmin):
    list_display = ['id', 'project', 'user', 'role', 'joined_at', 'is_active']
    search_fields = ['project__name', 'user__username']
    readonly_fields = ['joined_at']


@admin.register(Sprint)
class SprintAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'project', 'status', 'start_date', 'end_date']
    search_fields = ['name', 'project__name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'project', 'status', 'priority', 'assignee', 'due_date']
    search_fields = ['title', 'project__name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(SubTask)
class SubTaskAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'task', 'status', 'assignee', 'due_date']
    search_fields = ['title', 'task__title']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Checklist)
class ChecklistAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'task', 'created_at']
    search_fields = ['title', 'task__title']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ChecklistItem)
class ChecklistItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'checklist', 'content', 'is_checked', 'checked_by', 'updated_at']
    search_fields = ['content', 'checklist__title']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'project', 'ticket_type', 'status', 'priority', 'assignee', 'due_date']
    search_fields = ['title', 'project__name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'filename', 'content_type', 'uploaded_by', 'uploaded_at']
    search_fields = ['filename', 'description']
    readonly_fields = ['uploaded_at', 'updated_at']
