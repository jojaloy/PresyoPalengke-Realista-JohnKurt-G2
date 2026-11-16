from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import User
from reports.models import Market, PriceReport, Product

TEST_PASSWORD = 'PalengkeTest#2026'


class Command(BaseCommand):
    help = 'Create one test account per role (and a few sample price reports). Safe to re-run.'

    def handle(self, *args, **options):
        accounts = [
            ('admin_test', 'admin', 'Ana', 'Admin'),
            ('vendor_test', 'vendor', 'Vic', 'Vendor'),
            ('shopper_test', 'shopper', 'Sam', 'Shopper'),
        ]
        users = {}
        for username, role, first, last in accounts:
            user, created = User.objects.get_or_create(username=username, defaults={
                'email': f'{username}@example.com', 'role': role,
                'first_name': first, 'last_name': last,
                'is_staff': role == 'admin', 'is_superuser': role == 'admin'})
            user.set_password(TEST_PASSWORD)
            user.save()
            users[role] = user
            self.stdout.write(f'{"Created" if created else "Updated"} {username}')

        today = timezone.localdate()
        samples = [('Tomato', 'Carbon Market', '60.00', 'kg', 0), ('Bangus', 'Pasil Fish Market', '220.00', 'kg', 1),
                   ('Egg (medium)', 'Bulacao Market', '9.50', 'pc', 2)]
        for product, market, price, unit, days_ago in samples:
            PriceReport.objects.get_or_create(
                reporter=users['shopper'], product=Product.objects.get(name=product),
                market=Market.objects.get(name=market), date_observed=today - timedelta(days=days_ago),
                defaults={'price': Decimal(price), 'unit': unit})
        self.stdout.write(self.style.SUCCESS(f'Done. Password for all test accounts: {TEST_PASSWORD}'))
