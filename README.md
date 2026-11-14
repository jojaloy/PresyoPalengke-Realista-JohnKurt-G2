# PresyoPalengke

Crowdsourced palengke price checker for Cebu City public markets (IT-317 – G2, Project Development 1).
Full-stack Django (templates) + PostgreSQL/Supabase.

**Phase 1 – Account Feature:** registration, login/logout, role-based dashboards (Shopper, Vendor, Admin), user profile.

## Setup
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then fill in your DB credentials (never commit .env)
python manage.py migrate
python manage.py createsuperuser   # creates an Admin
python manage.py runserver
```
Open http://127.0.0.1:8000/

## Roles
| Role | How created | Dashboard |
|------|-------------|-----------|
| Shopper | Register form | `/dashboard/shopper/` |
| Vendor | Register form | `/dashboard/vendor/` |
| Admin | `createsuperuser` | `/dashboard/admin/` |

Opening another role's dashboard URL returns 403; logged-out users are redirected to login.

## Tests
`python manage.py test accounts`
