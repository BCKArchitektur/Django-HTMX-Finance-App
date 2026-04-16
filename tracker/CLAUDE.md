# tracker/ App Context

## Model Hierarchy

```
Project
  └── Contract (ManyToMany)
        └── Section (ManyToMany)
              └── Item (ManyToMany — field name: Section.Item, capital I)
                    ├── Task (ManyToMany)
                    └── User (ManyToMany)
```

Cascade deletes flow downward: deleting a Project deletes its Contracts → Sections → Items.

## Models Summary (tracker/models.py)

| Model | Key Fields | Notes |
|-------|-----------|-------|
| `User` | extends AbstractUser | adds `dark_mode` (BooleanField) |
| `Employee` | OneToOne→User, per-day assigned hours, `salary`, `social_security_percentage`, `total_salary` | `total_salary` auto-calculated incl. social security; `date_override` forced True for staff |
| `Client` | `firm_name` (unique), address, `country` (CountryField) | Referenced by Project.client_name FK |
| `Project` | `project_name`, `status` (4 choices), `hourly_rates_override` (JSONField) | ManyToMany: User, Contract |
| `Contract` | `contract_name`, `contract_no` (unique), `vat_percentage` (Decimal, default 19.00), `additional_fee_percentage` (default 6.5%), `hoai_data` (JSONField), `scope_of_work` (HTML from Quill) | ManyToMany: User, Section |
| `Section` | `section_name`, `allocated_budget`, `section_billed_hourly`, `exclude_from_nachlass`, `order` | ManyToMany: User, Item |
| `Item` | `Item_name` (capital I!), `quantity`, `unit` (Std/Psch/Stk/%/Monat/Tag), `rate`, `total` (auto), `order` | ManyToMany: Task, User. Has `get_applicable_rate()` method |
| `Task` | `task_name` | ManyToMany via Item |
| `Logs` | `log_time` (FloatField), `log_timestamps` (CharField — NOT DateTimeField), FKs: user, log_contract, log_section, log_Item (capital I), `log_tasks` (CharField storing task names) | Time tracking records |
| `Invoice` | `provided_quantities` (JSONField: `{item_id: {rate, quantity}}`), `invoice_net`, `current_invoice_net`, `invoice_gross`, `invoice_type` (ER/AR/SR/ZR), `is_cumulative`, `current_ar_number` | Atomic title generation in `save()` |
| `ProjectPreset` / `UserPreset` | FKs to user, project, contract, section, Item, task | Store last-used selections for quick re-logging |
| `SectionLibrary` / `ItemLibrary` / `TaskLibrary` | Hierarchical template library | Used in `get_library_section` view |
| `DeletedInvoiceNumber` | `number` (unique) | Tracks recycled invoice numbers |
| `EstimateSettings` | Singleton. 8 DecimalFields for hourly rates, FileFields for Word templates, `consecutive_start_no` | Default rates; overridable per-project via `Project.hourly_rates_override` |
| `InvoiceSettings` | Singleton. `invoice_counter`, FileFields for invoice templates | Global invoice numbering |
| `ServiceProfile` | `name` (unique), `excel_file`, `no_of_Honarzone`, `lp_breakdown` (JSONField with LP percentages) | HOAI tables |

### Item.get_applicable_rate() — rate resolution order
1. Check `Project.hourly_rates_override` JSONField for project-level override
2. Fall back to `EstimateSettings` global defaults
3. Fall back to `Item.rate`

## views.py Structure (2,800+ lines — logical groupings)

When splitting into a `tracker/views/` package, use these modules:

| File | Functions |
|------|-----------|
| `auth_views.py` | `toggle_dark_mode`, `login_page`, `logout_page` |
| `log_views.py` | `log_create_compact`, `log_create`, `delete_log`, `dashboard` |
| `project_views.py` | `projects`, `add_project`, `edit_project`, `delete_project`, `project_details`, `edit_client`, `delete_client`, `get_project_users`, `handle_user_updates` |
| `contract_views.py` | `load_contracts`, `load_sections`, `load_Items`, `load_tasks`, `load_contract_data`, `get_contract_scope`, `update_scope`, `delete_contract`, `move_contract`, `get_library_section`, `check_*_name`, `get_new_contract_number`, `handle_new_contract_form`, `handle_existing_contract_form` |
| `budget_views.py` | `add_budget`, `add_users`, `add_users_to_item`, `load_item_users`, `load_item_budget` |
| `invoice_views.py` | `create_invoice`, `delete_invoice`, `view_invoice`, `download_invoice`, `record_payment`, `get_first_invoice_mode` |
| `document_views.py` | `generate_word_document`, `insert_html_to_docx`, `set_bullet`, `extract_hoai_details` |
| `hoai_views.py` | `ServiceProfileUploadView`, `ServiceProfileListView`, `HOAICalculationView` |
| `project_settings_views.py` | `update_project_settings`, `reset_project_hourly_rates`, `generate_revit_shared_parameter_file` |

When splitting: create `tracker/views/__init__.py` that re-exports all names. `tracker/urls.py` imports by name — the split is transparent to URL patterns.

## Known Technical Debt

### Bugs / Deprecations
- **`request.is_ajax()` removed in Django 4.0** — appears in `project_details` view. Replace with:
  ```python
  request.headers.get('X-Requested-With') == 'XMLHttpRequest'
  ```
- **`log_timestamps` is a CharField**, not a DateTimeField. Stored as `"YYYY-MM-DD HH:MM:SS"` string. Do not treat it as a datetime object without parsing first.

### Code Quality
- **60+ `print()` calls** in views.py, 17 in models.py, 10 in signals.py — all should use `logging`
- **No `select_related`/`prefetch_related`** anywhere — every nested loop is an N+1 query. Worst offenders: `load_contract_data`, `handle_user_updates`, `download_invoice`, `edit_project`
- **No tests** — `tracker/tests.py` is empty (only boilerplate)
- **`parse_german_number()`, `format_german_number()`, `extract_hoai_details()`** are defined in `views.py` but belong in `utils.py` (which already exists)

### Performance hot spots
- `handle_user_updates`: cascades user add/remove through the full Project→Contract→Section→Item hierarchy (4 nested loops, no prefetching)
- `download_invoice`: iterates sections/items with no prefetching
- `load_contract_data`: called on every contract modal open, computes invoice history

## Signals (tracker/signals.py)

Registered via `TrackerConfig.ready()`:

| Signal | Trigger | Action |
|--------|---------|--------|
| `post_save` Contract (created) | New contract saved | Increment `EstimateSettings.consecutive_start_no` |
| `post_save` Contract (created) | New contract saved | Increment `InvoiceSettings.invoice_counter` |
| `post_delete` Invoice | Invoice deleted | Store number in `DeletedInvoiceNumber` (for recycling) or decrement counter |
| `post_delete` Contract | Contract deleted | Decrement `EstimateSettings.consecutive_start_no` |

## Forms (tracker/forms.py)

| Form | Purpose |
|------|---------|
| `LogForm` | Time entry with dependent dropdowns (contract → section → item → task) |
| `ProjectForm` | Project CRUD, active users only |
| `ClientForm` | Client CRUD with CountryField and DaisyUI styling |
| `ContractForm` | Minimal contract edit (name, VAT, contract_no) |
| `InvoiceForm` | Invoice creation with `provided_quantities` JSONField |
| `ProjectPresetForm` | Cascade dropdowns for quick re-logging |
| `AddUsersForm` / `AddBudgetForm` | Batch operations |
| `HiddenForm` | Hidden field passthrough |

## CSRF Pattern

All `fetch()` POSTs read the CSRF token from the form's hidden input:
```javascript
headers: {
    'X-CSRFToken': form.querySelector('[name=csrfmiddlewaretoken]').value,
}
```
Or from the meta tag in `base.html`:
```javascript
document.querySelector('meta[name="csrf-token"]').getAttribute('content')
```

**No view uses `@csrf_exempt`.** All forms must include `{% csrf_token %}`.

## Template Locations

- App templates: `tracker/templates/tracker/` (17 files)
- Partials: `tracker/templates/tracker/partials/` (navbar.html, sidebar.html)
- Auth templates: `finance_project/templates/` (allauth account templates)
- Word templates (.docx): `templates/estimates/`, `templates/invoices/`, `templates/terms_and_conditions/`

## Admin Features (tracker/admin.py)

- **Logs admin**: `export_to_excel` action generates formatted Excel with formulas
- **Project admin**: `generate_shared_param_file` action exports to Revit shared parameter format
- **EstimateSettings / InvoiceSettings**: file upload with old-file cleanup on replace
- **SectionLibrary / ItemLibrary / TaskLibrary**: hierarchical inline editing
