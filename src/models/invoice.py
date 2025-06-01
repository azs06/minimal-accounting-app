from src.extensions import db
from datetime import datetime, date

class Invoice(db.Model):
    __tablename__ = "invoices"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    invoice_number = db.Column(db.String(100), unique=True, nullable=False)
    customer_name = db.Column(db.String(200), nullable=False)
    customer_email = db.Column(db.String(120))
    customer_address = db.Column(db.Text)
    issue_date = db.Column(db.Date, nullable=False, default=date.today)
    due_date = db.Column(db.Date)
    total_amount = db.Column(db.Float, nullable=False, default=0.0)
    status = db.Column(db.String(50), nullable=False, default="Draft")  # e.g., Draft, Sent, Paid, Overdue, Cancelled
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Relationship to User
    creator = db.relationship("User", back_populates="invoices_created")
    # Relationship to InvoiceItem
    items = db.relationship("InvoiceItem", backref="invoice", lazy="dynamic", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Invoice {self.invoice_number} - {self.customer_name} - Status: {self.status}>"

    def calculate_total(self):
        self.total_amount = sum(item.line_total for item in self.items)
        return self.total_amount

    def to_dict(self):
        return {
            "id": self.id,
            "invoice_number": self.invoice_number,
            "customer_name": self.customer_name,
            "customer_email": self.customer_email,
            "customer_address": self.customer_address,
            "issue_date": self.issue_date.isoformat() if self.issue_date else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "total_amount": self.total_amount,
            "status": self.status,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "user_id": self.user_id,
            "items": [item.to_dict() for item in self.items.all()] # Serialize items
        }

class InvoiceItem(db.Model):
    __tablename__ = "invoice_items"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey("inventory_items.id"), nullable=True) # Can be NULL for custom items
    item_description = db.Column(db.Text, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    line_total = db.Column(db.Float, nullable=False)

    # Relationship to InventoryItem (optional, if you need to access inventory_item from invoice_item directly)
    inventory_item = db.relationship("InventoryItem", back_populates="invoice_lines")

    def __repr__(self):
        return f"<InvoiceItem {self.id} for Invoice {self.invoice_id} - {self.item_description} Qty: {self.quantity}>"
    
    def calculate_line_total(self):
        self.line_total = self.quantity * self.unit_price
        return self.line_total

    def to_dict(self):
        return {
            "id": self.id,
            "invoice_id": self.invoice_id,
            "item_id": self.item_id,
            "item_description": self.item_description,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "line_total": self.line_total
        }
