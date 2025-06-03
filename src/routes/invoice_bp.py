from flask import Blueprint, request, jsonify
from src.extensions import db
from src.models.invoice import Invoice, InvoiceItem
from src.models.inventory_item import InventoryItem as Product # Alias for clarity
from src.models.company import Company
from src.models.user import User # Though _get_current_user returns User object
from src.models.enums import CompanyRoleEnum, RoleEnum
from datetime import datetime, date
from flask_jwt_extended import jwt_required # get_jwt_identity is in _get_current_user
import shortuuid # For generating unique invoice numbers
from src.routes.company_bp import _get_current_user, _check_permission # Re-use helper functions

invoice_bp = Blueprint("invoice_bp", __name__)

# Helper to generate unique invoice number
def generate_invoice_number(company_id_for_uniqueness):
    prefix = date.today().strftime("INV-%Y%m%d-")
    while True:
        num = prefix + shortuuid.ShortUUID().random(length=4).upper()
        # Check for uniqueness within the specific company
        if not Invoice.query.filter_by(company_id=company_id_for_uniqueness, invoice_number=num).first():
            return num

@invoice_bp.route("/invoices", methods=["POST"])
@jwt_required()
def create_invoice(company_id): # Add company_id from URL
    current_user = _get_current_user()
    if not current_user:
        return jsonify({"message": "Authentication required"}), 401

    company = Company.query.get_or_404(company_id)

    if not _check_permission(current_user, company,
                             allowed_company_roles=[CompanyRoleEnum.ADMIN, CompanyRoleEnum.EDITOR],
                             allow_owner=True,
                             allow_system_admin=True):
        return jsonify({"message": "Unauthorized to create invoices for this company"}), 403

    data = request.get_json()
    if not data or not data.get("customer_name") or not data.get("items"):
        return jsonify({"message": "Missing required fields (customer_name, items)"}), 400

    invoice_number = data.get("invoice_number", generate_invoice_number(company_id))
    # Check for uniqueness within the company
    if Invoice.query.filter_by(company_id=company_id, invoice_number=invoice_number).first():
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
        user_id=current_user.id, # User who created the invoice
        company_id=company_id # Assign to the current company
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
            line_total=line_total
        )
        # Link to inventory item if item_id is provided
        if item_data.get("item_id"):
            product_id = item_data.get("item_id")
            product = Product.query.get(product_id)
            if not product or product.company_id != company_id:
                db.session.rollback()
                return jsonify({"message": f"Product with ID {product_id} not found or does not belong to this company."}), 404
            invoice_item_obj.item_id = product_id

        invoice_item_obj.invoice = new_invoice 
        db.session.add(invoice_item_obj) # Explicitly add item to session

    new_invoice.total_amount = total_invoice_amount
    
    try:
        db.session.commit()
        # TODO: Implement inventory quantity deduction here if invoice is not a draft
        # This should be part of the same transaction or handled carefully.
        # For each item in new_invoice.items:
        #   If item.item_id exists, find Product by item.item_id and decrement quantity_on_hand
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to create invoice", "error": str(e)}), 500

    return jsonify(new_invoice.to_dict()), 201

@invoice_bp.route("/invoices", methods=["GET"])
@jwt_required()
def get_all_invoices(company_id): # Add company_id from URL
    current_user = _get_current_user()
    if not current_user:
        return jsonify({"message": "Authentication required"}), 401

    company = Company.query.get_or_404(company_id)

    if not _check_permission(current_user, company,
                             allowed_company_roles=[CompanyRoleEnum.ADMIN, CompanyRoleEnum.EDITOR, CompanyRoleEnum.VIEWER],
                             allow_owner=True,
                             allow_system_admin=True):
        return jsonify({"message": "Unauthorized to view invoices for this company"}), 403

    invoices = Invoice.query.filter_by(company_id=company_id).order_by(Invoice.issue_date.desc()).all()
    return jsonify([invoice.to_dict() for invoice in invoices]), 200


@invoice_bp.route("/invoices/<int:invoice_id>", methods=["GET"])
@jwt_required()
def get_invoice(company_id, invoice_id): # Add company_id from URL
    current_user = _get_current_user()
    if not current_user:
        return jsonify({"message": "Authentication required"}), 401

    company = Company.query.get_or_404(company_id) # Ensure company exists
    invoice = Invoice.query.get_or_404(invoice_id)

    if invoice.company_id != company_id:
        return jsonify({"message": "Invoice not found in this company"}), 404

    if not _check_permission(current_user, company,
                             allowed_company_roles=[CompanyRoleEnum.ADMIN, CompanyRoleEnum.EDITOR, CompanyRoleEnum.VIEWER],
                             allow_owner=True,
                             allow_system_admin=True):
        return jsonify({"message": "Unauthorized to view this invoice"}), 403

    return jsonify(invoice.to_dict()), 200

@invoice_bp.route("/invoices/<int:invoice_id>", methods=["PUT"])
@jwt_required()
def update_invoice(company_id, invoice_id): # Add company_id from URL
    current_user = _get_current_user()
    if not current_user:
        return jsonify({"message": "Authentication required"}), 401

    company = Company.query.get_or_404(company_id) # Ensure company exists
    invoice = Invoice.query.get_or_404(invoice_id)

    if invoice.company_id != company_id:
        return jsonify({"message": "Invoice not found in this company"}), 404

    if not _check_permission(current_user, company,
                             allowed_company_roles=[CompanyRoleEnum.ADMIN, CompanyRoleEnum.EDITOR],
                             allow_owner=True,
                             allow_system_admin=True):
        return jsonify({"message": "Unauthorized to update this invoice"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"message": "Request body must be JSON"}), 400

    # TODO: Consider implications for inventory if status changes or items are modified
    # (e.g., if invoice was 'Sent' and items are changed, or status becomes 'Paid')
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
                line_total=line_total
            )
            # Link to inventory item if item_id is provided
            if item_data.get("item_id"):
                product_id = item_data.get("item_id")
                product = Product.query.get(product_id)
                if not product or product.company_id != company_id:
                    db.session.rollback()
                    return jsonify({"message": f"Product with ID {product_id} not found or does not belong to this company."}), 404
                new_invoice_item.item_id = product_id

            db.session.add(new_invoice_item) # Explicitly add item to session
        invoice.total_amount = new_total_amount
    else:
        # If items are not part of the payload, recalculate total from existing items
        invoice.calculate_total()

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to update invoice", "error": str(e)}), 500

    return jsonify(invoice.to_dict()), 200

@invoice_bp.route("/invoices/<int:invoice_id>", methods=["DELETE"])
@jwt_required()
def delete_invoice(company_id, invoice_id): # Add company_id from URL
    current_user = _get_current_user()
    if not current_user:
        return jsonify({"message": "Authentication required"}), 401

    company = Company.query.get_or_404(company_id) # Ensure company exists
    invoice = Invoice.query.get_or_404(invoice_id)

    if invoice.company_id != company_id:
        return jsonify({"message": "Invoice not found in this company"}), 404

    if not _check_permission(current_user, company,
                             allowed_company_roles=[CompanyRoleEnum.ADMIN], # Typically only ADMIN or owner can delete
                             allow_owner=True,
                             allow_system_admin=True):
        return jsonify({"message": "Unauthorized to delete this invoice"}), 403

    # The InvoiceItem records will be deleted due to cascade="all, delete-orphan" on Invoice.items
    db.session.delete(invoice) 
    db.session.commit() 
    # TODO: Consider if inventory needs to be restocked if invoice was not a draft
    # (e.g., if items were deducted from inventory previously)
    return '', 204
