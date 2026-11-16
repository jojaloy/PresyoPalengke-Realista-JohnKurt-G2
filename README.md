# PresyoPalengke

Crowdsourced palengke price checker for Cebu City public markets (IT-317 – G2, Project Development 1).
Full-stack Django (templates) + PostgreSQL/Supabase.

**Phase 1 – Account Feature:** registration, login/logout, role-based dashboards (Shopper, Vendor, Admin), user profile.

**Phase 2 – Core Feature: Price Reporting.** Shoppers report the price they saw for a product at a Cebu City market. Reports are saved to PostgreSQL/Supabase and linked to the shopper who made them.

| Role | What they can do with price reports |
|------|--------------------------------------|
| Shopper | Create, view, edit and delete **their own** reports (`/reports/`, `/reports/new/`) |
| Vendor | View all reports (read-only) to compare against their own prices |
| Admin | View all reports, delete any report (moderation); manage markets/products in Django Admin |

Models (`reports/models.py`): `Market`, `Product` (reference data, seeded by migration) and `PriceReport` (`reporter` → User, `product` → Product, `market` → Market).
Validation: price must be ₱0.01–₱10,000; date cannot be in the future or older than 7 days; one report per user, product, market and day; only active markets/products can be chosen.

## Setup
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then fill in your DB credentials (never commit .env)
python manage.py migrate
python manage.py createsuperuser   # creates an Admin
python manage.py seed_demo         # optional: test accounts (admin_test / vendor_test / shopper_test) + sample reports
python manage.py runserver
```
Open http://127.0.0.1:8000/

## Roles
| Role | How created | Dashboard |
|------|-------------|-----------|
| Shopper | Register form | `/dashboard/shopper/` |
| Vendor | Register form | `/dashboard/vendor/` |
| Admin | `createsuperuser` | `/dashboard/admin/` |

Users can change their own password from the Profile page (`/password/change/`).

Opening another role's dashboard URL returns 403; logged-out users are redirected to login.

## Tests
`python manage.py test` (runs `accounts` and `reports` tests)

## Branching
`main` (stable) ← `develop` (integration) ← `feature/<name>` branches, merged through Pull Requests.
