from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from reports.models import PriceReport

from .decorators import role_required
from .forms import LoginForm, ProfileForm, RegisterForm
from .models import User

DASHBOARD_BY_ROLE = {
    User.Role.SHOPPER: 'accounts:shopper_dashboard',
    User.Role.VENDOR: 'accounts:vendor_dashboard',
    User.Role.ADMIN: 'accounts:admin_dashboard',
}


def home(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    return redirect('accounts:login')


def register(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    form = RegisterForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome, {user.first_name}! Your account has been created.')
            return redirect('accounts:dashboard')
        messages.error(request, 'Registration failed. Please fix the errors below.')
    return render(request, 'accounts/register.html', {'form': form})


class UserLoginView(LoginView):
    template_name = 'accounts/login.html'
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        messages.success(self.request, f'Welcome back, {form.get_user().first_name or form.get_user().username}!')
        return super().form_valid(form)

    def get_success_url(self):
        # Honour ?next= when safe, otherwise go to the role dashboard.
        return self.get_redirect_url() or reverse(DASHBOARD_BY_ROLE[self.request.user.role])


@require_POST
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('accounts:login')


@login_required
def dashboard(request):
    """Send each user to the dashboard for their role."""
    return redirect(DASHBOARD_BY_ROLE[request.user.role])


@role_required(User.Role.SHOPPER)
def shopper_dashboard(request):
    mine = PriceReport.objects.filter(reporter=request.user).select_related('product', 'market')
    return render(request, 'dashboards/shopper.html', {
        'my_report_count': mine.count(),
        'my_recent_reports': mine[:5],
    })


@role_required(User.Role.VENDOR)
def vendor_dashboard(request):
    reports = PriceReport.objects.select_related('product', 'market')
    return render(request, 'dashboards/vendor.html', {
        'report_count': reports.count(),
        'recent_reports': reports[:5],
    })


@role_required(User.Role.ADMIN)
def admin_dashboard(request):
    context = {
        'total_users': User.objects.count(),
        'shopper_count': User.objects.filter(role=User.Role.SHOPPER).count(),
        'vendor_count': User.objects.filter(role=User.Role.VENDOR).count(),
        'recent_users': User.objects.order_by('-date_joined')[:10],
        'report_count': PriceReport.objects.count(),
        'recent_reports': PriceReport.objects.select_related('product', 'market', 'reporter')[:5],
    }
    return render(request, 'dashboards/admin.html', context)


@login_required
def profile(request):
    # Always the logged-in user's own record; no user id in the URL.
    return render(request, 'accounts/profile.html', {'profile_user': request.user})


@login_required
def profile_edit(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
    else:
        form = ProfileForm(instance=request.user)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('accounts:profile')
        messages.error(request, 'Could not update profile. Please fix the errors below.')
    return render(request, 'accounts/profile_edit.html', {'form': form})
