from datetime import datetime

from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncMonth
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAnalystOrAbove
from records.models import FinancialRecord


class SummaryView(APIView):
    """
    Dashboard summary — accessible to all authenticated users.

    Returns:
    - total_income, total_expense, net_balance
    - record_count
    - recent 5 records
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qs = FinancialRecord.objects.all()

        totals = qs.aggregate(
            total_income=Sum('amount', filter=Q(record_type='income')) or 0,
            total_expense=Sum('amount', filter=Q(record_type='expense')) or 0,
            record_count=Count('id'),
        )

        total_income = totals['total_income'] or 0
        total_expense = totals['total_expense'] or 0

        recent = qs.order_by('-created_at')[:5].values(
            'id', 'record_type', 'amount', 'category', 'date', 'status',
        )

        return Response({
            'total_income': total_income,
            'total_expense': total_expense,
            'net_balance': total_income - total_expense,
            'record_count': totals['record_count'],
            'recent_records': list(recent),
        })


class AnalyticsView(APIView):
    """
    Detailed analytics — accessible to analysts and admins only.

    Returns:
    - category_breakdown   — totals per category
    - type_distribution    — count and total per record type
    - monthly_trends       — income and expense totals per month
    """

    permission_classes = [permissions.IsAuthenticated, IsAnalystOrAbove]

    def get(self, request):
        qs = FinancialRecord.objects.all()

        # Category breakdown
        category_breakdown = list(
            qs.values('category').annotate(
                total=Sum('amount'),
                count=Count('id'),
            ).order_by('-total')
        )

        # Type distribution
        type_distribution = list(
            qs.values('record_type').annotate(
                total=Sum('amount'),
                count=Count('id'),
            )
        )

        # Monthly trends
        monthly_trends = list(
            qs.annotate(month=TruncMonth('date'))
            .values('month')
            .annotate(
                income=Sum('amount', filter=Q(record_type='income')),
                expense=Sum('amount', filter=Q(record_type='expense')),
            )
            .order_by('month')
        )

        # Convert month to string for JSON serialization
        for entry in monthly_trends:
            entry['month'] = entry['month'].strftime('%Y-%m') if entry['month'] else None
            entry['income'] = entry['income'] or 0
            entry['expense'] = entry['expense'] or 0

        return Response({
            'category_breakdown': category_breakdown,
            'type_distribution': type_distribution,
            'monthly_trends': monthly_trends,
        })


class TimeAnalyticsView(APIView):
    """
    Time-scoped financial analysis — accessible to analysts and admins only.

    Query parameters:
        type=daily&date=2026-04-05
        type=monthly&month=2026-04
        type=yearly&year=2026
        start_date=2026-01-01&end_date=2026-03-31  (custom range)
    """

    permission_classes = [permissions.IsAuthenticated, IsAnalystOrAbove]

    def get(self, request):
        analysis_type = request.query_params.get('type', '')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        # Custom date range (no 'type' needed)
        if start_date and end_date:
            start = self._parse_date(start_date)
            end = self._parse_date(end_date)
            if start is None or end is None:
                return self._error('Invalid date format. Use YYYY-MM-DD.')
            if start > end:
                return self._error('start_date must be before end_date.')
            qs = FinancialRecord.objects.filter(date__gte=start, date__lte=end)
            label = f'{start_date} to {end_date}'
            return self._build_response(qs, 'custom', label, include_daily_trend=True)

        # Type-based analysis
        if analysis_type == 'daily':
            date_str = request.query_params.get('date')
            if not date_str:
                return self._error('date parameter is required for daily analysis.')
            date = self._parse_date(date_str)
            if date is None:
                return self._error('Invalid date format. Use YYYY-MM-DD.')
            qs = FinancialRecord.objects.filter(date=date)
            return self._build_response(qs, 'daily', date_str)

        elif analysis_type == 'monthly':
            month_str = request.query_params.get('month')
            if not month_str:
                return self._error('month parameter is required for monthly analysis.')
            try:
                dt = datetime.strptime(month_str, '%Y-%m')
            except ValueError:
                return self._error('Invalid month format. Use YYYY-MM.')
            qs = FinancialRecord.objects.filter(
                date__year=dt.year, date__month=dt.month,
            )
            return self._build_response(qs, 'monthly', month_str, include_daily_trend=True)

        elif analysis_type == 'yearly':
            year_str = request.query_params.get('year')
            if not year_str:
                return self._error('year parameter is required for yearly analysis.')
            try:
                year = int(year_str)
            except ValueError:
                return self._error('Invalid year format. Use a 4-digit year.')
            qs = FinancialRecord.objects.filter(date__year=year)
            return self._build_response(qs, 'yearly', year_str, include_monthly_trend=True)

        else:
            return self._error(
                'Invalid or missing type. Use daily, monthly, yearly, '
                'or provide start_date and end_date for custom range.'
            )

    # ----- helpers -----

    @staticmethod
    def _parse_date(date_str):
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _error(message):
        return Response({'detail': message}, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def _build_response(qs, analysis_type, label,
                        include_daily_trend=False, include_monthly_trend=False):
        # Core totals
        totals = qs.aggregate(
            total_income=Sum('amount', filter=Q(record_type='income')),
            total_expense=Sum('amount', filter=Q(record_type='expense')),
            record_count=Count('id'),
        )
        total_income = totals['total_income'] or 0
        total_expense = totals['total_expense'] or 0

        # Category breakdown
        category_breakdown = list(
            qs.values('category').annotate(
                total=Sum('amount'), count=Count('id'),
            ).order_by('-total')
        )

        # Top 5 expense categories
        top_expense_categories = list(
            qs.filter(record_type='expense')
            .values('category')
            .annotate(total=Sum('amount'))
            .order_by('-total')[:5]
        )

        data = {
            'analysis_type': analysis_type,
            'period': label,
            'total_income': total_income,
            'total_expense': total_expense,
            'net_balance': total_income - total_expense,
            'record_count': totals['record_count'],
            'category_breakdown': category_breakdown,
            'top_expense_categories': top_expense_categories,
        }

        # Optional daily trend
        if include_daily_trend:
            daily = list(
                qs.values('date')
                .annotate(
                    income=Sum('amount', filter=Q(record_type='income')),
                    expense=Sum('amount', filter=Q(record_type='expense')),
                )
                .order_by('date')
            )
            for entry in daily:
                entry['day'] = entry.pop('date').isoformat() if entry.get('date') else None
                entry['income'] = entry['income'] or 0
                entry['expense'] = entry['expense'] or 0
            data['daily_trend'] = daily

        # Optional monthly trend
        if include_monthly_trend:
            monthly = list(
                qs.annotate(month=TruncMonth('date'))
                .values('month')
                .annotate(
                    income=Sum('amount', filter=Q(record_type='income')),
                    expense=Sum('amount', filter=Q(record_type='expense')),
                )
                .order_by('month')
            )
            for entry in monthly:
                entry['month'] = entry['month'].strftime('%Y-%m') if entry['month'] else None
                entry['income'] = entry['income'] or 0
                entry['expense'] = entry['expense'] or 0
            data['monthly_trend'] = monthly

        return Response(data)

