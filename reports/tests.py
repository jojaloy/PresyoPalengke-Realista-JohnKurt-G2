from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from accounts.tests import PW, make_user

from .models import Market, PriceReport, Product


def make_report(user, product, market, **kw):
    kw.setdefault('price', Decimal('50.00'))
    kw.setdefault('date_observed', timezone.localdate())
    return PriceReport.objects.create(reporter=user, product=product, market=market, **kw)


class ReportTestBase(TestCase):
    def setUp(self):
        self.product = Product.objects.create(name='Test Tomato', category='vegetables')
        self.product2 = Product.objects.create(name='Test Onion', category='vegetables')
        self.market = Market.objects.create(name='Test Market')
        self.shopper = make_user('shopper1', User.Role.SHOPPER)
        self.other = make_user('shopper2', User.Role.SHOPPER)
        self.vendor = make_user('vendor1', User.Role.VENDOR)
        self.admin = make_user('admin1', User.Role.ADMIN)

    def login(self, user):
        self.client.login(username=user.username, password=PW)

    def data(self, **kw):
        base = {'product': self.product.pk, 'market': self.market.pk, 'price': '55.50',
                'unit': 'kg', 'date_observed': timezone.localdate().isoformat(), 'notes': 'fresh'}
        base.update(kw)
        return base


class CreateTests(ReportTestBase):
    def test_shopper_creates_report_linked_to_self(self):
        self.login(self.shopper)
        r = self.client.post(reverse('reports:create'), self.data(), follow=True)
        report = PriceReport.objects.get()
        self.assertEqual(report.reporter, self.shopper)
        self.assertEqual(report.price, Decimal('55.50'))
        self.assertRedirects(r, reverse('reports:detail', args=[report.pk]))
        self.assertContains(r, 'saved')

    def test_requires_login(self):
        url = reverse('reports:create')
        self.assertRedirects(self.client.get(url), f"{reverse('accounts:login')}?next={url}")

    def test_vendor_and_admin_cannot_create(self):
        for user in (self.vendor, self.admin):
            self.login(user)
            self.assertEqual(self.client.get(reverse('reports:create')).status_code, 403)
            self.assertEqual(self.client.post(reverse('reports:create'), self.data()).status_code, 403)
        self.assertEqual(PriceReport.objects.count(), 0)

    def test_required_fields(self):
        self.login(self.shopper)
        r = self.client.post(reverse('reports:create'), {})
        self.assertContains(r, 'This field is required')
        self.assertContains(r, 'Could not save the report')
        self.assertEqual(PriceReport.objects.count(), 0)

    def test_price_must_be_positive(self):
        self.login(self.shopper)
        for bad in ('0', '-5', 'abc'):
            r = self.client.post(reverse('reports:create'), self.data(price=bad))
            self.assertEqual(PriceReport.objects.count(), 0, bad)
            self.assertEqual(r.status_code, 200)

    def test_price_upper_limit(self):
        self.login(self.shopper)
        self.client.post(reverse('reports:create'), self.data(price='10000.01'))
        self.assertEqual(PriceReport.objects.count(), 0)

    def test_future_date_rejected(self):
        self.login(self.shopper)
        tomorrow = (timezone.localdate() + timedelta(days=1)).isoformat()
        r = self.client.post(reverse('reports:create'), self.data(date_observed=tomorrow))
        self.assertContains(r, 'cannot be in the future')

    def test_old_date_rejected(self):
        self.login(self.shopper)
        old = (timezone.localdate() - timedelta(days=8)).isoformat()
        r = self.client.post(reverse('reports:create'), self.data(date_observed=old))
        self.assertContains(r, 'last 7 days')

    def test_duplicate_same_day_rejected(self):
        self.login(self.shopper)
        make_report(self.shopper, self.product, self.market)
        r = self.client.post(reverse('reports:create'), self.data())
        self.assertContains(r, 'already reported')
        self.assertEqual(PriceReport.objects.count(), 1)

    def test_inactive_market_not_selectable(self):
        self.market.is_active = False
        self.market.save()
        self.login(self.shopper)
        self.client.post(reverse('reports:create'), self.data())
        self.assertEqual(PriceReport.objects.count(), 0)


class ReadTests(ReportTestBase):
    def setUp(self):
        super().setUp()
        self.mine = make_report(self.shopper, self.product, self.market)
        self.theirs = make_report(self.other, self.product2, self.market)

    def test_shopper_list_shows_only_own(self):
        self.login(self.shopper)
        r = self.client.get(reverse('reports:list'))
        self.assertContains(r, 'Test Tomato')
        self.assertNotContains(r, 'Test Onion')

    def test_shopper_cannot_open_others_report(self):
        self.login(self.shopper)
        self.assertEqual(self.client.get(reverse('reports:detail', args=[self.theirs.pk])).status_code, 404)

    def test_vendor_and_admin_see_all(self):
        for user in (self.vendor, self.admin):
            self.login(user)
            r = self.client.get(reverse('reports:list'))
            self.assertContains(r, 'Test Tomato')
            self.assertContains(r, 'Test Onion')

    def test_vendor_detail_is_read_only(self):
        self.login(self.vendor)
        r = self.client.get(reverse('reports:detail', args=[self.mine.pk]))
        self.assertNotContains(r, reverse('reports:update', args=[self.mine.pk]))
        self.assertNotContains(r, reverse('reports:delete', args=[self.mine.pk]))

    def test_filter_by_product_and_market(self):
        other_market = Market.objects.create(name='Other Market')
        make_report(self.shopper, self.product2, other_market)
        self.login(self.admin)
        r = self.client.get(reverse('reports:list'), {'q': 'onion', 'market': other_market.pk})
        self.assertEqual(len(r.context['page'].object_list), 1)

    def test_logged_out_redirected(self):
        url = reverse('reports:list')
        self.assertRedirects(self.client.get(url), f"{reverse('accounts:login')}?next={url}")


class UpdateDeleteTests(ReportTestBase):
    def setUp(self):
        super().setUp()
        self.report = make_report(self.shopper, self.product, self.market)

    def test_owner_updates(self):
        self.login(self.shopper)
        r = self.client.post(reverse('reports:update', args=[self.report.pk]), self.data(price='70.00'), follow=True)
        self.report.refresh_from_db()
        self.assertEqual(self.report.price, Decimal('70.00'))
        self.assertContains(r, 'updated')

    def test_update_keeps_own_row_out_of_duplicate_check(self):
        self.login(self.shopper)
        self.client.post(reverse('reports:update', args=[self.report.pk]), self.data(notes='changed'))
        self.report.refresh_from_db()
        self.assertEqual(self.report.notes, 'changed')

    def test_update_validation_error_keeps_old_value(self):
        self.login(self.shopper)
        self.client.post(reverse('reports:update', args=[self.report.pk]), self.data(price='-1'))
        self.report.refresh_from_db()
        self.assertEqual(self.report.price, Decimal('50.00'))

    def test_other_shopper_cannot_update_or_delete(self):
        self.login(self.other)
        self.assertEqual(self.client.post(reverse('reports:update', args=[self.report.pk]), self.data()).status_code, 403)
        self.assertEqual(self.client.post(reverse('reports:delete', args=[self.report.pk])).status_code, 403)
        self.assertTrue(PriceReport.objects.filter(pk=self.report.pk).exists())

    def test_vendor_cannot_update_or_delete(self):
        self.login(self.vendor)
        self.assertEqual(self.client.post(reverse('reports:update', args=[self.report.pk]), self.data()).status_code, 403)
        self.assertEqual(self.client.post(reverse('reports:delete', args=[self.report.pk])).status_code, 403)

    def test_admin_cannot_edit_but_can_delete(self):
        self.login(self.admin)
        self.assertEqual(self.client.get(reverse('reports:update', args=[self.report.pk])).status_code, 403)
        r = self.client.post(reverse('reports:delete', args=[self.report.pk]), follow=True)
        self.assertContains(r, 'was deleted')
        self.assertFalse(PriceReport.objects.exists())

    def test_owner_deletes_after_confirm(self):
        self.login(self.shopper)
        self.assertContains(self.client.get(reverse('reports:delete', args=[self.report.pk])), 'Delete this report')
        self.assertTrue(PriceReport.objects.exists())  # GET does not delete
        self.client.post(reverse('reports:delete', args=[self.report.pk]))
        self.assertFalse(PriceReport.objects.exists())


class DashboardTests(ReportTestBase):
    def test_dashboards_show_reports_and_nav(self):
        make_report(self.shopper, self.product, self.market)
        self.login(self.shopper)
        self.assertContains(self.client.get(reverse('accounts:shopper_dashboard')), 'Test Tomato')
        self.login(self.vendor)
        self.assertContains(self.client.get(reverse('accounts:vendor_dashboard')), 'Test Tomato')
        self.login(self.admin)
        r = self.client.get(reverse('accounts:admin_dashboard'))
        self.assertContains(r, 'Test Tomato')
        self.assertEqual(r.context['report_count'], 1)

    def test_shopper_sees_report_link_vendor_does_not_see_create(self):
        self.login(self.vendor)
        self.assertNotContains(self.client.get(reverse('accounts:vendor_dashboard')), reverse('reports:create'))


class ModelTests(ReportTestBase):
    def test_db_unique_constraint(self):
        from django.db import IntegrityError, transaction
        make_report(self.shopper, self.product, self.market)
        with self.assertRaises(IntegrityError), transaction.atomic():
            make_report(self.shopper, self.product, self.market)

    def test_product_in_use_is_protected(self):
        from django.db.models import ProtectedError
        make_report(self.shopper, self.product, self.market)
        with self.assertRaises(ProtectedError):
            self.product.delete()

    def test_deleting_user_removes_reports(self):
        make_report(self.shopper, self.product, self.market)
        self.shopper.delete()
        self.assertEqual(PriceReport.objects.count(), 0)

    def test_seed_data_present_after_migrate(self):
        # Seeded by migration 0002 (test DB is built by running migrations).
        self.assertTrue(Market.objects.filter(name='Carbon Market').exists())
