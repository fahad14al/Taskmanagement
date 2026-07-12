from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AttachmentViewSet,
    ChecklistItemViewSet,
    ChecklistViewSet,
    DepartmentViewSet,
    OrganizationViewSet,
    ProjectMemberViewSet,
    ProjectViewSet,
    SprintViewSet,
    SubTaskViewSet,
    TaskViewSet,
    TeamMemberViewSet,
    TeamViewSet,
    TicketViewSet,
)

router = DefaultRouter()
router.register(r'organizations', OrganizationViewSet, basename='organization')
router.register(r'departments', DepartmentViewSet, basename='department')
router.register(r'teams', TeamViewSet, basename='team')
router.register(r'team-members', TeamMemberViewSet, basename='team-member')
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'project-members', ProjectMemberViewSet, basename='project-member')
router.register(r'sprints', SprintViewSet, basename='sprint')
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'subtasks', SubTaskViewSet, basename='subtask')
router.register(r'checklists', ChecklistViewSet, basename='checklist')
router.register(r'checklist-items', ChecklistItemViewSet, basename='checklist-item')
router.register(r'tickets', TicketViewSet, basename='ticket')
router.register(r'attachments', AttachmentViewSet, basename='attachment')

app_name = 'workspace'

urlpatterns = [
    path('', include(router.urls)),
]
