from flask import Blueprint, request, jsonify
from src.extensions import db
from src.models.income import Income
from datetime import datetime

# Placeholder for user authentication - in a real app, you'd get user_id from session/token
# For now, we might require user_id in the request or use a default
MOCK_USER_ID = 1 # Replace with actual user handling later

income_bp = Blueprint("income_bp", __name__)

@income_bp.route("/income", methods=["POST"])
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

    new_income = Income(
        description=data["description"],
        amount=amount,
        date_received=date_received,
        category=data.get("category"),
        notes=data.get("notes"),
        user_id=data.get("user_id", MOCK_USER_ID) # Use provided user_id or mock
    )
    db.session.add(new_income)
    db.session.commit()
    return jsonify(new_income.to_dict()), 201

@income_bp.route("/income", methods=["GET"])
def get_all_income():
    # Add filtering by user_id in a real app
    # incomes = Income.query.filter_by(user_id=MOCK_USER_ID).all()
    incomes = Income.query.all()
    return jsonify([income.to_dict() for income in incomes]), 200

@income_bp.route("/income/<int:income_id>", methods=["GET"])
def get_income(income_id):
    income = Income.query.get_or_404(income_id)
    # Add check for user_id if necessary
    return jsonify(income.to_dict()), 200

@income_bp.route("/income/<int:income_id>", methods=["PUT"])
def update_income(income_id):
    income = Income.query.get_or_404(income_id)
    # Add check for user_id if necessary
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
    
    db.session.commit()
    return jsonify(income.to_dict()), 200

@income_bp.route("/income/<int:income_id>", methods=["DELETE"])
def delete_income(income_id):
    income = Income.query.get_or_404(income_id)
    # Add check for user_id if necessary
    db.session.delete(income)
    db.session.commit()
    return jsonify({"message": "Income record deleted"}), 200

