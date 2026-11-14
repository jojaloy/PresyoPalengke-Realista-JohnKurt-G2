from django.test import TestCase
from django.urls import reverse

from .models import User

PW = 'Str0ng!Pass#123'


def make_user(username, role, email=None, **kw):
    return User.objects.create_user(
        username=username, password=PW, role=role,
        email=email or f'{username}@example.com', first_name=username.title(), **kw)


class RegistrationTests(TestCase):
    data = {'username': 'juan', 'first_name': 'Juan', 'last_name': 'Cruz',
            'email': 'juan@example.com', 'role': 'shopper',
            'password1': PW, 'password2': PW}

    def test_success_hashes_password_and_logs_in(self):
        r = self.client.post(reverse('accounts:register'), self.data, follow=True)
        u = User.objects.get(username='juan')
        self.assertNotEqual(u.password, PW)
        self.assertTrue(u.password.startswith(('pbkdf2_', 'argon2', 'scrypt')))
        self.assertRedirects(r, reverse('accounts:shopper_dashboard'))
        self.assertContains(r, 'account has been created')

    def test_vendor_role(self):
        self.client.post(reverse('accounts:register'), {**self.data, 'role': 'vendor'})
        self.assertEqual(User.objects.get(username='juan').role, 'vendor')

    def test_cannot_self_register_as_admin(self):
        r = self.client.post(reverse('accounts:register'), {**self.data, 'role': 'admin'})
        self.assertFalse(User.objects.filter(username='juan').exists())
        self.assertContains(r, 'Registration failed')

    def test_password_mismatch(self):
        r = self.client.post(reverse('accounts:register'), {**self.data, 'password2': 'nope'})
        self.assertFalse(User.objects.exists())
        self.assertContains(r, "didn")  # "didn't match"

    def test_invalid_email(self):
        r = self.client.post(reverse('accounts:register'), {**self.data, 'email': 'bad'})
        self.assertFalse(User.objects.exists())
        self.assertContains(r, 'valid email')

    def test_duplicate_email_case_insensitive(self):
        make_user('a', 'shopper', email='juan@example.com')
        r = self.client.post(reverse('accounts:register'), {**self.data, 'email': 'JUAN@example.com'})
        self.assertContains(r, 'already exists')

    def test_duplicate_username(self):
        make_user('juan', 'shopper')
        r = self.client.post(reverse('accounts:register'), self.data)
        self.assertEqual(User.objects.filter(username='juan').count(), 1)
        self.assertContains(r, 'already exists')

    def test_required_fields(self):
        r = self.client.post(reverse('accounts:register'), {})
        self.assertContains(r, 'This field is required')


class AuthTests(TestCase):
    def setUp(self):
        self.shopper = make_user('shop', 'shopper')
        self.vendor = make_user('vend', 'vendor')

    def test_login_redirects_by_role(self):
        r = self.client.post(reverse('accounts:login'), {'username': 'shop', 'password': PW})
        self.assertRedirects(r, reverse('accounts:shopper_dashboard'))
        self.client.logout()
        r = self.client.post(reverse('accounts:login'), {'username': 'vend', 'password': PW})
        self.assertRedirects(r, reverse('accounts:vendor_dashboard'))

    def test_invalid_login_message(self):
        r = self.client.post(reverse('accounts:login'), {'username': 'shop', 'password': 'wrong'})
        self.assertContains(r, 'Invalid username or password')

    def test_logout_ends_session(self):
        self.client.login(username='shop', password=PW)
        self.client.post(reverse('accounts:logout'))
        r = self.client.get(reverse('accounts:profile'))
        self.assertEqual(r.status_code, 302)

    def test_logout_requires_post(self):
        self.client.login(username='shop', password=PW)
        self.assertEqual(self.client.get(reverse('accounts:logout')).status_code, 405)

    def test_logged_out_redirected_to_login(self):
        for name in ('profile', 'profile_edit', 'dashboard', 'shopper_dashboard',
                     'vendor_dashboard', 'admin_dashboard'):
            r = self.client.get(reverse(f'accounts:{name}'))
            self.assertEqual(r.status_code, 302, name)
            self.assertIn(reverse('accounts:login'), r['Location'], name)


class RoleAccessTests(TestCase):
    def setUp(self):
        self.shopper = make_user('shop', 'shopper')
        self.vendor = make_user('vend', 'vendor')
        self.admin = User.objects.create_superuser('boss', 'boss@example.com', PW)

    def test_admin_superuser_gets_admin_role(self):
        self.assertEqual(self.admin.role, 'admin')

    def test_each_role_sees_only_own_dashboard(self):
        urls = {'shopper': 'accounts:shopper_dashboard', 'vendor': 'accounts:vendor_dashboard',
                'admin': 'accounts:admin_dashboard'}
        users = {'shopper': 'shop', 'vendor': 'vend', 'admin': 'boss'}
        for role, uname in users.items():
            self.client.login(username=uname, password=PW)
            for other, url in urls.items():
                code = self.client.get(reverse(url)).status_code
                self.assertEqual(code, 200 if other == role else 403, f'{role}->{other}')
            self.client.logout()


class ProfileTests(TestCase):
    def setUp(self):
        self.a = make_user('a', 'shopper')
        self.b = make_user('b', 'vendor')
        self.client.login(username='a', password=PW)

    def test_view_own_profile_only(self):
        r = self.client.get(reverse('accounts:profile'))
        self.assertContains(r, 'a@example.com')
        self.assertNotContains(r, 'b@example.com')

    def test_update_profile(self):
        r = self.client.post(reverse('accounts:profile_edit'), {
            'first_name': 'New', 'last_name': 'Name', 'email': 'new@example.com',
            'contact_number': '0917 123 4567', 'preferred_markets': 'Carbon'}, follow=True)
        self.a.refresh_from_db()
        self.assertEqual((self.a.first_name, self.a.email, self.a.contact_number),
                         ('New', 'new@example.com', '09171234567'))
        self.assertContains(r, 'profile has been updated')

    def test_cannot_use_other_users_email(self):
        r = self.client.post(reverse('accounts:profile_edit'), {
            'first_name': 'A', 'last_name': 'A', 'email': 'b@example.com'})
        self.assertContains(r, 'already used')

    def test_bad_phone_rejected(self):
        r = self.client.post(reverse('accounts:profile_edit'), {
            'first_name': 'A', 'last_name': 'A', 'email': 'a@example.com', 'contact_number': '123'})
        self.assertContains(r, 'valid PH number')

    def test_cannot_change_role_via_profile(self):
        self.client.post(reverse('accounts:profile_edit'), {
            'first_name': 'A', 'last_name': 'A', 'email': 'a@example.com', 'role': 'admin'})
        self.a.refresh_from_db()
        self.assertEqual(self.a.role, 'shopper')
