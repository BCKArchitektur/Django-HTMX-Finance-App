# BCK Tracker — External API Integration Guide

This document is the spec for any external app (e.g. the HR App) that needs to read data from the BCK Tracker.

**Base URL (production):** `https://bck-f86a70e697db.herokuapp.com`  
**Base URL (local dev):** `http://localhost:9000`

---

## Authentication

Every request must include an API key in the `Authorization` header:

```
Authorization: Api-Key <your-key>
```

**How to get a key:**  
A Tracker admin creates keys at `/admin/tracker/apikey/`. Each key gets a name (e.g. `HR App – Production`) and a randomly generated secret. The secret is shown in the admin detail view once and is stable — copy it and store it in the HR App's environment variables.

**To revoke a key:** set `is_active = False` in the admin. The key stops working immediately, no deploy required.

---

## Endpoints

### `GET /api/hours/`

Returns the total logged hours per calendar day for one employee within a date range.

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `username` | string | Yes | The Django username of the employee in the Tracker app |
| `from` | `YYYY-MM-DD` | Yes | Start date, **inclusive** |
| `to` | `YYYY-MM-DD` | Yes | End date, **inclusive** |

Date range cannot exceed 366 days.

#### Success Response — `200 OK`

```json
[
  {"date": "2026-04-01", "hours": 7.5},
  {"date": "2026-04-02", "hours": 8.0},
  {"date": "2026-04-04", "hours": 4.25}
]
```

- Sorted by date, ascending.
- Only dates that have **at least one log entry** are returned. Days with no logs are omitted (not returned as `{"hours": 0}`). The HR App should treat missing dates as "no data / possible absence".
- `hours` is a float rounded to 4 decimal places.

#### Error Responses

| Status | When |
|--------|------|
| `400 Bad Request` | Missing/invalid parameters |
| `401 Unauthorized` | Missing or wrong API key |
| `404 Not Found` | `username` not found in Tracker |

**400 example:**
```json
{
  "errors": {
    "from": "This parameter is required.",
    "to": "Must be in YYYY-MM-DD format."
  }
}
```

**401 example:**
```json
{
  "detail": "Invalid or inactive API key."
}
```

**404 example:**
```json
{
  "error": "No employee found with username 'john.doe'."
}
```

---

## Examples

### curl

```bash
curl -X GET \
  "https://bck-f86a70e697db.herokuapp.com/api/hours/?username=max.mustermann&from=2026-04-01&to=2026-04-30" \
  -H "Authorization: Api-Key YOUR_KEY_HERE"
```

### Python (requests library)

```python
import requests

API_BASE = "https://bck-f86a70e697db.herokuapp.com"
API_KEY  = "YOUR_KEY_HERE"  # store in env vars, never hardcode

def get_employee_hours(username: str, from_date: str, to_date: str) -> list[dict]:
    """
    Returns a list of {"date": "YYYY-MM-DD", "hours": float} dicts.
    Raises requests.HTTPError on non-2xx responses.
    """
    response = requests.get(
        f"{API_BASE}/api/hours/",
        headers={"Authorization": f"Api-Key {API_KEY}"},
        params={"username": username, "from": from_date, "to": to_date},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


# Example usage
hours = get_employee_hours("max.mustermann", "2026-04-01", "2026-04-30")
for entry in hours:
    print(f"{entry['date']}: {entry['hours']} h")
```

### Python — weekly aggregation (Phase 3 sync pattern)

```python
from datetime import date, timedelta
from collections import defaultdict

def get_weekly_hours(username: str, week_start: date) -> dict[str, float]:
    """Returns total hours for each day of the given ISO week."""
    week_end = week_start + timedelta(days=6)
    daily = get_employee_hours(
        username,
        week_start.strftime("%Y-%m-%d"),
        week_end.strftime("%Y-%m-%d"),
    )
    # Fill in zeros for missing days
    result = {}
    current = week_start
    for _ in range(7):
        result[current.isoformat()] = 0.0
        current += timedelta(days=1)
    for entry in daily:
        result[entry["date"]] = entry["hours"]
    return result
```

---

## Important Notes for the HR App

### Username Mapping
The `username` field is the Django username from the Tracker app (visible in `/admin/tracker/user/`). The HR App needs a `tracker_username` field on its employee profile to store this mapping. Confirm with the Tracker admin which users are active.

### Timezone
All timestamps in the Tracker are stored in **Europe/Berlin** time. The date boundary for each log entry is the Berlin-local date at the time the log was submitted. A log created at 00:30 Berlin time on April 2nd will appear under `2026-04-02`, not April 1st.

### Missing Days vs. Zero Hours
If a date is missing from the response, it means **no log entries exist** for that day — it does not necessarily mean the employee was absent. Public holidays, sick days, and vacation are not tracked in this system. The HR App should combine Tracker data with its own absence records to determine if a missing day is an absence or a day off.

### Hours Format
`hours` is stored as a float (e.g. `0.25` = 15 min, `0.5` = 30 min, `7.5` = 7 h 30 min). The Tracker UI uses increments of 0.25 h.

### Rate Limits
No rate limiting is currently enforced. Please keep nightly sync calls reasonable (one call per employee per sync run). If the HR App batches 30+ employees, add a 100ms delay between requests.

---

## Phases (Implementation Checklist)

### Phase 1 — Tracker API ✅ DONE
- [x] `GET /api/hours/` endpoint implemented
- [x] `APIKey` model with admin UI to manage keys
- [x] `Authorization: Api-Key` header authentication

### Phase 2 — HR App Setup (HR App developer)
- [ ] Add `tracker_username` field to employee profile model
- [ ] Create `tracker_sync` table: `employee`, `week_start`, `logged_hours`, `balance`, `synced_at`
- [ ] Store API key in Heroku config var: `TRACKER_API_KEY`
- [ ] Store Tracker URL in config var: `TRACKER_API_URL`

### Phase 3 — Nightly Sync (HR App developer)
- [ ] Cron job runs nightly (e.g. 02:00 Berlin time)
- [ ] For each employee with a `tracker_username`, call `GET /api/hours/` for the current week
- [ ] Calculate: `balance = logged_hours - assigned_hours` per week
- [ ] Flag days in the current week with no logs (possible absences)
- [ ] Save results to `tracker_sync`

### Phase 4 — HR Dashboard (HR App developer)
- [ ] Alert view: employees with balance < -4 h this week
- [ ] Alert view: employees with 2+ consecutive days without logs
- [ ] Detail view: week-by-week balance per employee

---

## Adding More Endpoints Later

To expose additional data (projects, invoices, etc.) follow the same pattern:

1. Add a new view class in `tracker/api_views.py` using `APIKeyAuthentication` + `IsAuthenticated`
2. Add the URL in `tracker/urls.py` under the `# External API` section
3. Document it in this file

The `APIKey` model supports multiple named keys — you can issue a separate key per integration if needed.
