from flask import Blueprint, jsonify, request
from src.extensions import db
from src.models.company import Company
from src.models.user import User
from src.models.company_user import CompanyUser # This will now correctly import the model
from src.models.enums import RoleEnum, CompanyRoleEnum # Import from the new enums.py
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import jwt_required, get_jwt_identity

company_bp = Blueprint('company_bp', __name__, url_prefix='/api/companies')

def _get_current_user():
    """Helper to get the current authenticated User object."""
    user_id_str = get_jwt_identity()
    if not user_id_str:
        return None
    try:
        user_id = int(user_id_str)
        return User.query.get(user_id)
    except ValueError:
        return None

def _check_permission(user, company, allowed_company_roles=None, allow_owner=False, allow_system_admin=False):
    """
    Helper function to check user permissions for a company.
    - user: The User object making the request.
    - company: The Company object being accessed.
    - allowed_company_roles: A list of CompanyRoleEnum values that are permitted.
    - allow_owner: Boolean, True if the company owner is permitted.
    - allow_system_admin: Boolean, True if a SYSTEM_ADMIN is permitted.
    """
    if not user or not company:
        return False

    if allow_system_admin and user.role == RoleEnum.SYSTEM_ADMIN:
        return True

    if allow_owner and company.owner_id == user.id:
        return True

    if allowed_company_roles:
        company_user_link = CompanyUser.query.filter_by(user_id=user.id, company_id=company.id).first()
        if company_user_link and company_user_link.role_in_company in allowed_company_roles:
            return True
    return False


@company_bp.route('', methods=['POST'])
@jwt_required()
def create_company():
    current_user = _get_current_user()
    if not current_user:
        return jsonify({"message": "Invalid user token"}), 401

    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({"message": "Company name is required"}), 400

    new_company = Company(name=data['name'], owner_id=current_user.id)
    try:
        db.session.add(new_company)
        db.session.commit()
        return jsonify(new_company.to_dict()), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Error creating company"}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "An unexpected error occurred", "error": str(e)}), 500


@company_bp.route('', methods=['GET'])
@jwt_required()
def get_companies():
    current_user = _get_current_user()
    if not current_user:
        return jsonify({"message": "Invalid user token"}), 401

    # Companies owned by the user
    owned_companies = Company.query.filter_by(owner_id=current_user.id).all()
    
    # Companies where the user is a member (via CompanyUser)
    member_company_ids = [cu.company_id for cu in CompanyUser.query.filter_by(user_id=current_user.id).all()]
    member_companies = Company.query.filter(Company.id.in_(member_company_ids)).all()
    
    all_accessible_companies = list(set(owned_companies + member_companies)) # Use set to avoid duplicates
    
    return jsonify([company.to_dict() for company in all_accessible_companies]), 200


@company_bp.route('/<int:company_id>', methods=['GET'])
@jwt_required()
def get_company(company_id):
    current_user = _get_current_user()
    if not current_user:
        return jsonify({"message": "Invalid user token"}), 401

    company = Company.query.get_or_404(company_id)

    # User can access if they are owner, system_admin, or any member of the company
    is_member = CompanyUser.query.filter_by(user_id=current_user.id, company_id=company.id).first() is not None
    
    if not _check_permission(current_user, company, allow_owner=True, allow_system_admin=True) and not is_member:
        return jsonify({"message": "Unauthorized to access this company"}), 403
        
    return jsonify(company.to_dict_detailed() if hasattr(company, 'to_dict_detailed') else company.to_dict()), 200


@company_bp.route('/<int:company_id>', methods=['PUT'])
@jwt_required()
def update_company(company_id):
    current_user = _get_current_user()
    if not current_user:
        return jsonify({"message": "Invalid user token"}), 401

    company = Company.query.get_or_404(company_id)
    
    if not _check_permission(current_user, company, 
                             allowed_company_roles=[CompanyRoleEnum.ADMIN], 
                             allow_owner=True, 
                             allow_system_admin=True):
        return jsonify({"message": "Unauthorized to update this company"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"message": "Request body must be JSON"}), 400

    if 'name' in data:
        company.name = data['name']
    # Add other updatable fields as necessary

    try:
        db.session.commit()
        return jsonify(company.to_dict()), 200
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Error updating company"}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "An unexpected error occurred", "error": str(e)}), 500


@company_bp.route('/<int:company_id>', methods=['DELETE'])
@jwt_required()
def delete_company(company_id):
    current_user = _get_current_user()
    if not current_user:
        return jsonify({"message": "Invalid user token"}), 401

    company = Company.query.get_or_404(company_id)

    if not _check_permission(current_user, company, allow_owner=True, allow_system_admin=True):
        return jsonify({"message": "Unauthorized to delete this company"}), 403

    try:
        # Consider what happens to related data (employees, invoices etc.) - cascade deletes or manual cleanup
        db.session.delete(company)
        db.session.commit()
        return '', 204
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error deleting company", "error": str(e)}), 500


# --- Company User Management ---

@company_bp.route('/<int:company_id>/users', methods=['POST'])
@jwt_required()
def add_user_to_company(company_id):
    current_user = _get_current_user()
    if not current_user:
        return jsonify({"message": "Invalid user token"}), 401

    company = Company.query.get_or_404(company_id)

    if not _check_permission(current_user, company, 
                             allowed_company_roles=[CompanyRoleEnum.ADMIN], 
                             allow_owner=True, 
                             allow_system_admin=True):
        return jsonify({"message": "Unauthorized to add users to this company"}), 403

    data = request.get_json()
    if not data or 'user_id' not in data or 'role_in_company' not in data:
        return jsonify({"message": "Missing user_id or role_in_company"}), 400

    user_to_add_id = data.get('user_id')
    role_str = data.get('role_in_company')

    user_to_add = User.query.get(user_to_add_id)
    if not user_to_add:
        return jsonify({"message": f"User with ID {user_to_add_id} not found"}), 404

    try:
        company_role = CompanyRoleEnum(role_str)
    except ValueError:
        valid_roles = [r.value for r in CompanyRoleEnum]
        return jsonify({"message": f"Invalid role_in_company: {role_str}. Valid roles are: {valid_roles}"}), 400

    existing_link = CompanyUser.query.filter_by(user_id=user_to_add_id, company_id=company_id).first()
    if existing_link:
        # Update role if user already exists in company
        existing_link.role_in_company = company_role
    else:
        new_company_user = CompanyUser(user_id=user_to_add_id, company_id=company_id, role_in_company=company_role)
        db.session.add(new_company_user)

    try:
        db.session.commit()
        # Fetch the committed object to return its dict representation
        committed_link = CompanyUser.query.filter_by(user_id=user_to_add_id, company_id=company_id).first()
        return jsonify(committed_link.to_dict() if committed_link else {"message": "User added/updated in company"}), 200 if existing_link else 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Error adding user to company"}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "An unexpected error occurred", "error": str(e)}), 500


@company_bp.route('/<int:company_id>/users', methods=['GET'])
@jwt_required()
def list_users_in_company(company_id):
    current_user = _get_current_user()
    if not current_user:
        return jsonify({"message": "Invalid user token"}), 401

    company = Company.query.get_or_404(company_id)
    
    # User must be a member of the company or a system admin to view members
    is_member = CompanyUser.query.filter_by(user_id=current_user.id, company_id=company_id).first() is not None
    is_owner = company.owner_id == current_user.id

    if not (is_member or is_owner or current_user.role == RoleEnum.SYSTEM_ADMIN):
        return jsonify({"message": "Unauthorized to view users for this company"}), 403

    company_users = CompanyUser.query.filter_by(company_id=company_id).all()
    return jsonify([cu.to_dict_with_user_details() if hasattr(cu, 'to_dict_with_user_details') else cu.to_dict() for cu in company_users]), 200


@company_bp.route('/<int:company_id>/users/<int:user_id_to_remove>', methods=['DELETE'])
@jwt_required()
def remove_user_from_company(company_id, user_id_to_remove):
    current_user = _get_current_user()
    if not current_user:
        return jsonify({"message": "Invalid user token"}), 401

    company = Company.query.get_or_404(company_id)

    if not _check_permission(current_user, company, 
                             allowed_company_roles=[CompanyRoleEnum.ADMIN], 
                             allow_owner=True, 
                             allow_system_admin=True):
        return jsonify({"message": "Unauthorized to remove users from this company"}), 403

    # Prevent owner from being removed via this endpoint
    if company.owner_id == user_id_to_remove:
        return jsonify({"message": "Company owner cannot be removed through this endpoint. Transfer ownership or delete company."}), 403

    company_user_link = CompanyUser.query.filter_by(user_id=user_id_to_remove, company_id=company_id).first()
    if not company_user_link:
        return jsonify({"message": "User not found in this company"}), 404

    try:
        db.session.delete(company_user_link)
        db.session.commit()
        return '', 204
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error removing user from company", "error": str(e)}), 500


# It's good practice to register this blueprint in your main app __init__.py or app.py
# from .routes.company_bp import company_bp
# app.register_blueprint(company_bp)

# Ensure your Company, User, and CompanyUser models have to_dict() methods.
# CompanyUser.to_dict() might look like:
# def to_dict(self):
# return {
# "user_id": self.user_id,
# "company_id": self.company_id,
# "role_in_company": self.role_in_company.value
# }
#
# And CompanyUser.to_dict_with_user_details() might include user's username/email:
# def to_dict_with_user_details(self):
#     user_details = User.query.get(self.user_id)
#     return {
#         "user_id": self.user_id,
#         "username": user_details.username if user_details else None,
#         "email": user_details.email if user_details else None,
#         "company_id": self.company_id,
#         "role_in_company": self.role_in_company.value
#     }

# Company.to_dict_detailed() could include lists of employees, etc.