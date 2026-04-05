from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class FinancialRecordCRUDTestCase(APITestCase):
    """Tests for FinancialRecord CRUD and role-based access."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin', email='admin@example.com', password='AdminPass123!', role='admin',
        )
        self.viewer = User.objects.create_user(
            username='viewer', email='viewer@example.com', password='ViewerPass123!', role='viewer',
        )
        self.analyst = User.objects.create_user(
            username='analyst', email='analyst@example.com', password='AnalystPass123!', role='analyst',
        )
        self.records_url = '/api/v1/records/'
        self.record_data = {
            'amount': '1500.00',
            'record_type': 'income',
            'category': 'salary',
            'date': '2026-04-01',
            'description': 'Monthly salary',
            'status': 'approved',
        }

    # ---- Create ----

    def test_admin_can_create_record(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(self.records_url, self.record_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['category'], 'salary')

    def test_viewer_cannot_create_record(self):
        self.client.force_authenticate(user=self.viewer)
        response = self.client.post(self.records_url, self.record_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_analyst_cannot_create_record(self):
        self.client.force_authenticate(user=self.analyst)
        response = self.client.post(self.records_url, self.record_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ---- Read ----

    def test_viewer_can_list_records(self):
        self.client.force_authenticate(user=self.admin)
        self.client.post(self.records_url, self.record_data)
        self.client.force_authenticate(user=self.viewer)
        response = self.client.get(self.records_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_analyst_can_list_records(self):
        self.client.force_authenticate(user=self.admin)
        self.client.post(self.records_url, self.record_data)
        self.client.force_authenticate(user=self.analyst)
        response = self.client.get(self.records_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_unauthenticated_cannot_access(self):
        response = self.client.get(self.records_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ---- Update ----

    def test_admin_can_update_record(self):
        self.client.force_authenticate(user=self.admin)
        create_resp = self.client.post(self.records_url, self.record_data)
        record_id = create_resp.data['id']
        response = self.client.patch(
            f'{self.records_url}{record_id}/',
            {'amount': '2000.00'},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(response.data['amount']), Decimal('2000.00'))

    def test_viewer_cannot_update_record(self):
        self.client.force_authenticate(user=self.admin)
        create_resp = self.client.post(self.records_url, self.record_data)
        record_id = create_resp.data['id']
        self.client.force_authenticate(user=self.viewer)
        response = self.client.patch(
            f'{self.records_url}{record_id}/',
            {'amount': '9999.00'},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ---- Delete ----

    def test_admin_can_delete_record(self):
        self.client.force_authenticate(user=self.admin)
        create_resp = self.client.post(self.records_url, self.record_data)
        record_id = create_resp.data['id']
        response = self.client.delete(f'{self.records_url}{record_id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_viewer_cannot_delete_record(self):
        self.client.force_authenticate(user=self.admin)
        create_resp = self.client.post(self.records_url, self.record_data)
        record_id = create_resp.data['id']
        self.client.force_authenticate(user=self.viewer)
        response = self.client.delete(f'{self.records_url}{record_id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ---- Validation ----

    def test_negative_amount_rejected(self):
        self.client.force_authenticate(user=self.admin)
        data = {**self.record_data, 'amount': '-100.00'}
        response = self.client.post(self.records_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_record_type_rejected(self):
        self.client.force_authenticate(user=self.admin)
        data = {**self.record_data, 'record_type': 'refund'}
        response = self.client.post(self.records_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_required_fields(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(self.records_url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ---- Filtering ----

    def test_filter_by_record_type(self):
        self.client.force_authenticate(user=self.admin)
        self.client.post(self.records_url, self.record_data)
        expense_data = {**self.record_data, 'record_type': 'expense', 'category': 'rent'}
        self.client.post(self.records_url, expense_data)
        response = self.client.get(f'{self.records_url}?record_type=income')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_filter_by_date_range(self):
        self.client.force_authenticate(user=self.admin)
        self.client.post(self.records_url, self.record_data)
        response = self.client.get(
            f'{self.records_url}?date_from=2026-04-01&date_to=2026-04-30'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
