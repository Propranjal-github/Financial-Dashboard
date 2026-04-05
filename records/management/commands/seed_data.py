import random
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from records.models import FinancialRecord

User = get_user_model()

CATEGORIES_INCOME = ['salary', 'freelance', 'investments', 'consulting', 'bonus']
CATEGORIES_EXPENSE = ['utilities', 'marketing', 'office supplies', 'travel', 'software', 'rent', 'food', 'insurance']


class Command(BaseCommand):
    help = 'Seed database with sample users and financial records'

    def handle(self, *args, **options):
        # Create users (skip if they already exist)
        users = {}
        user_data = [
            ('admin_user', 'admin@finance.com', 'Admin@123!', 'admin'),
            ('analyst_user', 'analyst@finance.com', 'Analyst@123!', 'analyst'),
            ('viewer_user', 'viewer@finance.com', 'Viewer@123!', 'viewer'),
        ]
        for username, email, password, role in user_data:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={'email': email, 'role': role},
            )
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(self.style.SUCCESS(f'  Created {role}: {username} / {password}'))
            else:
                self.stdout.write(f'  User already exists: {username}')
            users[role] = user

        admin = users['admin']

        # Create financial records
        if FinancialRecord.objects.exists():
            self.stdout.write(self.style.WARNING('\nRecords already exist. Skipping record creation.'))
            self.stdout.write(self.style.WARNING('To re-seed, delete existing records first.'))
            return

        records = []
        today = date.today()

        # Generate records for the past 6 months
        for i in range(60):
            record_date = today - timedelta(days=random.randint(0, 180))
            is_income = random.random() < 0.4  # 40% income, 60% expense

            if is_income:
                category = random.choice(CATEGORIES_INCOME)
                amount = Decimal(random.randint(500, 10000)) + Decimal(random.randint(0, 99)) / 100
            else:
                category = random.choice(CATEGORIES_EXPENSE)
                amount = Decimal(random.randint(50, 3000)) + Decimal(random.randint(0, 99)) / 100

            records.append(FinancialRecord(
                created_by=admin,
                amount=amount,
                record_type='income' if is_income else 'expense',
                category=category,
                date=record_date,
                description=f'Sample {category} record',
                status=random.choice(['pending', 'approved', 'approved', 'approved', 'rejected']),
            ))

        FinancialRecord.objects.bulk_create(records)
        self.stdout.write(self.style.SUCCESS(f'\n  Created {len(records)} financial records.'))

        self.stdout.write(self.style.SUCCESS('\nDone! You can now log in with:'))
        self.stdout.write('  Admin:   admin_user / Admin@123!')
        self.stdout.write('  Analyst: analyst_user / Analyst@123!')
        self.stdout.write('  Viewer:  viewer_user / Viewer@123!')
