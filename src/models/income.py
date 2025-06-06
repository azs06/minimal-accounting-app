from src.extensions import db
from datetime import datetime

class Income(db.Model):
    __tablename__ = "income"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    description = db.Column(db.Text, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date_received = db.Column(db.Date, nullable=False)
    category = db.Column(db.String(100))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)

    # --- Relationships ---
    # User who recorded this income
    recorder = db.relationship("User", back_populates="income_records")
    company = db.relationship("Company", back_populates="income_records")

    def __repr__(self):
        return f"<Income {self.id}: {self.description} - {self.amount}>"

    def to_dict(self):
        return {
            "id": self.id,
            "description": self.description,
            "amount": self.amount,
            "date_received": self.date_received.isoformat(),
            "category": self.category,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "user_id": self.user_id,
            "company_id": self.company_id
        }
