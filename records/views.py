from rest_framework import viewsets, permissions

from accounts.permissions import IsAdmin
from .filters import FinancialRecordFilter
from .models import FinancialRecord
from .serializers import FinancialRecordSerializer


class FinancialRecordViewSet(viewsets.ModelViewSet):
    """
    CRUD for financial records.

    Visibility: All records are global (organization-scoped).
    - All authenticated users can list and retrieve records.
    - Only admins can create, update, or delete records.

    Supports filtering (date, category, type, status, amount range)
    and search on description.
    """

    queryset = FinancialRecord.objects.select_related('created_by').all()
    serializer_class = FinancialRecordSerializer
    filterset_class = FinancialRecordFilter
    search_fields = ['description', 'category']
    ordering_fields = ['date', 'amount', 'created_at']

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), IsAdmin()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
