from src.extensions import db
from datetime import datetime

class InventoryItem(db.Model):
    __tablename__ = "inventory_items"

    # To ensure SKU and Name are unique per company, we use __table_args__
    __table_args__ = (
        db.UniqueConstraint('company_id', 'sku', name='uq_inventory_company_sku'),
        db.UniqueConstraint('company_id', 'name', name='uq_inventory_company_name'),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(200), nullable=False) # Unique constraint handled by __table_args__
    description = db.Column(db.Text)
    sku = db.Column(db.String(100))  # Stock Keeping Unit, Unique constraint handled by __table_args__
    purchase_price = db.Column(db.Float)  # Cost to acquire the item
    sale_price = db.Column(db.Float, nullable=False)  # Price at which the item is sold
    quantity_on_hand = db.Column(db.Integer, nullable=False, default=0)
    unit_of_measure = db.Column(db.String(50))  # e.g., 'pcs', 'kg', 'hour'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)

    # --- Relationships ---
    # Company this inventory item belongs to
    company = db.relationship("Company", back_populates="inventory_items")
    # Relationship with InvoiceItem
    invoice_lines = db.relationship('InvoiceItem', back_populates='inventory_item', lazy='dynamic') # Changed to lazy='dynamic' for consistency if you expect to filter/query these


    def __repr__(self):
        return f"<InventoryItem {self.id}: {self.name} (SKU: {self.sku}) - Qty: {self.quantity_on_hand}>"

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'sku': self.sku,
            'purchase_price': self.purchase_price,
            'sale_price': self.sale_price,
            'quantity_on_hand': self.quantity_on_hand,
            'unit_of_measure': self.unit_of_measure,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'company_id': self.company_id
        }
