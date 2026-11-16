from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Market(models.Model):
    """A public market where prices are observed (reference data, managed by Admin)."""

    name = models.CharField(max_length=100, unique=True)
    location = models.CharField(max_length=150, blank=True, help_text='Barangay / area, e.g. Pasil, Cebu City.')
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    """A palengke item whose price can be reported (reference data, managed by Admin)."""

    class Category(models.TextChoices):
        VEGETABLES = 'vegetables', 'Vegetables'
        FRUITS = 'fruits', 'Fruits'
        MEAT = 'meat', 'Meat & Poultry'
        FISH = 'fish', 'Fish & Seafood'
        GRAINS = 'grains', 'Rice & Grains'
        OTHER = 'other', 'Other'

    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.OTHER)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class PriceReport(models.Model):
    """One price observation submitted by a Shopper (the core feature record)."""

    class Unit(models.TextChoices):
        KILO = 'kg', 'per kilo'
        PIECE = 'pc', 'per piece'
        BUNCH = 'bunch', 'per bunch'
        LITER = 'liter', 'per liter'
        PACK = 'pack', 'per pack'

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='price_reports')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='price_reports')
    market = models.ForeignKey(Market, on_delete=models.PROTECT, related_name='price_reports')
    price = models.DecimalField(
        max_digits=8, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01')), MaxValueValidator(Decimal('10000'))],
        help_text='Price in pesos (₱).',
    )
    unit = models.CharField(max_length=10, choices=Unit.choices, default=Unit.KILO)
    date_observed = models.DateField(help_text='The day you saw this price.')
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_observed', '-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['reporter', 'product', 'market', 'date_observed'],
                name='unique_report_per_user_product_market_day'),
            models.CheckConstraint(condition=models.Q(price__gt=0), name='price_report_price_positive'),
        ]

    def __str__(self):
        return f'{self.product} @ {self.market}: ₱{self.price}/{self.unit}'
