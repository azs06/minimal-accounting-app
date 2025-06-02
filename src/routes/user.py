from flask import Blueprint, jsonify, request
from src.models.user import User, db
from src.models.employee import Employee # Import Employee model
from werkzeug.security import check_password_hash # generate_password_hash is in User model
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import jwt_required, get_jwt_identity # For protection
from datetime import datetime # For hire_date parsing

user_bp = Blueprint('user', __name__)

@user_bp.route('/users', methods=['GET'])
@jwt_required() # Protect this route, typically admin only
def get_users():
    # TODO: Add role-based authorization (e.g., only admins can see all users)
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])

@user_bp.route('/users', methods=['POST'])
@jwt_required() # Protect this route, typically admin only
def create_user():
    data = request.get_json()
    if not data:
        return jsonify({"message": "Request body must be JSON"}), 400

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    employee_details = data.get('employee_details') # Optional employee details

    if not username or not email or not password:
        return jsonify({"message": "Missing required fields (username, email, password)"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"message": f"User with username '{username}' already exists"}), 409
    if User.query.filter_by(email=email).first():
        return jsonify({"message": f"User with email '{email}' already exists"}), 409

    new_user = User(username=username, email=email)
    if data.get('role'): # Allow setting role if provided
        new_user.role = data.get('role')
    new_user.set_password(password)
    db.session.add(new_user)

    new_employee = None
    if employee_details:
        if not employee_details.get("first_name") or not employee_details.get("last_name"):
            db.session.rollback() # Rollback user creation if employee details are bad
            return jsonify({"message": "Employee details require first_name and last_name"}), 400
        
        # Check for duplicate employee email if provided
        if employee_details.get("email") and Employee.query.filter_by(email=employee_details["email"]).first():
            db.session.rollback()
            return jsonify({"message": f"Employee with email {employee_details['email']} already exists"}), 409

        try:
            hire_date_str = employee_details.get("hire_date")
            hire_date = datetime.strptime(hire_date_str, "%Y-%m-%d").date() if hire_date_str else None
        except ValueError:
            db.session.rollback()
            return jsonify({"message": "Invalid hire_date format (YYYY-MM-DD) for employee"}), 400

        new_employee = Employee(
            first_name=employee_details["first_name"],
            last_name=employee_details["last_name"],
            email=employee_details.get("email"),
            phone_number=employee_details.get("phone_number"),
            position=employee_details.get("position"),
            hire_date=hire_date,
            is_active=employee_details.get("is_active", True)
            # user_id will be set after user is committed and has an ID
        )
        db.session.add(new_employee)

    try:
        db.session.commit() # Commit user (and employee if present)
        
        if new_employee:
            new_employee.user_id = new_user.id # Link employee to the new user
            db.session.commit() # Commit the linkage

        return jsonify(new_user.to_dict()), 201 # User.to_dict() now includes employee_id
    except IntegrityError: # Should be caught by above checks, but as a safeguard
        db.session.rollback()
        return jsonify({"message": "Database error: User with that username or email might already exist."}), 409

@user_bp.route('/users/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    # TODO: Add role-based authorization (user can get self, admin can get any)
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())

@user_bp.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    # TODO: Add role-based authorization (user can update self, admin can update any)
    # current_acting_user_id = int(get_jwt_identity())
    # if current_acting_user_id != user_id and not is_admin(current_acting_user_id):
    #     return jsonify({"message": "Unauthorized"}), 403

    user = User.query.get_or_404(user_id)
    data = request.get_json()

    if not data:
        return jsonify({"message": "Request body must be JSON"}), 400

    if 'username' in data and data['username'] != user.username:
        if User.query.filter(User.id != user_id, User.username == data['username']).first():
            return jsonify({"message": f"Username '{data['username']}' is already taken"}), 409
        user.username = data['username']

    if 'email' in data and data['email'] != user.email:
        if User.query.filter(User.id != user_id, User.email == data['email']).first():
            return jsonify({"message": f"Email '{data['email']}' is already in use"}), 409
        user.email = data['email']

    if 'password' in data:
        # For a real app, you might want to require the old password
        # or have this as a separate, more privileged action.
        if not data['password']:
             return jsonify({"message": "New password cannot be empty"}), 400
        user.set_password(data['password'])

    if 'role' in data: # Allow role updates if necessary, potentially with authorization checks
        user.role = data['role']

    try:
        db.session.commit()
        return jsonify(user.to_dict()), 200
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Database error during update. Username or email might conflict."}), 409

@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required() # Protect this route, typically admin only
def delete_user(user_id):
    # TODO: Add role-based authorization (e.g., only admins can delete users)
    # current_acting_user_id = int(get_jwt_identity())
    # if not is_admin(current_acting_user_id):
    #     return jsonify({"message": "Unauthorized"}), 403
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return '', 204

@user_bp.route('/users/me/password', methods=['PUT'])
@jwt_required()
def update_my_password():
    """Allows the currently authenticated user to update their own password."""
    current_user_id = int(get_jwt_identity())
    user = User.query.get_or_404(current_user_id)

    data = request.get_json()
    if not data:
        return jsonify({"message": "Request body must be JSON"}), 400

    old_password = data.get('old_password')
    new_password = data.get('new_password')

    if not old_password or not new_password:
        return jsonify({"message": "Both old_password and new_password are required"}), 400

    if not user.check_password(old_password):
        return jsonify({"message": "Incorrect old password"}), 401

    if len(new_password) < 6: # Example: Enforce minimum password length
        return jsonify({"message": "New password must be at least 6 characters long"}), 400

    user.set_password(new_password)
    db.session.commit()

    return jsonify({"message": "Password updated successfully"}), 200
