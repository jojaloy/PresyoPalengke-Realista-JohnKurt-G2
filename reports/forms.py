from datetime import timedelta

from django import forms
from django.utils import timezone

from .models import Market, PriceReport, Product

MAX_REPORT_AGE_DAYS = 7


class PriceReportForm(forms.ModelForm):
    class Meta:
        model = PriceReport
        fields = ('product', 'market', 'price', 'unit', 'date_observed', 'notes')
        widgets = {
            'date_observed': forms.DateInput(attrs={'type': 'date'}),
            'price': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        # Only active reference data can be picked (an edited report keeps its current choice).
        self.fields['product'].queryset = Product.objects.filter(is_active=True)
        self.fields['market'].queryset = Market.objects.filter(is_active=True)
        self.fields['product'].empty_label = '— choose a product —'
        self.fields['market'].empty_label = '— choose a market —'
        if not self.instance.pk:
            self.fields['date_observed'].initial = timezone.localdate()

    def clean_date_observed(self):
        day = self.cleaned_data['date_observed']
        today = timezone.localdate()
        if day > today:
            raise forms.ValidationError('The date cannot be in the future.')
        if day < today - timedelta(days=MAX_REPORT_AGE_DAYS):
            raise forms.ValidationError(
                f'Only prices seen in the last {MAX_REPORT_AGE_DAYS} days can be reported.')
        return day

    def clean_notes(self):
        return self.cleaned_data['notes'].strip()

    def clean(self):
        cleaned = super().clean()
        product, market, day = (cleaned.get(k) for k in ('product', 'market', 'date_observed'))
        if self.user and product and market and day:
            duplicates = PriceReport.objects.filter(
                reporter=self.user, product=product, market=market, date_observed=day)
            if self.instance.pk:
                duplicates = duplicates.exclude(pk=self.instance.pk)
            if duplicates.exists():
                raise forms.ValidationError(
                    f'You already reported {product} at {market} for that day. Edit that report instead.')
        return cleaned


class ReportFilterForm(forms.Form):
    q = forms.CharField(required=False, label='Product', widget=forms.TextInput(attrs={'placeholder': 'Search product'}))
    market = forms.ModelChoiceField(queryset=Market.objects.all(), required=False, empty_label='All markets')
