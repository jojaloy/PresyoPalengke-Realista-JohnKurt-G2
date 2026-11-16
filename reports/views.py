from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.decorators import role_required
from accounts.models import User

from .forms import PriceReportForm, ReportFilterForm
from .models import PriceReport

ALL_ROLES = (User.Role.SHOPPER, User.Role.VENDOR, User.Role.ADMIN)


def visible_reports(user):
    """Shoppers see only their own reports; Vendors and Admins can see all (read-only for Vendors)."""
    qs = PriceReport.objects.select_related('product', 'market', 'reporter')
    if user.role == User.Role.SHOPPER:
        qs = qs.filter(reporter=user)
    return qs


def get_own_report_or_403(user, pk):
    """Shoppers may change only their own report; Admins may remove any report (moderation)."""
    report = get_object_or_404(PriceReport.objects.select_related('product', 'market', 'reporter'), pk=pk)
    if report.reporter_id != user.pk and user.role != User.Role.ADMIN:
        raise PermissionDenied
    return report


@role_required(*ALL_ROLES)
def report_list(request):
    reports = visible_reports(request.user)
    form = ReportFilterForm(request.GET or None)
    if form.is_valid():
        if form.cleaned_data['q']:
            reports = reports.filter(product__name__icontains=form.cleaned_data['q'])
        if form.cleaned_data['market']:
            reports = reports.filter(market=form.cleaned_data['market'])
    page = Paginator(reports, 10).get_page(request.GET.get('page'))
    query = request.GET.copy()
    query.pop('page', None)
    return render(request, 'reports/report_list.html', {
        'page': page, 'filter_form': form, 'querystring': query.urlencode(),
        'show_reporter': request.user.role != User.Role.SHOPPER,
    })


@role_required(*ALL_ROLES)
def report_detail(request, pk):
    report = get_object_or_404(visible_reports(request.user), pk=pk)
    return render(request, 'reports/report_detail.html', {
        'report': report,
        'can_edit': report.reporter_id == request.user.pk and request.user.role == User.Role.SHOPPER,
        'can_delete': report.reporter_id == request.user.pk or request.user.role == User.Role.ADMIN,
    })


@role_required(User.Role.SHOPPER)
def report_create(request):
    form = PriceReportForm(request.POST if request.method == 'POST' else None, user=request.user)
    if request.method == 'POST':
        if form.is_valid():
            report = form.save(commit=False)
            report.reporter = request.user
            report.save()
            messages.success(request, f'Price report for {report.product} saved. Salamat!')
            return redirect('reports:detail', pk=report.pk)
        messages.error(request, 'Could not save the report. Please fix the errors below.')
    return render(request, 'reports/report_form.html', {'form': form, 'is_edit': False})


@role_required(User.Role.SHOPPER)
def report_update(request, pk):
    report = get_object_or_404(PriceReport, pk=pk)
    if report.reporter_id != request.user.pk:
        raise PermissionDenied
    form = PriceReportForm(
        request.POST if request.method == 'POST' else None, instance=report, user=request.user)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'Price report updated.')
            return redirect('reports:detail', pk=report.pk)
        messages.error(request, 'Could not update the report. Please fix the errors below.')
    return render(request, 'reports/report_form.html', {'form': form, 'is_edit': True, 'report': report})


@role_required(User.Role.SHOPPER, User.Role.ADMIN)
def report_delete(request, pk):
    report = get_own_report_or_403(request.user, pk)
    if request.method == 'POST':
        label = f'{report.product} at {report.market}'
        report.delete()
        messages.success(request, f'Price report for {label} was deleted.')
        return redirect('reports:list')
    return render(request, 'reports/report_confirm_delete.html', {'report': report})
