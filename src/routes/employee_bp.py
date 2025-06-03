from flask import Blueprint, request, jsonify
from src.extensions import db
from src.models.employee import Employee
from src.models.salary import Salary # Import Salary from its new file
from src.models.user import User
from src.models.company import Company
from src.models.enums import CompanyRoleEnum, RoleEnum
from datetime import datetime, date
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.routes.company_bp import _get_current_user, _check_permission # Re-use helper functions

employee_bp = Blueprint("employee_bp", __name__)

# --- Employee Endpoints ---
@employee_bp.route("/employees", methods=["POST"])
@jwt_required()
def add_employee(company_id):
    current_user = _get_current_user()
    if not current_user:
        return jsonify({"message": "Authentication required"}), 401

    company = Company.query.get_or_404(company_id)

    if not _check_permission(current_user, company,
                             allowed_company_roles=[CompanyRoleEnum.ADMIN, CompanyRoleEnum.EDITOR],
                             allow_owner=True,
                             allow_system_admin=True):
        return jsonify({"message": "Unauthorized to add employees to this company"}), 403

    data = request.get_json()
    if not data or not data.get("first_name") or not data.get("last_name"):
        return jsonify({"message": "Missing required fields (first_name, last_name)"}), 400

    # Employee email uniqueness is global as per current model.
    # If it should be unique per company, the model and this check would need adjustment.
    if data.get("email") and Employee.query.filter_by(email=data["email"]).first():
        return jsonify({"message": f"Employee with email {data['email']} already exists"}), 409

    try:
        hire_date_str = data.get("hire_date")
        hire_date = datetime.strptime(hire_date_str, "%Y-%m-%d").date() if hire_date_str else None
        user_id = data.get("user_id") # Optional: link to an existing user
        if user_id and not User.query.get(user_id):
            return jsonify({"message": f"User with ID {user_id} not found."}), 404
    except ValueError:
        return jsonify({"message": "Invalid hire_date format (YYYY-MM-DD)"}), 400

    new_employee = Employee(
        first_name=data["first_name"],
        last_name=data["last_name"],
        email=data.get("email"),
        phone_number=data.get("phone_number"),
        position=data.get("position"),
        hire_date=hire_date,
        is_active=data.get("is_active", True),
        company_id=company_id, # Assign to the current company
        user_id=user_id
    )
    try:
        db.session.add(new_employee)
        db.session.commit()
        return jsonify(new_employee.to_dict()), 201
    except IntegrityError: # Should be caught by email check, but as a safeguard
        db.session.rollback()
        return jsonify({"message": "Database error: Employee with that email might already exist."}), 409


@employee_bp.route("/employees", methods=["GET"])
@jwt_required()
def get_all_employees(company_id):
    current_user = _get_current_user()
    if not current_user:
        return jsonify({"message": "Authentication required"}), 401

    company = Company.query.get_or_404(company_id)

    if not _check_permission(current_user, company,
                             allowed_company_roles=[CompanyRoleEnum.ADMIN, CompanyRoleEnum.EDITOR, CompanyRoleEnum.VIEWER],
                             allow_owner=True,
                             allow_system_admin=True):
        return jsonify({"message": "Unauthorized to view employees for this company"}), 403

    employees = Employee.query.filter_by(company_id=company_id).order_by(Employee.last_name, Employee.first_name).all()
    return jsonify([employee.to_dict() for employee in employees]), 200

@employee_bp.route("/employees/<int:employee_id>", methods=["GET"])
@jwt_required()
def get_employee(company_id, employee_id):
    current_user = _get_current_user()
    if not current_user:
        return jsonify({"message": "Authentication required"}), 401

    company = Company.query.get_or_404(company_id) # Ensure company exists
    employee = Employee.query.get_or_404(employee_id)

    if employee.company_id != company_id:
        return jsonify({"message": "Employee not found in this company"}), 404

    if not _check_permission(current_user, company,
                             allowed_company_roles=[CompanyRoleEnum.ADMIN, CompanyRoleEnum.EDITOR, CompanyRoleEnum.VIEWER],
                             allow_owner=True,
                             allow_system_admin=True):
        return jsonify({"message": "Unauthorized to view this employee"}), 403

    return jsonify(employee.to_dict()), 200

@employee_bp.route("/employees/<int:employee_id>", methods=["PUT"])
@jwt_required()
def update_employee(company_id, employee_id):
    current_user = _get_current_user()
    if not current_user:
        return jsonify({"message": "Authentication required"}), 401

    company = Company.query.get_or_404(company_id) # Ensure company exists
    employee = Employee.query.get_or_404(employee_id)
    data = request.get_json()
    if not data:
        return jsonify({"message": "Request body must be JSON"}), 400

    if "first_name" in data: employee.first_name = data["first_name"]
    if "last_name" in data: employee.last_name = data["last_name"]

    if employee.company_id != company_id:
        return jsonify({"message": "Employee not found in this company"}), 404

    if not _check_permission(current_user, company,
                             allowed_company_roles=[CompanyRoleEnum.ADMIN, CompanyRoleEnum.EDITOR],
                             allow_owner=True,
                             allow_system_admin=True):
        return jsonify({"message": "Unauthorized to update employees in this company"}), 403

    if 'email' in data and data['email'] != employee.email:
        # Ensure email is not None or empty if it's being set and is required to be non-null unique
        # For now, assuming unique constraint handles empty strings if not nullable.
        if data['email'] and Employee.query.filter(Employee.id != employee_id, Employee.email == data['email']).first():
            return jsonify({"message": f"Email '{data['email']}' is already in use by another employee"}), 409
        employee.email = data['email']
    elif 'email' in data and data['email'] is None and employee.email is not None: # Explicitly setting email to None
        employee.email = None

    if "phone_number" in data: employee.phone_number = data["phone_number"]
    if "position" in data: employee.position = data["position"]
    if "is_active" in data: employee.is_active = data["is_active"]
    if "user_id" in data: # Allow linking/unlinking user
        user_id_to_link = data.get("user_id")
        if user_id_to_link and not User.query.get(user_id_to_link):
            return jsonify({"message": f"User with ID {user_id_to_link} not found."}), 404
        employee.user_id = user_id_to_link

    try:
        if "hire_date" in data:
            hire_date_str = data.get("hire_date")
            employee.hire_date = datetime.strptime(hire_date_str, "%Y-%m-%d").date() if hire_date_str else None
    except ValueError:
        return jsonify({"message": "Invalid hire_date format (YYYY-MM-DD)"}), 400

    try:
        db.session.commit()
        return jsonify(employee.to_dict()), 200
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Database error during update. Email might conflict."}), 409

@employee_bp.route("/employees/<int:employee_id>", methods=["DELETE"])
@jwt_required()
def delete_employee(company_id, employee_id):
    current_user = _get_current_user()
    if not current_user:
        return jsonify({"message": "Authentication required"}), 401

    company = Company.query.get_or_404(company_id) # Ensure company exists
    employee = Employee.query.get_or_404(employee_id)

    if employee.company_id != company_id:
        return jsonify({"message": "Employee not found in this company"}), 404

    if not _check_permission(current_user, company,
                             allowed_company_roles=[CompanyRoleEnum.ADMIN],
                             allow_owner=True,
                             allow_system_admin=True):
        return jsonify({"message": "Unauthorized to delete employees from this company"}), 403
    # Salaries associated will be deleted due to cascade in model
    db.session.delete(employee)
    db.session.commit()
    return '', 204

# --- Endpoint to convert Employee to User ---
@employee_bp.route("/employees/<int:employee_id>/create-user", methods=["POST"])
@jwt_required() # Typically an admin action
def create_user_for_employee(company_id, employee_id):
    current_user = _get_current_user()
    if not current_user:
        return jsonify({"message": "Authentication required"}), 401

    company = Company.query.get_or_404(company_id)
    employee = Employee.query.get_or_404(employee_id)

    if employee.company_id != company_id:
        return jsonify({"message": "Employee not found in this company"}), 404

    if not _check_permission(current_user, company, allowed_company_roles=[CompanyRoleEnum.ADMIN], allow_owner=True, allow_system_admin=True):
        return jsonify({"message": "Unauthorized to create user for employee in this company"}), 403
        
    if employee.user_id:
        return jsonify({"message": f"Employee {employee_id} already has an associated user account (User ID: {employee.user_id})."}), 409

    data = request.get_json()
    if not data:
        return jsonify({"message": "Request body must be JSON"}), 400

    username = data.get('username')
    password = data.get('password')
    # Use employee's email as default if not provided, but require it if employee has no email
    email = data.get('email', employee.email)
    role = data.get('role', 'user')

    if not username or not password or not email:
        return jsonify({"message": "Missing required fields (username, password, email)"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"message": f"User with username '{username}' already exists"}), 409
    if User.query.filter_by(email=email).first():
        return jsonify({"message": f"User with email '{email}' already exists"}), 409

    try:
        user_role_enum = RoleEnum(role) # Validate system role
    except ValueError:
        valid_roles = [r.value for r in RoleEnum]
        return jsonify({"message": f"Invalid system role: {role}. Valid roles are: {valid_roles}"}), 400

    new_user = User(username=username, email=email, role=user_role_enum)
    new_user.set_password(password)
    
    db.session.add(new_user)
    
    try:
        db.session.flush() # Assigns an ID to new_user without full commit
        employee.user_id = new_user.id # Link employee to the new user
        db.session.commit()
        return jsonify({"message": "User account created and linked to employee successfully.", "user": new_user.to_dict()}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Database error during user creation or linking."}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "An unexpected error occurred.", "error": str(e)}), 500

# --- Salary Endpoints ---
@employee_bp.route("/employees/<int:employee_id>/salaries", methods=["POST"])
@jwt_required()
def add_salary(company_id, employee_id):
    current_user = _get_current_user()
    if not current_user:
        return jsonify({"message": "Authentication required"}), 401

    company = Company.query.get_or_404(company_id)
    employee = Employee.query.get_or_404(employee_id)

    data = request.get_json()

    if not data or data.get("gross_amount") is None or not data.get("payment_date"):
        return jsonify({"message": "Missing required fields (gross_amount, payment_date)"}), 400

    try:
        payment_date = datetime.strptime(data["payment_date"], "%Y-%m-%d").date()
        gross_amount = float(data["gross_amount"])
        deductions = float(data.get("deductions", 0.0))
        if gross_amount < 0 or deductions < 0:
            return jsonify({"message": "Gross amount and deductions cannot be negative"}), 400
        
        period_start_str = data.get("payment_period_start")
        payment_period_start = datetime.strptime(period_start_str, "%Y-%m-%d").date() if period_start_str else None
        period_end_str = data.get("payment_period_end")
        payment_period_end = datetime.strptime(period_end_str, "%Y-%m-%d").date() if period_end_str else None

    except ValueError:
        return jsonify({"message": "Invalid data format for amount or dates (YYYY-MM-DD)"}), 400

    if employee.company_id != company_id:
        return jsonify({"message": "Employee not found in this company"}), 404

    if not _check_permission(current_user, company,
                             allowed_company_roles=[CompanyRoleEnum.ADMIN, CompanyRoleEnum.EDITOR],
                             allow_owner=True,
                             allow_system_admin=True):
        return jsonify({"message": "Unauthorized to add salaries for this company's employees"}), 403

    recorder_id = current_user.id
    new_salary = Salary(
        employee_id=employee.id,
        payment_date=payment_date,
        gross_amount=gross_amount,
        deductions=deductions,
        payment_period_start=payment_period_start,
        payment_period_end=payment_period_end,
        notes=data.get("notes"),
        recorded_by_user_id=recorder_id
    )
    new_salary.calculate_net_amount() # Calculate net amount before saving
    
    try:
        db.session.add(new_salary)
        db.session.commit()
        return jsonify(new_salary.to_dict()), 201
    except Exception as e: # Catch a broader exception if needed, or specific ones
        db.session.rollback()
        return jsonify({"message": "Failed to add salary record", "error": str(e)}), 500

@employee_bp.route("/employees/<int:employee_id>/salaries", methods=["GET"])
@jwt_required()
def get_employee_salaries(company_id, employee_id):
    current_user = _get_current_user()
    if not current_user:
        return jsonify({"message": "Authentication required"}), 401

    company = Company.query.get_or_404(company_id)
    employee = Employee.query.get_or_404(employee_id)

    if employee.company_id != company_id:
        return jsonify({"message": "Employee not found in this company"}), 404

    if not _check_permission(current_user, company,
                             allowed_company_roles=[CompanyRoleEnum.ADMIN, CompanyRoleEnum.EDITOR, CompanyRoleEnum.VIEWER],
                             allow_owner=True,
                             allow_system_admin=True):
        return jsonify({"message": "Unauthorized to view salaries for this company's employees"}), 403

    salaries = Salary.query.filter_by(employee_id=employee_id).order_by(Salary.payment_date.desc()).all()
    return jsonify([salary.to_dict() for salary in salaries]), 200

# Note: The individual salary GET, PUT, DELETE routes are now nested under company and employee
# as per the api.http file structure: /api/companies/<cid>/employees/<eid>/salaries/<sid>

@employee_bp.route("/employees/<int:employee_id>/salaries/<int:salary_id>", methods=["GET"])
@jwt_required()
def get_salary(company_id, employee_id, salary_id):
    current_user = _get_current_user()
    if not current_user:
        return jsonify({"message": "Authentication required"}), 401

    company = Company.query.get_or_404(company_id)
    employee = Employee.query.get_or_404(employee_id)
    salary = Salary.query.get_or_404(salary_id)

    if employee.company_id != company_id or salary.employee_id != employee_id:
        return jsonify({"message": "Salary record not found for this employee in this company"}), 404

    if not _check_permission(current_user, company,
                             allowed_company_roles=[CompanyRoleEnum.ADMIN, CompanyRoleEnum.EDITOR, CompanyRoleEnum.VIEWER],
                             allow_owner=True,
                             allow_system_admin=True):
        return jsonify({"message": "Unauthorized to view this salary record"}), 403

    return jsonify(salary.to_dict()), 200

@employee_bp.route("/employees/<int:employee_id>/salaries/<int:salary_id>", methods=["PUT"])
@jwt_required()
def update_salary(company_id, employee_id, salary_id):
    current_user = _get_current_user()
    if not current_user: return jsonify({"message": "Authentication required"}), 401
    company = Company.query.get_or_404(company_id)
    employee = Employee.query.get_or_404(employee_id)
    salary = Salary.query.get_or_404(salary_id)
    data = request.get_json()
    updated = False

    try:
        if "payment_date" in data:
            salary.payment_date = datetime.strptime(data["payment_date"], "%Y-%m-%d").date()
            updated = True
        if "gross_amount" in data:
            gross_amount = float(data["gross_amount"])
            if gross_amount < 0: return jsonify({"message": "Gross amount cannot be negative"}), 400
            salary.gross_amount = gross_amount
            updated = True
        if "deductions" in data:
            deductions = float(data["deductions"])
            if deductions < 0: return jsonify({"message": "Deductions cannot be negative"}), 400
            salary.deductions = deductions
            updated = True
        
        if "payment_period_start" in data:
            period_start_str = data.get("payment_period_start")
            salary.payment_period_start = datetime.strptime(period_start_str, "%Y-%m-%d").date() if period_start_str else None
            updated = True
        if "payment_period_end" in data:
            period_end_str = data.get("payment_period_end")
            salary.payment_period_end = datetime.strptime(period_end_str, "%Y-%m-%d").date() if period_end_str else None
            updated = True
        if "notes" in data:
            salary.notes = data["notes"]
            updated = True

    except ValueError:
        return jsonify({"message": "Invalid data format for amount or dates (YYYY-MM-DD)"}), 400

    if employee.company_id != company_id or salary.employee_id != employee_id:
        return jsonify({"message": "Salary record not found for this employee in this company"}), 404

    if not _check_permission(current_user, company,
                             allowed_company_roles=[CompanyRoleEnum.ADMIN, CompanyRoleEnum.EDITOR],
                             allow_owner=True,
                             allow_system_admin=True):
        return jsonify({"message": "Unauthorized to update this salary record"}), 403

    if updated:
        salary.calculate_net_amount()
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({"message": "Failed to update salary record", "error": str(e)}), 500
        
    return jsonify(salary.to_dict()), 200

@employee_bp.route("/employees/<int:employee_id>/salaries/<int:salary_id>", methods=["DELETE"])
@jwt_required()
def delete_salary(company_id, employee_id, salary_id):
    current_user = _get_current_user()
    if not current_user: return jsonify({"message": "Authentication required"}), 401

    company = Company.query.get_or_404(company_id)
    employee = Employee.query.get_or_404(employee_id)
    salary = Salary.query.get_or_404(salary_id)

    if employee.company_id != company_id or salary.employee_id != employee_id:
        return jsonify({"message": "Salary record not found for this employee in this company"}), 404

    if not _check_permission(current_user, company,
                             allowed_company_roles=[CompanyRoleEnum.ADMIN],
                             allow_owner=True,
                             allow_system_admin=True):
        return jsonify({"message": "Unauthorized to delete this salary record"}), 403

    db.session.delete(salary)
    db.session.commit()
    return '', 204
