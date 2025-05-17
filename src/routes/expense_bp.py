from flask import Blueprint, request, jsonify
from src.extensions import db
from src.models.expense import Expense # Changed from Income to Expense
from datetime import datetime

# Placeholder for user authentication - in a real app, you'd get user_id from session/token
# For now, we might require user_id in the request or use a default
MOCK_USER_ID = 1 # Replace with actual user handling later

expense_bp = Blueprint("expense_bp", __name__)

@expense_bp.route("/expenses", methods=["POST"])
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

    new_expense = Expense(
        description=data["description"],
        amount=amount,
        date_incurred=date_incurred,
        category=data.get("category"),
        vendor=data.get("vendor"),
        notes=data.get("notes"),
        user_id=data.get("user_id", MOCK_USER_ID)
    )
    db.session.add(new_expense)
    db.session.commit()
    return jsonify(new_expense.to_dict()), 201

@expense_bp.route("/expenses", methods=["GET"])
def get_all_expenses(): # Renamed from get_all_income
    expenses = Expense.query.all()
    return jsonify([expense.to_dict() for expense in expenses]), 200

@expense_bp.route("/expenses/<int:expense_id>", methods=["GET"])
def get_expense(expense_id): # Renamed from get_income
    expense = Expense.query.get_or_404(expense_id)
    return jsonify(expense.to_dict()), 200

@expense_bp.route("/expenses/<int:expense_id>", methods=["PUT"])
def update_expense(expense_id): # Renamed from update_income
    expense = Expense.query.get_or_404(expense_id)
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
    
    db.session.commit()
    return jsonify(expense.to_dict()), 200

@expense_bp.route("/expenses/<int:expense_id>", methods=["DELETE"])
def delete_expense(expense_id): # Renamed from delete_income
    expense = Expense.query.get_or_404(expense_id)
    db.session.delete(expense)
    db.session.commit()
    return jsonify({"message": "Expense record deleted"}), 200

