"""
Tests for tracker.middleware.LoginRequiredMiddleware (Hotfix 20.10.2026).

Every URL in the app must require a login, except the login pages
(/accounts/), the admin (own login), the external HR API (/api/, Api-Key)
and static files.
"""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import URLPattern, URLResolver, get_resolver, reverse

from .models import APIKey, Contract, Employee, Invoice, Project

User = get_user_model()

EXEMPT_PREFIXES = ('/accounts/', '/admin/', '/api/')

# Placeholder values for URL converters when enumerating all routes.
PLACEHOLDERS = {'int': '1', 'str': 'x', 'slug': 'x', 'path': 'x', 'uuid': '00000000-0000-0000-0000-000000000001'}


def all_app_paths():
    """Every concrete URL path of the project, with int/str placeholders filled in."""
    paths = []

    def walk(patterns, prefix=''):
        for p in patterns:
            if isinstance(p, URLResolver):
                walk(p.url_patterns, prefix + str(p.pattern))
            elif isinstance(p, URLPattern):
                route = prefix + str(p.pattern)
                if not hasattr(p.pattern, 'converters'):
                    continue  # regex pattern (admin internals) – skip
                for name, conv in p.pattern.converters.items():
                    route = route.replace('<%s:%s>' % (type(conv).__name__.replace('Converter', '').lower(), name),
                                          PLACEHOLDERS.get(type(conv).__name__.replace('Converter', '').lower(), '1'))
                    route = route.replace('<%s>' % name, '1')
                paths.append('/' + route)

    walk(get_resolver().url_patterns)
    return sorted(set(paths))


# Templates use {% static %}; the manifest storage needs collectstatic, which tests don't run.
@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class LoginRequiredMiddlewareTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='tester', password='secret-pw-123')
        Employee.objects.create(user=cls.user)
        cls.project = Project.objects.create(
            project_name='P', project_address='A', project_no='001', status='0',
        )
        cls.contract = Contract.objects.create(contract_name='C')
        cls.project.contract.add(cls.contract)
        cls.invoice = Invoice.objects.create(
            project=cls.project, contract=cls.contract, invoice_net=100.0,
            title='TEST-INV-1', amount_received=0,
        )
        cls.api_key = APIKey.objects.create(name='test')

    # ── anonymous access ──────────────────────────────────────────────────

    def test_every_app_url_requires_login_anonymously(self):
        paths = [p for p in all_app_paths() if not p.startswith(EXEMPT_PREFIXES)]
        self.assertGreater(len(paths), 40)
        for path in paths:
            for method in ('get', 'post'):
                with self.subTest(path=path, method=method):
                    resp = getattr(self.client, method)(path)
                    self.assertEqual(resp.status_code, 302)
                    self.assertTrue(resp['Location'].startswith(settings.LOGIN_URL),
                                    msg='%s redirected to %s' % (path, resp['Location']))

    def test_anonymous_fetch_and_htmx_requests_get_401_json(self):
        url = reverse('view_invoice', args=[self.invoice.id])
        for headers in ({'HTTP_HX_REQUEST': 'true'},
                        {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'},
                        {'HTTP_ACCEPT': 'application/json'}):
            with self.subTest(headers=headers):
                resp = self.client.get(url, **headers)
                self.assertEqual(resp.status_code, 401)
                self.assertEqual(resp.json(), {'error': 'Login erforderlich.'})

    def test_anonymous_record_payment_changes_nothing(self):
        url = reverse('record_payment', args=[self.invoice.id])
        resp = self.client.post(url, {'amount_received': '999', 'date_of_payment': '2026-10-20'})
        self.assertEqual(resp.status_code, 302)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.amount_received, 0)
        self.assertIsNone(self.invoice.date_of_payment)

    def test_anonymous_download_invoice_redirects_with_next(self):
        url = reverse('download_invoice', args=[self.invoice.id])
        resp = self.client.get(url)
        self.assertRedirects(resp, '%s?next=%s' % (settings.LOGIN_URL, url), fetch_redirect_response=False)

    # ── exemptions ────────────────────────────────────────────────────────

    def test_login_page_and_admin_login_reachable(self):
        self.assertEqual(self.client.get('/accounts/login/').status_code, 200)
        resp = self.client.get('/admin/')
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp['Location'].startswith('/admin/login/'))
        self.assertEqual(self.client.get('/admin/login/').status_code, 200)

    @override_settings(WHITENOISE_USE_FINDERS=True, WHITENOISE_AUTOREFRESH=True)
    def test_static_files_reachable(self):
        resp = Client().get(settings.STATIC_URL + 'css/output.css')  # fresh client → WhiteNoise re-inits
        self.assertEqual(resp.status_code, 200)

    def test_hr_api_uses_its_own_api_key_auth(self):
        url = reverse('api_employee_hours')
        params = {'username': self.user.username, 'from': '2026-10-01', 'to': '2026-10-31'}
        # no key → DRF 401, not a login redirect
        resp = self.client.get(url, params)
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp['WWW-Authenticate'], 'Api-Key realm="api"')
        # valid key → 200
        resp = self.client.get(url, params, HTTP_AUTHORIZATION='Api-Key ' + self.api_key.key)
        self.assertEqual(resp.status_code, 200)

    # ── logged in ─────────────────────────────────────────────────────────

    def test_logged_in_user_passes_through(self):
        self.client.force_login(self.user)
        for name, args in (('log_create_compact', []), ('projects', []),
                           ('dashboard', []), ('view_invoice', [self.invoice.id])):
            with self.subTest(view=name):
                self.assertEqual(self.client.get(reverse(name, args=args)).status_code, 200)

    def test_login_then_redirect_back_to_invoice(self):
        url = reverse('download_invoice', args=[self.invoice.id])
        resp = self.client.post('/accounts/login/',
                                {'login': 'tester', 'password': 'secret-pw-123', 'next': url})
        self.assertRedirects(resp, url, fetch_redirect_response=False)
