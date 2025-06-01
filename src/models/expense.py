from src.extensions import db
from datetime import datetime

class Expense(db.Model):
    __tablename__ = "expenses"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    description = db.Column(db.Text, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date_incurred = db.Column(db.Date, nullable=False)
    category = db.Column(db.String(100))
    vendor = db.Column(db.String(100))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Relationship to User
    recorder = db.relationship("User", back_populates="expense_records")

    def __repr__(self):
        return f"<Expense {self.id}: {self.description} - {self.amount}>"

    def to_dict(self):
        return {
            "id": self.id,
            "description": self.description,
            "amount": self.amount,
            "date_incurred": self.date_incurred.isoformat(),
            "category": self.category,
            "vendor": self.vendor,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "user_id": self.user_id
        }
