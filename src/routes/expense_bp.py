from flask import Blueprint, request, jsonify
from src.extensions import db
from src.models.expense import Expense # Changed from Income to Expense
from datetime import datetime
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError


expense_bp = Blueprint("expense_bp", __name__)

@expense_bp.route("/expenses", methods=["POST"])
@jwt_required()
def add_expense(): # Renamed from add_income
    data = request.get_json()
    if not data or not data.get("description") or data.get("amount") is None or not data.get("date_incurred"):
        return jsonify({"message": "Missing required fields (description, amount, date_incurred)"}), 400
    
    try:
        date_incurred = datetime.strptime(data["date_incurred"], "%Y-%m-%d").date()
        amount = float(data["amount"])
        if amount <= 0:
            return jsonify({"message": "Amount must be positive"}), 400
    except ValueError:
        return jsonify({"message": "Invalid data format for amount or date_incurred (YYYY-MM-DD)"}), 400

    current_user_id = int(get_jwt_identity())
    new_expense = Expense(
        description=data["description"],
        amount=amount,
        date_incurred=date_incurred,
        category=data.get("category"),
        vendor=data.get("vendor"),
        notes=data.get("notes"),
        user_id=current_user_id
    )
    try:
        db.session.add(new_expense)
        db.session.commit()
        return jsonify(new_expense.to_dict()), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Database error: Could not add expense record."}), 500
    except Exception as e: # Catch other potential errors
        db.session.rollback()
        return jsonify({"message": "An unexpected error occurred.", "error": str(e)}), 500


@expense_bp.route("/expenses", methods=["GET"])
@jwt_required()
def get_all_expenses(): # Renamed from get_all_income
    current_user_id = int(get_jwt_identity())
    expenses = Expense.query.filter_by(user_id=current_user_id).all()
    return jsonify([expense.to_dict() for expense in expenses]), 200

@expense_bp.route("/expenses/<int:expense_id>", methods=["GET"])
@jwt_required()
def get_expense(expense_id): # Renamed from get_income
    current_user_id = int(get_jwt_identity())
    expense = Expense.query.get_or_404(expense_id)
    if expense.user_id != current_user_id:
        return jsonify({"message": "Unauthorized to access this expense record"}), 403
    return jsonify(expense.to_dict()), 200

@expense_bp.route("/expenses/<int:expense_id>", methods=["PUT"])
@jwt_required()
def update_expense(expense_id): # Renamed from update_income
    current_user_id = int(get_jwt_identity())
    expense = Expense.query.get_or_404(expense_id)
    if expense.user_id != current_user_id:
        return jsonify({"message": "Unauthorized to update this expense record"}), 403

    data = request.get_json()
    if data.get("description"):
        expense.description = data["description"]
    if data.get("amount") is not None:
        try:
            amount = float(data["amount"])
            if amount <= 0:
                return jsonify({"message": "Amount must be positive"}), 400
            expense.amount = amount
        except ValueError:
            return jsonify({"message": "Invalid amount format"}), 400
    if data.get("date_incurred"):
        try:
            expense.date_incurred = datetime.strptime(data["date_incurred"], "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"message": "Invalid date_incurred format (YYYY-MM-DD)"}), 400
    if data.get("category"):
        expense.category = data["category"]
    if data.get("vendor"):
        expense.vendor = data["vendor"]
    if data.get("notes"):
        expense.notes = data["notes"]
    
    try:
        db.session.commit()
        return jsonify(expense.to_dict()), 200
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Database error: Could not update expense record."}), 500
    except Exception as e: # Catch other potential errors
        db.session.rollback()
        return jsonify({"message": "An unexpected error occurred.", "error": str(e)}), 500

@expense_bp.route("/expenses/<int:expense_id>", methods=["DELETE"])
@jwt_required()
def delete_expense(expense_id): # Renamed from delete_income
    current_user_id = int(get_jwt_identity())
    expense = Expense.query.get_or_404(expense_id)
    if expense.user_id != current_user_id:
        return jsonify({"message": "Unauthorized to delete this expense record"}), 403
    db.session.delete(expense)
    db.session.commit()
    return '', 204
