from flask import Blueprint, jsonify, Response, request
from src.extensions import db
from src.models.income import Income
from src.models.expense import Expense
from src.models.employee import Salary # Corrected import for Salary model
from src.models.inventory_item import InventoryItem
from datetime import datetime, date
import csv
import io
from sqlalchemy import func, extract

reports_bp = Blueprint("reports_bp", __name__)

# Helper to get date range from request args
def get_date_range(args):
    start_date_str = args.get("start_date")
    end_date_str = args.get("end_date")
    
    start_date, end_date = None, None
    try:
        if start_date_str:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        if end_date_str:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("Invalid date format. Please use YYYY-MM-DD.")
    
    return start_date, end_date

@reports_bp.route("/reports/profit_and_loss", methods=["GET"])
def profit_and_loss_report():
    try:
        start_date, end_date = get_date_range(request.args)
    except ValueError as e:
        return jsonify({"message": str(e)}), 400

    # Total Income
    income_query = db.session.query(func.sum(Income.amount).label("total_income"))
    if start_date:
        income_query = income_query.filter(Income.date_received >= start_date)
    if end_date:
        income_query = income_query.filter(Income.date_received <= end_date)
    total_income = income_query.scalar() or 0.0

    # Total Expenses (excluding salaries, as they are handled separately for P&L)
    expense_query = db.session.query(func.sum(Expense.amount).label("total_expenses"))
    if start_date:
        expense_query = expense_query.filter(Expense.date_incurred >= start_date)
    if end_date:
        expense_query = expense_query.filter(Expense.date_incurred <= end_date)
    total_general_expenses = expense_query.scalar() or 0.0

    # Total Salaries Paid
    salary_query = db.session.query(func.sum(Salary.gross_amount).label("total_salaries")) # Using gross for P&L
    if start_date:
        salary_query = salary_query.filter(Salary.payment_date >= start_date)
    if end_date:
        salary_query = salary_query.filter(Salary.payment_date <= end_date)
    total_salaries_paid = salary_query.scalar() or 0.0

    total_expenses = total_general_expenses + total_salaries_paid
    profit_or_loss = total_income - total_expenses

    report_data = {
        "report_type": "Profit and Loss Statement",
        "start_date": start_date.isoformat() if start_date else "Beginning of time",
        "end_date": end_date.isoformat() if end_date else "Today",
        "total_income": total_income,
        "total_general_expenses": total_general_expenses,
        "total_salaries_paid": total_salaries_paid,
        "total_expenses": total_expenses,
        "profit_or_loss": profit_or_loss
    }
    return jsonify(report_data), 200

@reports_bp.route("/reports/expense_report", methods=["GET"])
def expense_summary_report():
    try:
        start_date, end_date = get_date_range(request.args)
    except ValueError as e:
        return jsonify({"message": str(e)}), 400

    expense_query = db.session.query(
        Expense.category,
        func.sum(Expense.amount).label("total_amount_for_category")
    ).group_by(Expense.category)
    
    if start_date:
        expense_query = expense_query.filter(Expense.date_incurred >= start_date)
    if end_date:
        expense_query = expense_query.filter(Expense.date_incurred <= end_date)
    
    expenses_by_category = expense_query.all()
    total_expenses = sum(e.total_amount_for_category for e in expenses_by_category)

    report_data = {
        "report_type": "Expense Report by Category",
        "start_date": start_date.isoformat() if start_date else "Beginning of time",
        "end_date": end_date.isoformat() if end_date else "Today",
        "expenses_by_category": [
            {"category": e.category if e.category else "Uncategorized", "total_amount": e.total_amount_for_category}
            for e in expenses_by_category
        ],
        "total_expenses": total_expenses
    }
    return jsonify(report_data), 200

@reports_bp.route("/reports/income_report", methods=["GET"])
def income_summary_report():
    try:
        start_date, end_date = get_date_range(request.args)
    except ValueError as e:
        return jsonify({"message": str(e)}), 400

    income_query = db.session.query(
        Income.category,
        func.sum(Income.amount).label("total_amount_for_category")
    ).group_by(Income.category)

    if start_date:
        income_query = income_query.filter(Income.date_received >= start_date)
    if end_date:
        income_query = income_query.filter(Income.date_received <= end_date)
        
    income_by_category = income_query.all()
    total_income = sum(i.total_amount_for_category for i in income_by_category)

    report_data = {
        "report_type": "Income Report by Category",
        "start_date": start_date.isoformat() if start_date else "Beginning of time",
        "end_date": end_date.isoformat() if end_date else "Today",
        "income_by_category": [
            {"category": i.category if i.category else "Uncategorized", "total_amount": i.total_amount_for_category}
            for i in income_by_category
        ],
        "total_income": total_income
    }
    return jsonify(report_data), 200

@reports_bp.route("/reports/inventory_report", methods=["GET"])
def inventory_summary_report():
    # This report shows current stock levels and values. Date range might not be as relevant here
    # unless tracking historical inventory, which is more complex.
    # For now, a current snapshot.
    inventory_items = InventoryItem.query.order_by(InventoryItem.name).all()
    
    report_items = []
    total_inventory_value_at_sale_price = 0
    total_inventory_value_at_purchase_price = 0

    for item in inventory_items:
        value_at_sale = item.quantity_on_hand * item.sale_price
        value_at_purchase = item.quantity_on_hand * item.purchase_price if item.purchase_price is not None else 0
        report_items.append({
            "id": item.id,
            "name": item.name,
            "sku": item.sku,
            "quantity_on_hand": item.quantity_on_hand,
            "sale_price": item.sale_price,
            "purchase_price": item.purchase_price,
            "total_value_at_sale_price": value_at_sale,
            "total_value_at_purchase_price": value_at_purchase
        })
        total_inventory_value_at_sale_price += value_at_sale
        if item.purchase_price is not None:
            total_inventory_value_at_purchase_price += value_at_purchase

    report_data = {
        "report_type": "Inventory Summary Report",
        "generated_at": datetime.utcnow().isoformat(),
        "items": report_items,
        "total_items_in_stock": sum(item["quantity_on_hand"] for item in report_items),
        "total_inventory_value_at_sale_price": total_inventory_value_at_sale_price,
        "total_inventory_value_at_purchase_price": total_inventory_value_at_purchase_price
    }
    return jsonify(report_data), 200

# --- CSV Export Endpoints ---

@reports_bp.route("/export/income", methods=["GET"])
def export_income_csv():
    try:
        start_date, end_date = get_date_range(request.args)
    except ValueError as e:
        return jsonify({"message": str(e)}), 400

    query = Income.query
    if start_date: query = query.filter(Income.date_received >= start_date)
    if end_date: query = query.filter(Income.date_received <= end_date)
    income_records = query.order_by(Income.date_received.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Description", "Amount", "Date Received", "Category", "Notes", "User ID", "Created At"])
    for record in income_records:
        writer.writerow([
            record.id, record.description, record.amount, record.date_received.isoformat(), 
            record.category, record.notes, record.user_id, record.created_at.isoformat()
        ])
    
    response = Response(output.getvalue(), mimetype="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=income_export.csv"
    return response

@reports_bp.route("/export/expenses", methods=["GET"])
def export_expenses_csv():
    try:
        start_date, end_date = get_date_range(request.args)
    except ValueError as e:
        return jsonify({"message": str(e)}), 400

    query = Expense.query
    if start_date: query = query.filter(Expense.date_incurred >= start_date)
    if end_date: query = query.filter(Expense.date_incurred <= end_date)
    expense_records = query.order_by(Expense.date_incurred.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Description", "Amount", "Date Incurred", "Category", "Vendor", "Notes", "User ID", "Created At"])
    for record in expense_records:
        writer.writerow([
            record.id, record.description, record.amount, record.date_incurred.isoformat(),
            record.category, record.vendor, record.notes, record.user_id, record.created_at.isoformat()
        ])
    
    response = Response(output.getvalue(), mimetype="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=expenses_export.csv"
    return response

@reports_bp.route("/export/inventory", methods=["GET"])
def export_inventory_csv():
    inventory_items = InventoryItem.query.order_by(InventoryItem.name).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Name", "Description", "SKU", "Purchase Price", "Sale Price", "Quantity on Hand", "Unit of Measure", "Created At", "Updated At"])
    for item in inventory_items:
        writer.writerow([
            item.id, item.name, item.description, item.sku, item.purchase_price, item.sale_price,
            item.quantity_on_hand, item.unit_of_measure, item.created_at.isoformat(), item.updated_at.isoformat()
        ])
    response = Response(output.getvalue(), mimetype="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=inventory_export.csv"
    return response

