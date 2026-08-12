# Complaint Management System

A complete Django 6.0 web application for managing complaints with role-based access (User, Staff, Admin).

## Features

- **Authentication**: Registration, login, logout, password change
- **Roles**: Normal User, Staff, Admin with appropriate permissions
- **Complaints**: Create, edit (pending only), delete, list with pagination
- **Search & Filter**: By title, category, status, priority, date range
- **Dashboard**: Statistics cards and recent complaints
- **Admin**: Assign staff, update status, manage categories, export CSV
- **Comments & Timeline**: Discussion and status history on each complaint
- **Email notifications**: Console backend on status change (development)
- **Responsive UI**: Bootstrap 5, Poppins font, Font Awesome, custom CSS

## Requirements

- Python 3.10+
- Django 6.0.8
- Pillow

## Setup

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Apply migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Seed sample categories
python manage.py seed_data

# Run development server
python manage.py runserver
```

Visit http://127.0.0.1:8000/

## Project Structure

```
complaint_management_system/
├── complaint_management_system/   # Project settings
│   ├── settings.py
│   ├── urls.py
│   └── ...
├── complaints/                    # Main app
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   ├── admin.py
│   ├── urls.py
│   ├── signals.py
│   └── management/commands/seed_data.py
├── templates/
│   ├── base.html, navbar.html, footer.html
│   ├── home.html, dashboard.html, admin_dashboard.html
│   ├── accounts/
│   └── complaints/
├── static/css/
│   ├── style.css
│   ├── dashboard.css
│   ├── forms.css
│   └── responsive.css
├── media/
├── manage.py
└── requirements.txt
```

## Roles & Permissions

| Action              | User | Staff | Admin |
|---------------------|------|-------|-------|
| Submit complaint    | Yes  | Yes   | Yes   |
| View own complaints | Yes  | Yes   | Yes   |
| View assigned       |      | Yes   | Yes   |
| View all            |      |       | Yes   |
| Assign staff        |      |       | Yes   |
| Update status       |      | Yes   | Yes   |
| Manage categories   |      |       | Yes   |
| Export CSV          |      |       | Yes   |

## URLs

- `/` – Home
- `/dashboard/` – User dashboard
- `/complaints/` – List
- `/complaints/create/` – New complaint
- `/complaints/<id>/` – Detail
- `/categories/` – Category management (admin)
- `/profile/` – User profile
- `/accounts/login/`, `/accounts/register/`, `/accounts/logout/`
- `/admin/` – Django admin
- `/admin-dashboard/` – Custom admin stats
- `/export/csv/` – CSV export

## Notes

- SQLite is used by default for development.
- Media files are stored under `media/`.
- Email uses the console backend in development.
- After creating a superuser, run `seed_data` so their Profile role is set to admin.
- Staff users: create via Django admin and set Profile.role to `staff`.
