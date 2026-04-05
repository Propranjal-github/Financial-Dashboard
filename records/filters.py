import django_filters

from .models import FinancialRecord


class FinancialRecordFilter(django_filters.FilterSet):
    """
    Filters for FinancialRecord listing:
    - date_from / date_to  — date range
    - category             — exact match
    - record_type          — exact match (income / expense)
    - status               — exact match
    - amount_min / amount_max — amount range
    """

    date_from = django_filters.DateFilter(field_name='date', lookup_expr='gte')
    date_to = django_filters.DateFilter(field_name='date', lookup_expr='lte')
    amount_min = django_filters.NumberFilter(field_name='amount', lookup_expr='gte')
    amount_max = django_filters.NumberFilter(field_name='amount', lookup_expr='lte')

    class Meta:
        model = FinancialRecord
        fields = ['record_type', 'category', 'status']
