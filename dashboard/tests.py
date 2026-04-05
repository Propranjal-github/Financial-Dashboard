from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from records.models import FinancialRecord

User = get_user_model()


class SummaryViewTestCase(APITestCase):
    """Tests for GET /api/v1/dashboard/summary/."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin', email='admin@summary.test', password='AdminPass123!', role='admin',
        )
        self.viewer = User.objects.create_user(
            username='viewer', email='viewer@summary.test', password='ViewerPass123!', role='viewer',
        )
        self.url = '/api/v1/dashboard/summary/'

        FinancialRecord.objects.create(
            created_by=self.admin, amount=Decimal('5000.00'),
            record_type='income', category='salary', date=date(2026, 4, 1),
        )
        FinancialRecord.objects.create(
            created_by=self.admin, amount=Decimal('1500.00'),
            record_type='expense', category='rent', date=date(2026, 4, 2),
        )
        FinancialRecord.objects.create(
            created_by=self.admin, amount=Decimal('800.00'),
            record_type='expense', category='utilities', date=date(2026, 4, 3),
        )

    def _auth(self, user):
        token = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')

    def test_unauthenticated_returns_401(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_viewer_can_access(self):
        self._auth(self.viewer)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_can_access(self):
        self._auth(self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_response_structure(self):
        self._auth(self.viewer)
        response = self.client.get(self.url)
        data = response.data
        self.assertIn('total_income', data)
        self.assertIn('total_expense', data)
        self.assertIn('net_balance', data)
        self.assertIn('record_count', data)
        self.assertIn('recent_records', data)

    def test_correct_totals(self):
        self._auth(self.viewer)
        response = self.client.get(self.url)
        data = response.data
        self.assertEqual(data['total_income'], Decimal('5000.00'))
        self.assertEqual(data['total_expense'], Decimal('2300.00'))
        self.assertEqual(data['net_balance'], Decimal('2700.00'))
        self.assertEqual(data['record_count'], 3)

    def test_recent_records_limited(self):
        self._auth(self.viewer)
        response = self.client.get(self.url)
        self.assertTrue(len(response.data['recent_records']) <= 5)

    def test_empty_database_returns_zeros(self):
        FinancialRecord.objects.all().delete()
        self._auth(self.viewer)
        response = self.client.get(self.url)
        self.assertEqual(response.data['total_income'], 0)
        self.assertEqual(response.data['total_expense'], 0)
        self.assertEqual(response.data['net_balance'], 0)
        self.assertEqual(response.data['record_count'], 0)

    def test_recent_records_fields(self):
        self._auth(self.viewer)
        response = self.client.get(self.url)
        record = response.data['recent_records'][0]
        for field in ('id', 'record_type', 'amount', 'category', 'date', 'status'):
            self.assertIn(field, record)


class AnalyticsViewTestCase(APITestCase):
    """Tests for GET /api/v1/dashboard/analytics/."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin', email='admin@anview.test', password='AdminPass123!', role='admin',
        )
        self.analyst = User.objects.create_user(
            username='analyst', email='analyst@anview.test', password='AnalystPass123!', role='analyst',
        )
        self.viewer = User.objects.create_user(
            username='viewer', email='viewer@anview.test', password='ViewerPass123!', role='viewer',
        )
        self.url = '/api/v1/dashboard/analytics/'

        FinancialRecord.objects.create(
            created_by=self.admin, amount=Decimal('3000.00'),
            record_type='income', category='salary', date=date(2026, 3, 1),
        )
        FinancialRecord.objects.create(
            created_by=self.admin, amount=Decimal('500.00'),
            record_type='expense', category='utilities', date=date(2026, 3, 15),
        )
        FinancialRecord.objects.create(
            created_by=self.admin, amount=Decimal('1000.00'),
            record_type='income', category='freelance', date=date(2026, 4, 1),
        )

    def _auth(self, user):
        token = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')

    def test_viewer_forbidden(self):
        self._auth(self.viewer)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_analyst_allowed(self):
        self._auth(self.analyst)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_allowed(self):
        self._auth(self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_response_structure(self):
        self._auth(self.analyst)
        response = self.client.get(self.url)
        data = response.data
        self.assertIn('category_breakdown', data)
        self.assertIn('type_distribution', data)
        self.assertIn('monthly_trends', data)

    def test_category_breakdown_correctness(self):
        self._auth(self.analyst)
        response = self.client.get(self.url)
        cats = {c['category']: c['total'] for c in response.data['category_breakdown']}
        self.assertEqual(cats['salary'], Decimal('3000.00'))
        self.assertEqual(cats['utilities'], Decimal('500.00'))
        self.assertEqual(cats['freelance'], Decimal('1000.00'))

    def test_type_distribution(self):
        self._auth(self.analyst)
        response = self.client.get(self.url)
        types = {t['record_type']: t for t in response.data['type_distribution']}
        self.assertEqual(types['income']['total'], Decimal('4000.00'))
        self.assertEqual(types['income']['count'], 2)
        self.assertEqual(types['expense']['total'], Decimal('500.00'))
        self.assertEqual(types['expense']['count'], 1)


class TimeAnalyticsTestCase(APITestCase):
    """Tests for the time-scoped analytics API endpoint."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin', email='admin@analytics.test', password='AdminPass123!', role='admin',
        )
        self.analyst = User.objects.create_user(
            username='analyst', email='analyst@analytics.test', password='AnalystPass123!', role='analyst',
        )
        self.viewer = User.objects.create_user(
            username='viewer', email='viewer@analytics.test', password='ViewerPass123!', role='viewer',
        )
        self.url = '/api/v1/dashboard/time-analytics/'

        # Create test records across dates
        FinancialRecord.objects.create(
            created_by=self.admin, amount=Decimal('1000.00'),
            record_type='income', category='salary', date=date(2026, 4, 5),
        )
        FinancialRecord.objects.create(
            created_by=self.admin, amount=Decimal('200.00'),
            record_type='expense', category='utilities', date=date(2026, 4, 5),
        )
        FinancialRecord.objects.create(
            created_by=self.admin, amount=Decimal('500.00'),
            record_type='income', category='freelance', date=date(2026, 4, 10),
        )
        FinancialRecord.objects.create(
            created_by=self.admin, amount=Decimal('300.00'),
            record_type='expense', category='marketing', date=date(2026, 3, 15),
        )
        FinancialRecord.objects.create(
            created_by=self.admin, amount=Decimal('800.00'),
            record_type='income', category='salary', date=date(2025, 12, 1),
        )

    def _auth(self, user):
        token = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')

    # ---- Role-based access ----

    def test_viewer_forbidden(self):
        self._auth(self.viewer)
        response = self.client.get(self.url, {'type': 'daily', 'date': '2026-04-05'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_analyst_allowed(self):
        self._auth(self.analyst)
        response = self.client.get(self.url, {'type': 'daily', 'date': '2026-04-05'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_allowed(self):
        self._auth(self.admin)
        response = self.client.get(self.url, {'type': 'daily', 'date': '2026-04-05'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_forbidden(self):
        response = self.client.get(self.url, {'type': 'daily', 'date': '2026-04-05'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ---- Daily analysis ----

    def test_daily_totals(self):
        self._auth(self.analyst)
        response = self.client.get(self.url, {'type': 'daily', 'date': '2026-04-05'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(data['analysis_type'], 'daily')
        self.assertEqual(data['period'], '2026-04-05')
        self.assertEqual(data['total_income'], Decimal('1000.00'))
        self.assertEqual(data['total_expense'], Decimal('200.00'))
        self.assertEqual(data['net_balance'], Decimal('800.00'))
        self.assertEqual(data['record_count'], 2)

    def test_daily_missing_date(self):
        self._auth(self.analyst)
        response = self.client.get(self.url, {'type': 'daily'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_daily_invalid_date(self):
        self._auth(self.analyst)
        response = self.client.get(self.url, {'type': 'daily', 'date': 'not-a-date'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ---- Monthly analysis ----

    def test_monthly_totals(self):
        self._auth(self.analyst)
        response = self.client.get(self.url, {'type': 'monthly', 'month': '2026-04'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(data['analysis_type'], 'monthly')
        self.assertEqual(data['total_income'], Decimal('1500.00'))
        self.assertEqual(data['total_expense'], Decimal('200.00'))
        self.assertEqual(data['record_count'], 3)
        self.assertIn('daily_trend', data)

    def test_monthly_missing_param(self):
        self._auth(self.analyst)
        response = self.client.get(self.url, {'type': 'monthly'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_monthly_invalid_format(self):
        self._auth(self.analyst)
        response = self.client.get(self.url, {'type': 'monthly', 'month': '2026/04'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ---- Yearly analysis ----

    def test_yearly_totals(self):
        self._auth(self.analyst)
        response = self.client.get(self.url, {'type': 'yearly', 'year': '2026'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(data['analysis_type'], 'yearly')
        self.assertEqual(data['total_income'], Decimal('1500.00'))
        self.assertEqual(data['total_expense'], Decimal('500.00'))
        self.assertEqual(data['record_count'], 4)
        self.assertIn('monthly_trend', data)

    def test_yearly_missing_param(self):
        self._auth(self.analyst)
        response = self.client.get(self.url, {'type': 'yearly'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_yearly_invalid_format(self):
        self._auth(self.analyst)
        response = self.client.get(self.url, {'type': 'yearly', 'year': 'abc'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ---- Custom range ----

    def test_custom_range(self):
        self._auth(self.analyst)
        response = self.client.get(
            self.url, {'start_date': '2026-03-01', 'end_date': '2026-04-30'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(data['analysis_type'], 'custom')
        self.assertEqual(data['total_income'], Decimal('1500.00'))
        self.assertEqual(data['total_expense'], Decimal('500.00'))
        self.assertEqual(data['record_count'], 4)
        self.assertIn('daily_trend', data)

    def test_custom_invalid_dates(self):
        self._auth(self.analyst)
        response = self.client.get(
            self.url, {'start_date': 'bad', 'end_date': 'bad'}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_custom_reversed_dates(self):
        self._auth(self.analyst)
        response = self.client.get(
            self.url, {'start_date': '2026-12-01', 'end_date': '2026-01-01'}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ---- Invalid type ----

    def test_invalid_type(self):
        self._auth(self.analyst)
        response = self.client.get(self.url, {'type': 'weekly'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_type_and_dates(self):
        self._auth(self.analyst)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ---- Category breakdown correctness ----

    def test_daily_category_breakdown(self):
        self._auth(self.analyst)
        response = self.client.get(self.url, {'type': 'daily', 'date': '2026-04-05'})
        cats = {c['category']: c['total'] for c in response.data['category_breakdown']}
        self.assertEqual(cats['salary'], Decimal('1000.00'))
        self.assertEqual(cats['utilities'], Decimal('200.00'))

    def test_top_expense_categories(self):
        self._auth(self.analyst)
        response = self.client.get(self.url, {'type': 'yearly', 'year': '2026'})
        top = response.data['top_expense_categories']
        self.assertTrue(len(top) <= 5)
        self.assertEqual(top[0]['category'], 'marketing')
