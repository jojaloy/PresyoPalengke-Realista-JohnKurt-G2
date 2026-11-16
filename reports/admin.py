from django.contrib import admin

from .models import Market, PriceReport, Product


@admin.register(Market)
class MarketAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'location')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name',)


@admin.register(PriceReport)
class PriceReportAdmin(admin.ModelAdmin):
    list_display = ('product', 'market', 'price', 'unit', 'date_observed', 'reporter')
    list_filter = ('market', 'product__category', 'unit')
    search_fields = ('product__name', 'market__name', 'reporter__username')
