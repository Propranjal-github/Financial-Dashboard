from django.contrib import admin

from .models import FinancialRecord


@admin.register(FinancialRecord)
class FinancialRecordAdmin(admin.ModelAdmin):
    list_display = ['id', 'record_type', 'amount', 'category', 'status', 'date', 'created_by']
    list_filter = ['record_type', 'status', 'category']
    search_fields = ['description', 'category']
    date_hierarchy = 'date'
    readonly_fields = ['created_at', 'updated_at']
