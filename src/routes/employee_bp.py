from flask import Blueprint, request, jsonify
from src.extensions import db
from src.models.employee import Employee, Salary
from datetime import datetime, date
from sqlalchemy.exc import IntegrityError

# Placeholder for user authentication
MOCK_USER_ID = 1

employee_bp = Blueprint("employee_bp", __name__)

# --- Employee Endpoints ---
@employee_bp.route("/employees", methods=["POST"])
def add_employee():
    data = request.get_json()
    if not data or not data.get("first_name") or not data.get("last_name"):
        return jsonify({"message": "Missing required fields (first_name, last_name)"}), 400

    if data.get("email") and Employee.query.filter_by(email=data["email"]).first():
        return jsonify({"message": f"Employee with email {data['email']} already exists"}), 409

    try:
        hire_date_str = data.get("hire_date")
        hire_date = datetime.strptime(hire_date_str, "%Y-%m-%d").date() if hire_date_str else None
    except ValueError:
        return jsonify({"message": "Invalid hire_date format (YYYY-MM-DD)"}), 400

    new_employee = Employee(
        first_name=data["first_name"],
        last_name=data["last_name"],
        email=data.get("email"),
        phone_number=data.get("phone_number"),
        position=data.get("position"),
        hire_date=hire_date,
        is_active=data.get("is_active", True)
    )
    try:
        db.session.add(new_employee)
        db.session.commit()
        return jsonify(new_employee.to_dict()), 201
    except IntegrityError: # Should be caught by email check, but as a safeguard
        db.session.rollback()
        return jsonify({"message": "Database error: Employee with that email might already exist."}), 409


@employee_bp.route("/employees", methods=["GET"])
def get_all_employees():
    employees = Employee.query.order_by(Employee.last_name, Employee.first_name).all()
    return jsonify([employee.to_dict() for employee in employees]), 200

@employee_bp.route("/employees/<int:employee_id>", methods=["GET"])
def get_employee(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    return jsonify(employee.to_dict()), 200

@employee_bp.route("/employees/<int:employee_id>", methods=["PUT"])
def update_employee(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    data = request.get_json()
    if not data:
        return jsonify({"message": "Request body must be JSON"}), 400

    if "first_name" in data: employee.first_name = data["first_name"]
    if "last_name" in data: employee.last_name = data["last_name"]

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
def delete_employee(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    # Salaries associated will be deleted due to cascade in model
    db.session.delete(employee)
    db.session.commit()
    return '', 204

# --- Salary Endpoints ---
@employee_bp.route("/employees/<int:employee_id>/salaries", methods=["POST"])
def add_salary(employee_id):
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

    new_salary = Salary(
        employee_id=employee.id,
        payment_date=payment_date,
        gross_amount=gross_amount,
        deductions=deductions,
        payment_period_start=payment_period_start,
        payment_period_end=payment_period_end,
        notes=data.get("notes"),
        recorded_by_user_id=data.get("recorded_by_user_id", MOCK_USER_ID)
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
def get_employee_salaries(employee_id):
    Employee.query.get_or_404(employee_id) # Ensure employee exists
    salaries = Salary.query.filter_by(employee_id=employee_id).order_by(Salary.payment_date.desc()).all()
    return jsonify([salary.to_dict() for salary in salaries]), 200

@employee_bp.route("/salaries/<int:salary_id>", methods=["GET"])
def get_salary(salary_id):
    salary = Salary.query.get_or_404(salary_id)
    return jsonify(salary.to_dict()), 200

@employee_bp.route("/salaries/<int:salary_id>", methods=["PUT"])
def update_salary(salary_id):
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

    if updated:
        salary.calculate_net_amount()
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({"message": "Failed to update salary record", "error": str(e)}), 500
        
    return jsonify(salary.to_dict()), 200

@employee_bp.route("/salaries/<int:salary_id>", methods=["DELETE"])
def delete_salary(salary_id):
    salary = Salary.query.get_or_404(salary_id)
    db.session.delete(salary)
    db.session.commit()
    return '', 204
