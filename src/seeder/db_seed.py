import click
from flask.cli import with_appcontext
from src.extensions import db
from src.models.user import User, RoleEnum # Import RoleEnum
from src.models.company import Company
from datetime import datetime
from werkzeug.security import generate_password_hash

# Define a Click group for all seed commands
@click.group(name='seed')
def seed_bp():
    """Commands to seed the database."""
    pass

@seed_bp.command("initial")
@with_appcontext
def seed_initial_data():
    """Seeds the database with essential initial data like an admin user and a default company."""
    click.echo("Starting to seed initial data...")

    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        click.echo("Creating admin user...")
        admin_password_hash = generate_password_hash('adminpassword') # Choose a strong default password
        admin_user = User(
            id=1, # Explicitly set ID if other parts of your system rely on it for the default company
            username='admin',
            email='admin@example.com',
            password_hash=admin_password_hash,
            role=RoleEnum.SYSTEM_ADMIN, # Use Enum member
            created_at=datetime.utcnow()
        )
        db.session.add(admin_user)
        try:
            db.session.commit()
            click.echo("Admin user created successfully with ID: 1.")
        except Exception as e:
            db.session.rollback()
            click.echo(f"Error creating admin user: {e}")
            return # Stop if admin user creation fails
    else:
        click.echo(f"Admin user (ID: {admin_user.id}) already exists. Skipping user seeding.")
        # Ensure the existing admin user has ID 1 if we are relying on it
        if admin_user.id != 1:
            click.echo(f"WARNING: Existing admin user does not have ID 1. Default company creation might fail if it expects owner_id=1.")


    default_company = Company.query.filter_by(name='Default Company').first()
    if not default_company:
        # Ensure the admin user (owner_id=1) exists before creating the company
        owner_for_default_company = User.query.get(1)
        if not owner_for_default_company:
            click.echo("Admin user with ID 1 not found. Cannot create Default Company without an owner.")
            return

        click.echo("Creating Default Company...")
        default_company = Company(
            # id=1, # Let the DB assign the ID for the company unless specifically needed
            name='Default Company',
            owner_id=owner_for_default_company.id, # Assumes admin user with ID 1 is the owner
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.session.add(default_company)
        try:
            db.session.commit()
            click.echo(f"Default Company created successfully with ID: {default_company.id}.")
        except Exception as e:
            db.session.rollback()
            click.echo(f"Error creating Default Company: {e}")
    else:
        click.echo(f"Default Company (ID: {default_company.id}) already exists. Skipping company seeding.")

    click.echo("Initial data seeding process finished.")


def register_seed_commands(app):
    """Registers seed commands with the Flask application."""
    app.cli.add_command(seed_bp)