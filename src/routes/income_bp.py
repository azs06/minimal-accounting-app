from flask import Blueprint, request, jsonify
from src.extensions import db
from src.models.income import Income
from src.models.company import Company
from src.models.user import User # Though _get_current_user returns User object
from src.models.enums import CompanyRoleEnum, RoleEnum
from datetime import datetime
from flask_jwt_extended import jwt_required # get_jwt_identity is in _get_current_user
from sqlalchemy.exc import IntegrityError
from src.routes.company_bp import _get_current_user, _check_permission # Re-use helper functions


income_bp = Blueprint("income_bp", __name__)

@income_bp.route("/income", methods=["POST"])
@jwt_required()
def add_income_record(company_id): # Renamed function and added company_id
    current_user = _get_current_user()
    if not current_user:
        return jsonify({"message": "Authentication required"}), 401

    company = Company.query.get_or_404(company_id)

    if not _check_permission(current_user, company,
                             allowed_company_roles=[CompanyRoleEnum.ADMIN, CompanyRoleEnum.EDITOR],
                             allow_owner=True,
                             allow_system_admin=True):
        return jsonify({"message": "Unauthorized to add income to this company"}), 403

    data = request.get_json()
    if not data or not data.get("description") or data.get("amount") is None or not data.get("date_received"):
        return jsonify({"message": "Missing required fields (description, amount, date_received)"}), 400
    
    try:
        date_received = datetime.strptime(data["date_received"], "%Y-%m-%d").date()
        amount = float(data["amount"])
        if amount <= 0:
            return jsonify({"message": "Amount must be positive"}), 400
    except ValueError:
        return jsonify({"message": "Invalid data format for amount or date_received (YYYY-MM-DD)"}), 400

    new_income = Income(
        description=data["description"],
        amount=amount,
        date_received=date_received,
        category=data.get("category"),
        notes=data.get("notes"),
        user_id=current_user.id, # User who recorded this income
        company_id=company_id # Assign to the current company
    )
    try:
        db.session.add(new_income)
        db.session.commit()
        return jsonify(new_income.to_dict()), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Database error: Could not add income record."}), 500
    except Exception as e: # Catch other potential errors
        db.session.rollback()
        return jsonify({"message": "An unexpected error occurred.", "error": str(e)}), 500

@income_bp.route("/income", methods=["GET"])
@jwt_required()
def get_all_income_records(company_id): # Renamed function and added company_id
    current_user = _get_current_user()
    if not current_user:
        return jsonify({"message": "Authentication required"}), 401

    company = Company.query.get_or_404(company_id)

    if not _check_permission(current_user, company,
                             allowed_company_roles=[CompanyRoleEnum.ADMIN, CompanyRoleEnum.EDITOR, CompanyRoleEnum.VIEWER],
                             allow_owner=True,
                             allow_system_admin=True):
        return jsonify({"message": "Unauthorized to view income for this company"}), 403

    incomes = Income.query.filter_by(company_id=company_id).order_by(Income.date_received.desc()).all()
    return jsonify([income.to_dict() for income in incomes]), 200

@income_bp.route("/income/<int:income_id>", methods=["GET"])
@jwt_required()
def get_income_record(company_id, income_id): # Renamed function and added company_id
    current_user = _get_current_user()
    if not current_user:
        return jsonify({"message": "Authentication required"}), 401

    company = Company.query.get_or_404(company_id) # Ensure company exists
    income = Income.query.get_or_404(income_id)

    if income.company_id != company_id:
        return jsonify({"message": "Income record not found in this company"}), 404

    if not _check_permission(current_user, company,
                             allowed_company_roles=[CompanyRoleEnum.ADMIN, CompanyRoleEnum.EDITOR, CompanyRoleEnum.VIEWER],
                             allow_owner=True,
                             allow_system_admin=True):
        return jsonify({"message": "Unauthorized to view this income record"}), 403

    return jsonify(income.to_dict()), 200

@income_bp.route("/income/<int:income_id>", methods=["PUT"])
@jwt_required()
def update_income_record(company_id, income_id): # Renamed function and added company_id
    current_user = _get_current_user()
    if not current_user:
        return jsonify({"message": "Authentication required"}), 401

    company = Company.query.get_or_404(company_id) # Ensure company exists
    income = Income.query.get_or_404(income_id)
    data = request.get_json()
    updated = False # Flag to check if any actual update happened

    if data.get("description"):
        income.description = data["description"]
        updated = True
    if data.get("amount") is not None:
        try:
            amount = float(data["amount"])
            if amount <= 0:
                return jsonify({"message": "Amount must be positive"}), 400
            income.amount = amount
        except ValueError:
            return jsonify({"message": "Invalid amount format"}), 400
        updated = True
    if data.get("date_received"):
        try:
            income.date_received = datetime.strptime(data["date_received"], "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"message": "Invalid date_received format (YYYY-MM-DD)"}), 400
        updated = True
    if data.get("category"):
        income.category = data["category"]
        updated = True
    if data.get("notes"):
        income.notes = data["notes"]
        updated = True
    
    if income.company_id != company_id:
        return jsonify({"message": "Income record not found in this company"}), 404

    if not _check_permission(current_user, company,
                             allowed_company_roles=[CompanyRoleEnum.ADMIN, CompanyRoleEnum.EDITOR],
                             allow_owner=True,
                             allow_system_admin=True):
        return jsonify({"message": "Unauthorized to update income in this company"}), 403

    if updated:
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return jsonify({"message": "Database error: Could not update income record."}), 500
        except Exception as e: # Catch other potential errors
            db.session.rollback()
            return jsonify({"message": "An unexpected error occurred.", "error": str(e)}), 500
    return jsonify(income.to_dict()), 200

@income_bp.route("/income/<int:income_id>", methods=["DELETE"])
@jwt_required()
def delete_income_record(company_id, income_id): # Renamed function and added company_id
    current_user = _get_current_user()
    if not current_user:
        return jsonify({"message": "Authentication required"}), 401

    company = Company.query.get_or_404(company_id) # Ensure company exists
    income = Income.query.get_or_404(income_id)

    if income.company_id != company_id:
        return jsonify({"message": "Income record not found in this company"}), 404

    if not _check_permission(current_user, company,
                             allowed_company_roles=[CompanyRoleEnum.ADMIN], # Typically only admins or owners can delete
                             allow_owner=True,
                             allow_system_admin=True):
        return jsonify({"message": "Unauthorized to delete income from this company"}), 403
    try:
        db.session.delete(income)
        db.session.commit()
        return '', 204
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to delete income record", "error": str(e)}), 500
