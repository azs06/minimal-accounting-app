# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Flask-based small business accounting software with multi-company support, role-based access control, and comprehensive financial management features. The application uses JWT authentication and SQLAlchemy ORM with SQLite database.

## Common Development Commands

### Application Startup

```bash
# Primary method - use the shell script
./run_app.sh

# Alternative methods
export FLASK_APP=src/main.py && flask run --host=0.0.0.0 --port=8080
python src/main.py  # Runs on port 5000
```

### Database Operations

```bash
# Set Flask app for database commands
export FLASK_APP=src/main.py

# Create new migration
flask db migrate -m "Description of changes"

# Apply migrations
flask db upgrade

# Seed initial data (creates admin user + default company)
flask seed initial
```

### Environment Setup

```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

## Architecture Overview

### Multi-Tenant Structure

- All business operations are company-scoped with URL pattern `/api/companies/{company_id}/`
- Users can own multiple companies with role-based permissions within each
- Authentication uses JWT tokens with user context

### Core Components

- **Models**: Database entities in `src/models/` with SQLAlchemy ORM
- **Routes**: API blueprints in `src/routes/` - all business endpoints are company-scoped
- **Authentication**: JWT-based with role decorators in `src/decorators/auth_decorators.py`
- **Database**: SQLite with Flask-Migrate for schema versioning

### Key Models

- **User/Company**: Many-to-many with CompanyUser association and role management
- **Employee**: Company-scoped with optional User account linking
- **Business Records**: Income, Expense, Invoice, Inventory, Salary - all company-isolated
- **Reporting**: Built-in P&L, sales, expense, and payroll report generation

### Permission System

Three levels: System Admin (platform-wide), Company Owner (full company access), Company Roles (Admin/Editor/Viewer within companies)

## Testing

The project uses `api.http` for API testing with comprehensive endpoint coverage. No formal testing framework is currently configured.

## Database Schema

Migrations are in `/migrations/versions/`. The application uses Flask-Migrate (Alembic) for schema management. Current schema includes user authentication, company multi-tenancy, and full accounting data models with proper foreign key relationships.
