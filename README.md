# Finance Dashboard

**Live Demo**: [https://financial-dashboard-i373.onrender.com](https://financial-dashboard-i373.onrender.com)

A Django + Django REST Framework backend for a multi-user finance dashboard system with JWT authentication, role-based access control, financial record management, dashboard analytics, and a minimal Django-based frontend for demonstration.

## Tech Stack

- **Python 3.x** / **Django 5.2+**
- **Django REST Framework** — API layer
- **djangorestframework-simplejwt** — JWT authentication with token blacklisting
- **django-filter** — queryset filtering
- **Bootstrap 5** — frontend styling (via CDN)
- **Neon PostgreSQL** — remote production/development database

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 1.5 Setup Environment (Optional for local testing)
# Create a .env file with DATABASE_URL to use PostgreSQL. 
# If omitted, it will safely fall back to a local SQLite database!

# 2. Run migrations
python manage.py migrate

# 3. Create a superuser (admin role)
python manage.py createsuperuser

# 4. Seed sample data (optional — creates 3 users + 60 records)
python manage.py seed_data

# 5. Run the development server
python manage.py runserver

# 6. Run the test suite
python manage.py test --verbosity=2
```

After creating a superuser, set the user's role to `admin` via Django Admin at `http://127.0.0.1:8000/admin/` (the `role` field defaults to `viewer` — update it to `admin` for full access).

Alternatively, use `python manage.py seed_data` to create ready-to-use accounts. 

### Demo Credentials

These are pre-seeded accounts for evaluation/testing.
Login is username-based.

**Admin:**
- username: `admin_user`
- password: `Admin@123!`

**Analyst:**
- username: `analyst_user`
- password: `Analyst@123!`

**Viewer:**
- username: `viewer_user`
- password: `Viewer@123!`

## Frontend

A minimal Django-based frontend is included for demonstration purposes. It uses Django templates with Bootstrap 5 and session authentication.

| Page | URL | Access |
|------|-----|--------|
| Login | `/login/` | Public |
| Dashboard | `/dashboard/` | All authenticated users |
| Records | `/records/` | All authenticated users |
| Create Record | `/records/create/` | Admin only |
| Analytics | `/analytics/` | Analyst + Admin |
| User Management | `/users/` | Admin only |
| Create User | `/users/create/` | Admin only |

The root URL (`/`) redirects to the dashboard if logged in, or to the login page otherwise.

## Project Structure

```
├── manage.py
├── requirements.txt
├── finance_dashboard/        # Django project settings & root URLs
│   ├── settings.py
│   └── urls.py
├── accounts/                 # User model, auth, user management
│   ├── models.py             # Custom User with role field
│   ├── serializers.py        # Profile, UserManagement
│   ├── permissions.py        # IsAdmin, IsAnalystOrAbove
│   ├── views.py              # Logout, Profile, User CRUD
│   ├── urls.py
│   ├── admin.py
│   └── tests.py
├── records/                  # Financial record management
│   ├── models.py             # FinancialRecord model
│   ├── serializers.py        # CRUD serializer with validation
│   ├── filters.py            # Date, category, type, amount filters
│   ├── views.py              # ModelViewSet with per-action permissions
│   ├── urls.py
│   ├── admin.py
│   └── tests.py
├── dashboard/                # Aggregated analytics & summaries
│   ├── views.py              # SummaryView, AnalyticsView, TimeAnalyticsView
│   ├── urls.py
│   └── tests.py
├── frontend/                 # Django template frontend
│   ├── views.py              # Login, dashboard, records, analytics, users
│   └── urls.py
└── templates/                # HTML templates (Bootstrap 5)
```

## Roles & Permission Matrix

| Action                          | Viewer | Analyst | Admin |
|---------------------------------|--------|---------|-------|
| Login / Logout                  | ✓      | ✓       | ✓     |
| View own profile                | ✓      | ✓       | ✓     |
| List / view financial records   | ✓      | ✓       | ✓     |
| Create / update / delete records| ✗      | ✗       | ✓     |
| Dashboard summary               | ✓      | ✓       | ✓     |
| Dashboard analytics             | ✗      | ✓       | ✓     |
| Time-scoped analytics           | ✗      | ✓       | ✓     |
| Create / manage users           | ✗      | ✗       | ✓     |
| Deactivate users                | ✗      | ✗       | ✓     |

**Enforcement**: Permissions are enforced at the API layer using custom DRF permission classes (`IsAdmin`, `IsAnalystOrAbove`) applied per-view or per-action in viewsets.

## API Endpoints

Base URL: `/api/v1/`

### Authentication

| Method | Endpoint               | Description                     | Auth     |
|--------|------------------------|---------------------------------|----------|
| POST   | `/auth/login/`         | Obtain JWT token pair           | Public   |
| POST   | `/auth/login/refresh/` | Refresh an access token         | Public   |
| POST   | `/auth/logout/`        | Blacklist refresh token         | JWT      |
| GET    | `/auth/profile/`       | Current user profile            | JWT      |

### User Management (Admin only)

| Method     | Endpoint             | Description                        |
|------------|----------------------|------------------------------------|
| GET        | `/auth/users/`       | List all users                     |
| POST       | `/auth/users/`       | Create user with any role          |
| GET        | `/auth/users/{id}/`  | Retrieve a user                    |
| PUT/PATCH  | `/auth/users/{id}/`  | Update user (role, active status)  |

> **Note**: There is no user self-registration. All user accounts are created and managed by Admin only.

### Financial Records

| Method     | Endpoint              | Description                        | Auth            |
|------------|-----------------------|------------------------------------|-----------------:|
| GET        | `/records/`           | List records (paginated, filterable) | All auth users |
| POST       | `/records/`           | Create a record                    | Admin only      |
| GET        | `/records/{id}/`      | Retrieve a record                  | All auth users  |
| PUT/PATCH  | `/records/{id}/`      | Update a record                    | Admin only      |
| DELETE     | `/records/{id}/`      | Delete a record                    | Admin only      |

**Filters** (query params on `GET /records/`):

| Param         | Example                    | Description               |
|---------------|----------------------------|---------------------------|
| `record_type` | `?record_type=income`      | income or expense         |
| `category`    | `?category=salary`         | Exact category match      |
| `status`      | `?status=approved`         | pending/approved/rejected |
| `date_from`   | `?date_from=2026-01-01`    | Records on or after date  |
| `date_to`     | `?date_to=2026-12-31`      | Records on or before date |
| `amount_min`  | `?amount_min=100`          | Minimum amount            |
| `amount_max`  | `?amount_max=5000`         | Maximum amount            |
| `search`      | `?search=salary`           | Search in description/category |
| `ordering`    | `?ordering=-amount`        | Order by date/amount/created_at |

### Dashboard & Analytics

| Method | Endpoint                      | Description                                            | Auth            |
|--------|-------------------------------|--------------------------------------------------------|-----------------|
| GET    | `/dashboard/summary/`         | Income/expense totals, net balance, recent records     | All auth users  |
| GET    | `/dashboard/analytics/`       | Category breakdown, monthly trends, type distribution  | Analyst + Admin |
| GET    | `/dashboard/time-analytics/`  | Time-scoped analysis (daily/monthly/yearly/custom)     | Analyst + Admin |

**Time analytics query parameters**:

| Mode    | Parameters                                  |
|---------|---------------------------------------------|
| Daily   | `?type=daily&date=2026-04-05`               |
| Monthly | `?type=monthly&month=2026-04`               |
| Yearly  | `?type=yearly&year=2026`                    |
| Custom  | `?start_date=2026-01-01&end_date=2026-03-31`|

## Example Requests

### Login
```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin_user","password":"Admin@123!"}'
# Returns: {"access": "...", "refresh": "..."}
```

### Create a financial record (Admin)
```bash
curl -X POST http://127.0.0.1:8000/api/v1/records/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"amount":"5000.00","record_type":"income","category":"salary","date":"2026-04-01","description":"Monthly salary","status":"approved"}'
```

### Get dashboard summary
```bash
curl http://127.0.0.1:8000/api/v1/dashboard/summary/ \
  -H "Authorization: Bearer <access_token>"
# Returns: {"total_income":5000,"total_expense":1500,"net_balance":3500,"record_count":3,"recent_records":[...]}
```

### Logout
```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/logout/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"refresh":"<refresh_token>"}'
```

## Design Decisions & Assumptions

### Record Visibility
Financial records are **organization-scoped (global)**. All authenticated users can view all records. This models a company finance dashboard where records represent organizational transactions, not personal expenses. The `created_by` field is tracked for audit purposes.

### Authentication & Logout
- **JWT** via `djangorestframework-simplejwt` for stateless API authentication.
- **Session authentication** is additionally enabled for the frontend template layer.
- **Logout** is handled by blacklisting the refresh token on the server side. The client should discard both tokens. The `rest_framework_simplejwt.token_blacklist` app manages this.
- **Token rotation** is enabled — when refreshing, the old refresh token is automatically blacklisted.

### User Management
- There is **no public self-registration**. All user accounts are created by Admin, either through the API (`POST /auth/users/`) or the frontend user management page.
- **User deletion is intentionally not supported.** Instead, users can be **deactivated** by setting the `is_active` field to `false`. This preserves data integrity — financial records, audit trails, and `created_by` references remain intact even after a user is deactivated. Deactivated users cannot log in.
- Roles are stored as a field on the custom `User` model (not a separate table) for simplicity.
- The `is_staff` and `is_superuser` Django fields are separate from the application-level `role` field. Superusers have Django Admin access; the `role` field controls API-level permissions.

### Validation
- Amount must be positive (enforced in serializer).
- Record type must be `income` or `expense` (enforced by model choices).
- Status must be `pending`, `approved`, or `rejected`.
- Password validation uses Django's built-in validators (min length, common passwords, numeric-only).
- Missing required fields return 400 with field-level error messages.
- Analytics parameters are validated with clear error messages for invalid dates, formats, and unsupported types.

### What's Not Included
- No soft delete for records — records are hard-deleted. Can be added via a `deleted_at` field if needed.
- No multi-tenancy or organization model — records are globally visible to all authenticated users.
- No file uploads, invoicing, or complex accounting logic.

## Tests

60 tests covering:
- **Auth**: login (JWT), logout (blacklisting), profile access, admin user management permissions
- **Records CRUD**: admin can create/update/delete; viewer/analyst get 403; unauthenticated gets 401
- **Validation**: negative amounts, invalid record types, missing fields
- **Filtering**: by record type, date range
- **Dashboard**: summary returns correct totals and structure; analytics accessible to analyst/admin only; viewer gets 403
- **Time Analytics**: daily/monthly/yearly/custom modes, parameter validation, role-based access, totals correctness, category breakdowns

```bash
python manage.py test --verbosity=2
```
