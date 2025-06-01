from flask import Blueprint, request, jsonify
from src.extensions import db
from src.models.inventory_item import InventoryItem


inventory_bp = Blueprint("inventory_bp", __name__)

# Add sample product if inventory is empty (for demo purposes as per knowledge module)
def add_sample_products_if_empty():
    if InventoryItem.query.count() == 0:
        sample_products = [
            InventoryItem(name="Laptop Model X", description="High-performance laptop", sku="LPX001", purchase_price=800.00, sale_price=1200.00, quantity_on_hand=50, unit_of_measure="pcs"),
            InventoryItem(name="Wireless Mouse", description="Ergonomic wireless mouse", sku="MOU007", purchase_price=15.00, sale_price=25.00, quantity_on_hand=200, unit_of_measure="pcs"),
            InventoryItem(name="Software License A", description="Annual license for Software A", sku="SFT001A", purchase_price=0, sale_price=99.99, quantity_on_hand=1000, unit_of_measure="license"),
            InventoryItem(name="Consulting Service", description="Hourly consulting rate", sku="SVC001H", purchase_price=0, sale_price=75.00, quantity_on_hand=9999, unit_of_measure="hour")
        ]
        db.session.add_all(sample_products)
        db.session.commit()
        print("Added sample products to inventory.")
# Recommendation: Call add_sample_products_if_empty() during app initialization
# or via a CLI command, not directly within a GET route.

@inventory_bp.route("/inventory", methods=["POST"])
def add_inventory_item():
    data = request.get_json()
    if not data or not data.get("name") or data.get("sale_price") is None:
        return jsonify({"message": "Missing required fields (name, sale_price)"}), 400
    
    if InventoryItem.query.filter_by(name=data["name"]).first():
        return jsonify({"message": f"Inventory item with name {data['name']} already exists"}), 400
    if data.get("sku") and InventoryItem.query.filter_by(sku=data["sku"]).first():
        return jsonify({"message": f"Inventory item with SKU {data['sku']} already exists"}), 400

    try:
        sale_price = float(data["sale_price"])
        if sale_price < 0:
             return jsonify({"message": "Sale price cannot be negative"}), 400
        purchase_price = float(data.get("purchase_price", 0.0)) if data.get("purchase_price") is not None else None
        if purchase_price is not None and purchase_price < 0:
            return jsonify({"message": "Purchase price cannot be negative"}), 400
        quantity_on_hand = int(data.get("quantity_on_hand", 0))
        if quantity_on_hand < 0:
            return jsonify({"message": "Quantity on hand cannot be negative"}), 400
    except ValueError:
        return jsonify({"message": "Invalid data format for price or quantity"}), 400

    new_item = InventoryItem(
        name=data["name"],
        description=data.get("description"),
        sku=data.get("sku"),
        purchase_price=purchase_price,
        sale_price=sale_price,
        quantity_on_hand=quantity_on_hand,
        unit_of_measure=data.get("unit_of_measure")
    )
    try:
        db.session.add(new_item)
        db.session.commit()
        return jsonify(new_item.to_dict()), 201
    except Exception as e: # Catch potential db errors
        db.session.rollback()
        return jsonify({"message": "Failed to add inventory item", "error": str(e)}), 500

@inventory_bp.route("/inventory", methods=["GET"])
def get_all_inventory_items():
    # Consider removing add_sample_products_if_empty() from here.
    # It's better to handle sample data during app setup or via a separate script.
    # If you keep it for demo purposes, be aware of its side effects on a GET request.
    items = InventoryItem.query.all()
    return jsonify([item.to_dict() for item in items]), 200


@inventory_bp.route("/inventory/<int:item_id>", methods=["GET"])
def get_inventory_item(item_id):
    item = InventoryItem.query.get_or_404(item_id)
    return jsonify(item.to_dict()), 200

@inventory_bp.route("/inventory/<int:item_id>", methods=["PUT"])
def update_inventory_item(item_id):
    item = InventoryItem.query.get_or_404(item_id)
    data = request.get_json()

    if data.get("name"):
        # Check if new name already exists for another item
        existing_item_with_name = InventoryItem.query.filter(InventoryItem.id != item_id, InventoryItem.name == data["name"]).first()
        if existing_item_with_name:
            return jsonify({"message": f"Inventory item with name {data['name']} already exists"}), 400
        item.name = data["name"]
    
    if data.get("sku"):
        # Check if new SKU already exists for another item
        existing_item_with_sku = InventoryItem.query.filter(InventoryItem.id != item_id, InventoryItem.sku == data["sku"]).first()
        if existing_item_with_sku:
            return jsonify({"message": f"Inventory item with SKU {data['sku']} already exists"}), 400
        item.sku = data["sku"]

    if data.get("description"):
        item.description = data["description"]
    if data.get("purchase_price") is not None:
        try:
            purchase_price = float(data["purchase_price"])
            if purchase_price < 0:
                return jsonify({"message": "Purchase price cannot be negative"}), 400
            item.purchase_price = purchase_price
        except ValueError:
            return jsonify({"message": "Invalid purchase_price format"}), 400
    if data.get("sale_price") is not None:
        try:
            sale_price = float(data["sale_price"])
            if sale_price < 0:
                return jsonify({"message": "Sale price cannot be negative"}), 400
            item.sale_price = sale_price
        except ValueError:
            return jsonify({"message": "Invalid sale_price format"}), 400
    if data.get("quantity_on_hand") is not None:
        try:
            quantity = int(data["quantity_on_hand"])
            if quantity < 0:
                return jsonify({"message": "Quantity on hand cannot be negative"}), 400
            item.quantity_on_hand = quantity
        except ValueError:
            return jsonify({"message": "Invalid quantity_on_hand format"}), 400
    if data.get("unit_of_measure"):
        item.unit_of_measure = data["unit_of_measure"]
    
    try:
        db.session.commit()
        return jsonify(item.to_dict()), 200
    except Exception as e: # Catch potential db errors
        db.session.rollback()
        return jsonify({"message": "Failed to update inventory item", "error": str(e)}), 500

@inventory_bp.route("/inventory/<int:item_id>", methods=["DELETE"])
def delete_inventory_item(item_id):
    item = InventoryItem.query.get_or_404(item_id)
    try:
        db.session.delete(item)
        db.session.commit()
        return '', 204
    except Exception as e: # Catch potential db errors
        db.session.rollback()
        return jsonify({"message": "Failed to delete inventory item", "error": str(e)}), 500
