from django.conf import settings
from django.db import models


class FinancialRecord(models.Model):
    """
    A financial record (transaction entry) in the system.

    Visibility: Records are organization-scoped (global). All authenticated users
    can view all records. Only admins can create, update, or delete records.
    The `created_by` field tracks who created the record for audit purposes.
    """

    class RecordType(models.TextChoices):
        INCOME = 'income', 'Income'
        EXPENSE = 'expense', 'Expense'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='financial_records',
        help_text='User who created this record.',
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text='Transaction amount (must be positive).',
    )
    record_type = models.CharField(
        max_length=7,
        choices=RecordType.choices,
        help_text='income or expense.',
    )
    category = models.CharField(
        max_length=50,
        help_text='Category label, e.g. salary, utilities, marketing.',
    )
    date = models.DateField(
        help_text='Date of the transaction.',
    )
    description = models.TextField(
        blank=True,
        default='',
        help_text='Optional notes or description.',
    )
    status = models.CharField(
        max_length=8,
        choices=Status.choices,
        default=Status.PENDING,
        help_text='Record approval status.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f'{self.get_record_type_display()} — {self.amount} ({self.category})'
