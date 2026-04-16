# BCK Architektur Finance App

## Project Identity
- **Client:** BCK Architektur GMBH (German architectural firm)
- **Purpose:** Internal finance management — project tracking, HOAI fee calculations, contract & invoice management, employee time logging, Word document generation
- **Deployed on:** Heroku (branch: `heroku-deployment`)
- **Stack:** Django 4.2 · Python 3.13 · PostgreSQL · HTMX 1.9.10 · Tailwind CSS 3 / DaisyUI 4 · Gunicorn · WhiteNoise

## Development Commands

```bash
# Activate virtualenv
source venv/bin/activate

# Run dev server (port 9000 is conventional for this project)
python manage.py runserver 0.0.0.0:9000

# Database
python manage.py makemigrations
python manage.py migrate

# Collect static files (required before Heroku deploy)
python manage.py collectstatic --no-input

# Django deployment checks
python manage.py check --deploy

# Build Tailwind CSS (run inside jstoolchain/)
cd jstoolchain && npm run tailwind-build

# Watch Tailwind during development
cd jstoolchain && npm run tailwind-watch
```

## Environment Variables

Copy `.env.example` to `.env` for local development. Required variables:

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Django secret key — generate with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `DEBUG` | `True` for local dev, `False` in production |
| `ALLOWED_HOSTS` | Comma-separated, e.g. `bck-f86a70e697db.herokuapp.com,localhost` |
| `DATABASE_URL` | PostgreSQL URL (Heroku sets this automatically via the Postgres add-on) |

## Architecture Overview

```
finance_project/        Django project config (settings, URLs, wsgi/asgi)
tracker/                Single Django app — all models, views, forms, signals
  models.py             Core data models (13 models)
  views.py              All view functions (~50 views, 2,800+ lines)
  forms.py              Form classes
  admin.py              Django admin configuration
  signals.py            Post-save/post-delete signals for counters
  utils.py              Shared utilities
  urls.py               URL patterns (65 routes)
  serializers.py        DRF serializers for HOAI API views
  templatetags/         Custom template filters
  management/commands/  Management commands
templates/              Word document templates (.docx) for estimates & invoices
static/                 CSS (output.css), JS, fonts, images
jstoolchain/            Node.js toolchain for Tailwind CSS compilation
```

**Frontend pattern:** Most interactions are HTMX requests or vanilla `fetch()` calls — not full page reloads. DaisyUI (Tailwind component library) for UI components. jQuery 3.6 and Tom Select also in use.

**REST API:** Django REST Framework is used only for 3 HOAI endpoints (`ServiceProfileUploadView`, `ServiceProfileListView`, `HOAICalculationView`). All other endpoints are standard Django views.

**Static files:** WhiteNoise serves compressed/hashed static files in production. CSS must be pre-built (`npm run tailwind-build`) and `static/css/output.css` committed to git — Heroku does not run npm builds.

**Media files:** `MEDIA_ROOT = media/` — Heroku has an ephemeral filesystem. Uploaded Word templates and HOAI Excel files are **lost on dyno restart**. Consider S3/Cloudinary for production file storage.

## Critical: German Locale Rules

**All monetary values use German format — this affects every calculation and display:**

| Format | German | English (wrong) |
|--------|--------|-----------------|
| Thousands | period `.` | comma `,` |
| Decimal | comma `,` | period `.` |
| Example | `1.234,56` | `1,234.56` |

Helper functions in `tracker/views.py`:
- `parse_german_number(value)` — converts German string (e.g. `"1.234,56"`) to `Decimal`
- `format_german_number(value)` — formats `Decimal`/`float` to German string

**Never use Python's default float formatting for financial output in templates or Word documents.**

Timezone: `Europe/Berlin`. All time operations must use `django.utils.timezone` or `pytz`.

## Critical: HOAI Business Logic

HOAI = *Honorarordnung für Architekten und Ingenieure* (German mandatory fee schedule for architects).

Key concepts:
- **Leistungsphasen (LP) 1–9:** Service phases, each has a percentage of the Grundhonorar
- **Grundhonorar:** Base fee, calculated from *anrechenbare Kosten* (eligible construction costs) via linear interpolation in HOAI tables (Excel files stored in `ServiceProfile` model)
- **Honorarzone:** Fee zone I–V, sets the fee range
- **Zuschlag:** Surcharge percentage added to Grundhonorar
- **Nebenkosten:** Ancillary costs, default 6.5% (stored in `Contract.additional_fee_percentage`)
- **Nachlass:** Discount, applied only to sections where `exclude_from_nachlass=False`

HOAI contract data is stored as JSON in `Contract.hoai_data`. LP sections reference the Grundhonorar with a percentage breakdown stored in `ServiceProfile.lp_breakdown`.

## Invoice Types

| Code | German | Meaning |
|------|--------|---------|
| `ER` | Einzelrechnung | Standard individual invoice |
| `AR` | Abschlagsrechnung | Progress/partial invoice — tracked with `current_ar_number` |
| `SR` | Schlussrechnung | Final invoice |
| `ZR` | Anzahlungsrechnung | Advance payment invoice |

**Cumulative invoices** (`is_cumulative=True`): each invoice shows running totals; `current_invoice_net` is the delta from the previous invoice. Non-cumulative: each invoice is standalone.

## Model Naming Conventions (Do NOT rename)

- `Item_name` — capital `I` — used in DB column names and existing data
- `log_Item` — capital `I` — FK field on Logs model
- `Section.Item` — ManyToManyField with capital `I` — established pattern
- These naming quirks are intentional legacy — renaming breaks existing data and migrations

## CSRF Pattern for fetch() calls

All `fetch()` POST requests must include the CSRF token header. Standard pattern:

```javascript
// When a form with {% csrf_token %} is on the page:
headers: {
    'X-CSRFToken': form.querySelector('[name=csrfmiddlewaretoken]').value,
}

// When no form is accessible (e.g. inline delete buttons):
function getCsrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    if (meta) return meta.getAttribute('content');
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : '';
}
headers: { 'X-CSRFToken': getCsrfToken() }
```

The base template includes `<meta name="csrf-token" content="{{ csrf_token }}">` in `<head>`.

**No view should use `@csrf_exempt`.** All POST endpoints are protected by Django's CSRF middleware.
