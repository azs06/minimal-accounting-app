from flask import Blueprint, request, jsonify
from src.extensions import db
from src.models.income import Income
from datetime import datetime
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError


income_bp = Blueprint("income_bp", __name__)

@income_bp.route("/income", methods=["POST"])
@jwt_required()
def add_income():
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

    current_user_id = int(get_jwt_identity()) # Cast identity back to int
    new_income = Income(
        description=data["description"],
        amount=amount,
        date_received=date_received,
        category=data.get("category"),
        notes=data.get("notes"),
        user_id=current_user_id 
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
def get_all_income():
    current_user_id = int(get_jwt_identity()) # Cast identity back to int
    # Only fetch income records for the currently authenticated user
    incomes = Income.query.filter_by(user_id=current_user_id).all()
    return jsonify([income.to_dict() for income in incomes]), 200

@income_bp.route("/income/<int:income_id>", methods=["GET"])
@jwt_required()
def get_income(income_id):
    current_user_id = int(get_jwt_identity()) # Cast identity back to int
    income = Income.query.get_or_404(income_id)
    if income.user_id != current_user_id:
        return jsonify({"message": "Unauthorized to access this income record"}), 403
    return jsonify(income.to_dict()), 200

@income_bp.route("/income/<int:income_id>", methods=["PUT"])
@jwt_required()
def update_income(income_id):
    current_user_id = int(get_jwt_identity()) # Cast identity back to int
    income = Income.query.get_or_404(income_id)
    if income.user_id != current_user_id:
        return jsonify({"message": "Unauthorized to update this income record"}), 403

    data = request.get_json()

    if data.get("description"):
        income.description = data["description"]
    if data.get("amount") is not None:
        try:
            amount = float(data["amount"])
            if amount <= 0:
                return jsonify({"message": "Amount must be positive"}), 400
            income.amount = amount
        except ValueError:
            return jsonify({"message": "Invalid amount format"}), 400
    if data.get("date_received"):
        try:
            income.date_received = datetime.strptime(data["date_received"], "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"message": "Invalid date_received format (YYYY-MM-DD)"}), 400
    if data.get("category"):
        income.category = data["category"]
    if data.get("notes"):
        income.notes = data["notes"]
    
    try:
        db.session.commit()
        return jsonify(income.to_dict()), 200
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Database error: Could not update income record."}), 500
    except Exception as e: # Catch other potential errors
        db.session.rollback()
        return jsonify({"message": "An unexpected error occurred.", "error": str(e)}), 500

@income_bp.route("/income/<int:income_id>", methods=["DELETE"])
@jwt_required()
def delete_income(income_id):
    current_user_id = int(get_jwt_identity()) # Cast identity back to int
    income = Income.query.get_or_404(income_id)
    if income.user_id != current_user_id:
        return jsonify({"message": "Unauthorized to delete this income record"}), 403
    db.session.delete(income)
    db.session.commit()
    return '', 204
