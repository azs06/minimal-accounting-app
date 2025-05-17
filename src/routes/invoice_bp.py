from flask import Blueprint, request, jsonify
from src.extensions import db
from src.models.invoice import Invoice, InvoiceItem
from src.models.inventory_item import InventoryItem as Product # Alias to avoid confusion
from datetime import datetime, date
import shortuuid # For generating unique invoice numbers

# Placeholder for user authentication
MOCK_USER_ID = 1

invoice_bp = Blueprint("invoice_bp", __name__)

# Helper to generate unique invoice number
def generate_invoice_number():
    prefix = date.today().strftime("INV-%Y%m%d-")
    while True:
        num = prefix + shortuuid.ShortUUID().random(length=4).upper()
        if not Invoice.query.filter_by(invoice_number=num).first():
            return num

@invoice_bp.route("/invoices", methods=["POST"])
def create_invoice():
    data = request.get_json()
    if not data or not data.get("customer_name") or not data.get("items"):
        return jsonify({"message": "Missing required fields (customer_name, items)"}), 400

    invoice_number = data.get("invoice_number", generate_invoice_number())
    if Invoice.query.filter_by(invoice_number=invoice_number).first():
        return jsonify({"message": f"Invoice number {invoice_number} already exists. Please use a unique invoice number or let the system generate one."}), 409

    try:
        issue_date_str = data.get("issue_date")
        issue_date = datetime.strptime(issue_date_str, "%Y-%m-%d").date() if issue_date_str else date.today()
        due_date_str = data.get("due_date")
        due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date() if due_date_str else None
    except ValueError:
        return jsonify({"message": "Invalid date format (YYYY-MM-DD) for issue_date or due_date"}), 400

    new_invoice = Invoice(
        invoice_number=invoice_number,
        customer_name=data["customer_name"],
        customer_email=data.get("customer_email"),
        customer_address=data.get("customer_address"),
        issue_date=issue_date,
        due_date=due_date,
        status=data.get("status", "Draft"),
        notes=data.get("notes"),
        user_id=data.get("user_id", MOCK_USER_ID)
    )
    db.session.add(new_invoice)

    total_invoice_amount = 0

    for item_data in data.get("items", []):
        if not item_data.get("item_description") or item_data.get("quantity") is None or item_data.get("unit_price") is None:
            db.session.rollback()
            return jsonify({"message": "Each item must have item_description, quantity, and unit_price"}), 400
        
        try:
            quantity = int(item_data["quantity"])
            unit_price = float(item_data["unit_price"])
            if quantity <= 0 or unit_price < 0:
                db.session.rollback()
                return jsonify({"message": "Item quantity must be positive and unit price non-negative"}), 400
        except ValueError:
            db.session.rollback()
            return jsonify({"message": "Invalid quantity or unit_price format for an item"}), 400

        line_total = quantity * unit_price
        total_invoice_amount += line_total

        invoice_item_obj = InvoiceItem(
            item_description=item_data["item_description"],
            quantity=quantity,
            unit_price=unit_price,
            line_total=line_total,
            item_id=item_data.get("item_id")
        )
        invoice_item_obj.invoice = new_invoice 
        db.session.add(invoice_item_obj) # Explicitly add item to session

    new_invoice.total_amount = total_invoice_amount
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to create invoice", "error": str(e)}), 500

    return jsonify(new_invoice.to_dict()), 201

@invoice_bp.route("/invoices", methods=["GET"])
def get_all_invoices():
    invoices = Invoice.query.order_by(Invoice.issue_date.desc()).all()
    return jsonify([invoice.to_dict() for invoice in invoices]), 200

@invoice_bp.route("/invoices/<int:invoice_id>", methods=["GET"])
def get_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    return jsonify(invoice.to_dict()), 200

@invoice_bp.route("/invoices/<int:invoice_id>", methods=["PUT"])
def update_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    data = request.get_json()

    if "customer_name" in data: invoice.customer_name = data["customer_name"]
    if "customer_email" in data: invoice.customer_email = data["customer_email"]
    if "customer_address" in data: invoice.customer_address = data["customer_address"]
    if "notes" in data: invoice.notes = data["notes"]
    if "status" in data: invoice.status = data["status"]
    
    try:
        if "issue_date" in data:
            invoice.issue_date = datetime.strptime(data["issue_date"], "%Y-%m-%d").date()
        if "due_date" in data:
            invoice.due_date = datetime.strptime(data["due_date"], "%Y-%m-%d").date() if data["due_date"] else None
    except ValueError:
        return jsonify({"message": "Invalid date format (YYYY-MM-DD)"}), 400

    if "items" in data:
        for item in invoice.items.all():
            db.session.delete(item)
        
        new_total_amount = 0
        for item_data in data["items"]:
            if not item_data.get("item_description") or item_data.get("quantity") is None or item_data.get("unit_price") is None:
                db.session.rollback()
                return jsonify({"message": "Each item must have item_description, quantity, and unit_price"}), 400
            try:
                quantity = int(item_data["quantity"])
                unit_price = float(item_data["unit_price"])
                if quantity <= 0 or unit_price < 0:
                    db.session.rollback()
                    return jsonify({"message": "Item quantity must be positive and unit price non-negative"}), 400
            except ValueError:
                db.session.rollback()
                return jsonify({"message": "Invalid quantity or unit_price format for an item"}), 400
            
            line_total = quantity * unit_price
            new_total_amount += line_total
            new_invoice_item = InvoiceItem(
                invoice_id=invoice.id,
                item_description=item_data["item_description"],
                quantity=quantity,
                unit_price=unit_price,
                line_total=line_total,
                item_id=item_data.get("item_id")
            )
            db.session.add(new_invoice_item) # Explicitly add item to session
        invoice.total_amount = new_total_amount
    else:
        invoice.calculate_total()

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to update invoice", "error": str(e)}), 500

    return jsonify(invoice.to_dict()), 200

@invoice_bp.route("/invoices/<int:invoice_id>", methods=["DELETE"])
def delete_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    db.session.delete(invoice)
    db.session.commit()
    return jsonify({"message": "Invoice deleted successfully"}), 200

