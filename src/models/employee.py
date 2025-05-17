from src.extensions import db
from datetime import datetime, date

class Employee(db.Model):
    __tablename__ = "employees"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True)
    phone_number = db.Column(db.String(50))
    position = db.Column(db.String(100))
    hire_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to Salaries
    salaries = db.relationship("Salary", backref="employee", lazy="dynamic", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Employee {self.id}: {self.first_name} {self.last_name} - {self.position}>"

    def to_dict(self):
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "phone_number": self.phone_number,
            "position": self.position,
            "hire_date": self.hire_date.isoformat() if self.hire_date else None,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat()
        }

class Salary(db.Model):
    __tablename__ = "salaries"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    payment_date = db.Column(db.Date, nullable=False)
    gross_amount = db.Column(db.Float, nullable=False)
    deductions = db.Column(db.Float, default=0.0)
    net_amount = db.Column(db.Float, nullable=False)
    payment_period_start = db.Column(db.Date)
    payment_period_end = db.Column(db.Date)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    recorded_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Relationship to User who recorded it
    # recorder = db.relationship("User", back_populates="salaries_recorded")

    def __repr__(self):
        return f"<Salary {self.id} for Employee {self.employee_id} - Net: {self.net_amount} on {self.payment_date}>"
    
    def calculate_net_amount(self):
        self.net_amount = self.gross_amount - self.deductions
        return self.net_amount

    def to_dict(self):
        return {
            "id": self.id,
            "employee_id": self.employee_id,
            "payment_date": self.payment_date.isoformat() if self.payment_date else None,
            "gross_amount": self.gross_amount,
            "deductions": self.deductions,
            "net_amount": self.net_amount,
            "payment_period_start": self.payment_period_start.isoformat() if self.payment_period_start else None,
            "payment_period_end": self.payment_period_end.isoformat() if self.payment_period_end else None,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "recorded_by_user_id": self.recorded_by_user_id
        }

