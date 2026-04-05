from rest_framework import serializers

from .models import FinancialRecord


class FinancialRecordSerializer(serializers.ModelSerializer):
    """
    Serializer for FinancialRecord CRUD.
    `created_by` is auto-set from the authenticated user on creation.
    """

    created_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = FinancialRecord
        fields = [
            'id',
            'created_by',
            'amount',
            'record_type',
            'category',
            'date',
            'description',
            'status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('Amount must be a positive number.')
        return value
