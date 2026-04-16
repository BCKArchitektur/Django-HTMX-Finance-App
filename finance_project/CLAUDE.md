# finance_project/ — Settings & Deployment Context

## Settings Notes (finance_project/settings.py)

### Locale / i18n — Watch the Duplicate Block!

The file has **two separate locale blocks** that conflict:

- **Lines 9–26** (top of file): Set correct German locale:
  ```python
  LANGUAGE_CODE = 'de'
  TIME_ZONE = 'Europe/Berlin'
  USE_L10N = True
  USE_I18N = True
  USE_THOUSAND_SEPARATOR = True
  DECIMAL_SEPARATOR = ','
  THOUSAND_SEPARATOR = '.'
  NUMBER_GROUPING = 3
  ```

- **Lines 140–146** (Django-generated boilerplate): Override with wrong values:
  ```python
  LANGUAGE_CODE = "en-us"   # WRONG — overrides German above
  TIME_ZONE = "UTC"          # WRONG — overrides Berlin above
  USE_I18N = True
  USE_TZ = True
  ```

The duplicate block means `LANGUAGE_CODE` and `TIME_ZONE` resolve to `en-us` / `UTC` at runtime, but the format settings (`DECIMAL_SEPARATOR`, etc.) at the top do apply correctly. This needs consolidation into one block.

### Key Settings at a Glance

```python
AUTH_USER_MODEL = 'tracker.User'          # Custom user model
LOGIN_REDIRECT_URL = 'log_create_compact' # After login → time logging page
SITE_ID = 1                               # Required by django-allauth

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'   # Target for collectstatic
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'          # EPHEMERAL on Heroku — see note below
```

### Installed Apps Order (matters!)
`jazzmin` must come **before** `django.contrib.admin` in `INSTALLED_APPS` — it overrides admin templates. Current order is correct; do not reorder.

### RotatingFileHandler Import
`from logging.handlers import RotatingFileHandler` is imported on line 3 but `LOGGING` is never configured. The import is unused until `LOGGING` dict is added. Do not remove the import — it will be used by the logging configuration.

---

## Heroku Deployment

### Required Files Checklist
- [x] `Procfile` — `web: gunicorn finance_project.wsgi --workers 4 --timeout 120` + `release: python manage.py migrate`
- [x] `runtime.txt` — `python-3.13.x` (pins exact Python version)
- [x] `.env.example` — documents all required environment variables
- [ ] `django.contrib.sites` — commented out in INSTALLED_APPS; allauth needs `SITE_ID=1` and a matching Site DB record

### First-Deploy Steps
After first deploy to Heroku, create the allauth Site record:
```bash
heroku run python manage.py shell -c "
from django.contrib.sites.models import Site
Site.objects.get_or_create(id=1, defaults={'domain': 'bck-f86a70e697db.herokuapp.com', 'name': 'BCK Finance'})
"
```

### Build Process on Heroku
1. Heroku detects Python → installs `requirements.txt`
2. **CSS must be pre-built** — `static/css/output.css` must be committed to git. Heroku does NOT run npm build. Run `cd jstoolchain && npm run tailwind-build` locally before pushing.
3. `release` phase in Procfile runs `python manage.py migrate` automatically
4. WhiteNoise serves static files — no nginx/S3 needed for static assets

### Database
- `DATABASE_URL` env var set automatically by Heroku Postgres add-on
- `conn_max_age=600` in DATABASES config — persistent DB connections (10-minute pool)
- `ssl_require=not DEBUG` — SSL enforced in production

### Media Files — Ephemeral Filesystem Warning
`MEDIA_ROOT = BASE_DIR / 'media'` stores files on the Heroku dyno's ephemeral filesystem. Any uploaded files (Word document templates in `EstimateSettings`, HOAI Excel files in `ServiceProfile`) are **permanently lost on dyno restart or deploy**.

**Recommendation:** Use django-storages + AWS S3 (or Cloudinary) for `MEDIA_ROOT` in production. The `EstimateSettings` and `InvoiceSettings` models have `FileField` fields for Word templates that would be affected.

### Environment Variable Reference

| Variable | Required | Example | Notes |
|----------|----------|---------|-------|
| `SECRET_KEY` | Yes | `django-...` | Generate fresh; never reuse across environments |
| `DEBUG` | Yes (prod=False) | `False` | Missing = False in prod (raises ValueError) |
| `ALLOWED_HOSTS` | Yes | `bck-finance.herokuapp.com` | Comma-separated |
| `DATABASE_URL` | Yes | `postgres://...` | Set by Heroku add-on automatically |
| `DISABLE_COLLECTSTATIC` | Optional | `1` | Set to skip collectstatic during build |

---

## Authentication (django-allauth)

- `allauth.account` is installed; `allauth.socialaccount` is NOT (no OAuth/social login)
- Login page: `/accounts/login/`
- After login: redirects to `log_create_compact` view (time logging page)
- Allauth email verification and registration can be configured in `ACCOUNT_*` settings — currently uses Django defaults

---

## Admin Interface (Jazzmin)

- `django-jazzmin` replaces default Django admin UI
- Branded with BCK Architektur logo (`static/images/BCK-icon.svg`, `BCK_logo.png`)
- Must be first in `INSTALLED_APPS`
- Config in `JAZZMIN_SETTINGS` and `JAZZMIN_UI_TWEAKS` dicts in settings.py
- Admin accessible at `/admin/`
- Usermenu link "Back to App" points to `/projects/`

---

## URL Structure (finance_project/urls.py)

```python
/admin/      → Django admin (jazzmin)
/accounts/   → django-allauth authentication
/            → tracker.urls (all app routes, 65 patterns)
```

Media file serving (debug only): `urlpatterns += static(MEDIA_URL, document_root=MEDIA_ROOT)`
