from rest_framework import permissions, viewsets

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
from .serializers import (
    AttachmentCreateSerializer,
    AttachmentSerializer,
    ChecklistCreateUpdateSerializer,
    ChecklistItemSerializer,
    ChecklistSerializer,
    DepartmentSerializer,
    OrganizationCreateUpdateSerializer,
    OrganizationDetailSerializer,
    OrganizationListSerializer,
    ProjectCreateUpdateSerializer,
    ProjectDetailSerializer,
    ProjectListSerializer,
    ProjectMemberSerializer,
    SprintCreateUpdateSerializer,
    SprintSerializer,
    SubTaskSerializer,
    TaskCreateUpdateSerializer,
    TaskDetailSerializer,
    TaskListSerializer,
    TeamDetailSerializer,
    TeamMemberSerializer,
    TeamSerializer,
    TicketCreateUpdateSerializer,
    TicketDetailSerializer,
    TicketListSerializer,
)


class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.select_related('created_by').all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action in {'create', 'update', 'partial_update'}:
            return OrganizationCreateUpdateSerializer
        if self.action == 'retrieve':
            return OrganizationDetailSerializer
        return OrganizationListSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.select_related('organization', 'head', 'created_by').all()
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.select_related('department', 'lead', 'created_by').all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return TeamDetailSerializer
        return TeamSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class TeamMemberViewSet(viewsets.ModelViewSet):
    queryset = TeamMember.objects.select_related('team', 'user').all()
    serializer_class = TeamMemberSerializer
    permission_classes = [permissions.IsAuthenticated]


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.select_related('organization', 'department', 'team', 'project_manager', 'created_by').all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action in {'create', 'update', 'partial_update'}:
            return ProjectCreateUpdateSerializer
        if self.action == 'retrieve':
            return ProjectDetailSerializer
        return ProjectListSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ProjectMemberViewSet(viewsets.ModelViewSet):
    queryset = ProjectMember.objects.select_related('project', 'user').all()
    serializer_class = ProjectMemberSerializer
    permission_classes = [permissions.IsAuthenticated]


class SprintViewSet(viewsets.ModelViewSet):
    queryset = Sprint.objects.select_related('project').all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action in {'create', 'update', 'partial_update'}:
            return SprintCreateUpdateSerializer
        return SprintSerializer


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.select_related('project', 'sprint', 'assignee', 'reporter', 'created_by').all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action in {'create', 'update', 'partial_update'}:
            return TaskCreateUpdateSerializer
        if self.action == 'retrieve':
            return TaskDetailSerializer
        return TaskListSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, reporter=self.request.user)


class SubTaskViewSet(viewsets.ModelViewSet):
    queryset = SubTask.objects.select_related('task', 'assignee', 'created_by').all()
    serializer_class = SubTaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ChecklistViewSet(viewsets.ModelViewSet):
    queryset = Checklist.objects.select_related('task', 'created_by').all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action in {'create', 'update', 'partial_update'}:
            return ChecklistCreateUpdateSerializer
        return ChecklistSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ChecklistItemViewSet(viewsets.ModelViewSet):
    queryset = ChecklistItem.objects.select_related('checklist', 'checked_by').all()
    serializer_class = ChecklistItemSerializer
    permission_classes = [permissions.IsAuthenticated]


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.select_related('project', 'task', 'reporter', 'assignee', 'resolver', 'created_by').all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action in {'create', 'update', 'partial_update'}:
            return TicketCreateUpdateSerializer
        if self.action == 'retrieve':
            return TicketDetailSerializer
        return TicketListSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class AttachmentViewSet(viewsets.ModelViewSet):
    queryset = Attachment.objects.select_related('uploaded_by').all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action in {'create', 'update', 'partial_update'}:
            return AttachmentCreateSerializer
        return AttachmentSerializer
