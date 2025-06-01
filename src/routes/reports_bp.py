from flask import Blueprint, jsonify, request
from src.extensions import db
from datetime import datetime

# Import your models here to fetch data for reports
from src.models.income import Income
from src.models.expense import Expense
from src.models.invoice import Invoice 
from src.models.inventory_item import InventoryItem
from src.models.employee import Salary, Employee

# It's common to define the blueprint with its own segment of the URL.
# Since it's registered with /api in main.py, and these are report routes,
# a /reports prefix here makes sense, leading to /api/reports/...
reports_bp = Blueprint("reports_bp", __name__, url_prefix="/reports")

@reports_bp.route("/profit_and_loss", methods=["GET"])
def get_profit_and_loss_report():
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    if not start_date_str or not end_date_str:
        return jsonify({"message": "Both start_date and end_date are required parameters."}), 400

    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"message": "Invalid date format. Please use YYYY-MM-DD."}), 400

    if start_date > end_date:
        return jsonify({"message": "Start date cannot be after end date."}), 400

    total_income = db.session.query(db.func.sum(Income.amount)).filter(
        Income.date_received >= start_date,
        Income.date_received <= end_date
    ).scalar() or 0.0

    total_expenses = db.session.query(db.func.sum(Expense.amount)).filter(
        Expense.date_incurred >= start_date,
        Expense.date_incurred <= end_date
    ).scalar() or 0.0

    net_profit_loss = total_income - total_expenses

    return jsonify({
        "report_name": "Profit and Loss",
        "period_start": start_date.isoformat(),
        "period_end": end_date.isoformat(),
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_profit_loss": net_profit_loss
    }), 200

@reports_bp.route("/sales_report", methods=["GET"])
def get_sales_report():
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    if not start_date_str or not end_date_str:
        return jsonify({"message": "Both start_date and end_date are required parameters."}), 400

    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"message": "Invalid date format. Please use YYYY-MM-DD."}), 400

    if start_date > end_date:
        return jsonify({"message": "Start date cannot be after end date."}), 400

    invoices_query = Invoice.query.filter(
        Invoice.issue_date >= start_date,
        Invoice.issue_date <= end_date
    ).order_by(Invoice.issue_date.asc()) # You might also want to filter by status (e.g., 'Paid', 'Sent')
    
    invoices = invoices_query.all()
    total_sales_amount = sum(invoice.total_amount for invoice in invoices)
    
    return jsonify({
        "report_name": "Sales Report",
        "period_start": start_date.isoformat(),
        "period_end": end_date.isoformat(),
        "total_sales_amount": total_sales_amount,
        "number_of_invoices": len(invoices),
        "invoices": [invoice.to_dict() for invoice in invoices]
    }), 200

@reports_bp.route("/expense_report", methods=["GET"])
def get_expense_report():
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    if not start_date_str or not end_date_str:
        return jsonify({"message": "Both start_date and end_date are required parameters."}), 400

    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"message": "Invalid date format. Please use YYYY-MM-DD."}), 400

    if start_date > end_date:
        return jsonify({"message": "Start date cannot be after end date."}), 400

    expenses_query = Expense.query.filter(
        Expense.date_incurred >= start_date,
        Expense.date_incurred <= end_date
    ).order_by(Expense.date_incurred.asc())
    
    expenses = expenses_query.all()
    total_expenses = sum(expense.amount for expense in expenses)
    return jsonify({
        "report_name": "Expense Report",
        "period_start": start_date.isoformat(),
        "period_end": end_date.isoformat(),
        "total_expenses": total_expenses,
        "expense_details": [expense.to_dict() for expense in expenses]
    }), 200

@reports_bp.route("/inventory_summary", methods=["GET"])
def get_inventory_summary():
    inventory_items = InventoryItem.query.order_by(InventoryItem.name.asc()).all()

    report_items = []
    total_inventory_value = 0.0

    for item in inventory_items:
        item_stock_value = (item.sale_price or 0.0) * (item.quantity_on_hand or 0)
        total_inventory_value += item_stock_value
        report_items.append({
            "id": item.id,
            "name": item.name,
            "sku": item.sku,
            "quantity_on_hand": item.quantity_on_hand,
            "sale_price": item.sale_price,
            "current_stock_value_at_sale_price": item_stock_value
        })

    return jsonify({
        "report_name": "Inventory Summary Report",
        "generated_at": datetime.utcnow().isoformat(),
        "total_inventory_value_at_sale_price": total_inventory_value,
        "number_of_items": len(report_items),
        "inventory_details": report_items
    }), 200

@reports_bp.route("/employee_payroll", methods=["GET"])
def get_employee_payroll_summary():
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    if not start_date_str or not end_date_str:
        return jsonify({"message": "Both start_date and end_date are required parameters."}), 400

    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"message": "Invalid date format. Please use YYYY-MM-DD."}), 400

    if start_date > end_date:
        return jsonify({"message": "Start date cannot be after end date."}), 400

    salaries_query = Salary.query.filter(
        Salary.payment_date >= start_date,
        Salary.payment_date <= end_date
    ).order_by(Salary.payment_date.asc(), Salary.employee_id.asc())
    
    salaries = salaries_query.all()

    total_gross_pay = sum(s.gross_amount for s in salaries)
    total_deductions = sum(s.deductions for s in salaries)
    total_net_pay = sum(s.net_amount for s in salaries)

    return jsonify({
        "report_name": "Employee Payroll Summary",
        "period_start": start_date.isoformat(),
        "period_end": end_date.isoformat(),
        "total_gross_pay": total_gross_pay,
        "total_deductions": total_deductions,
        "total_net_pay": total_net_pay,
        "number_of_payments_made": len(salaries),
        "payroll_details": [salary.to_dict() for salary in salaries]
    }), 200