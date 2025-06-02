from src.extensions import db
from datetime import datetime, date
from .salary import Salary # Import the Salary model from its new file

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

    # Foreign key to the company this employee belongs to
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)

    # Foreign key to User model for one-to-one relationship
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=True)

    # --- Relationships ---
    # Relationship to Salaries
    salaries = db.relationship("Salary", backref="employee", lazy="dynamic", cascade="all, delete-orphan")
    # Relationship to Company
    company = db.relationship("Company", back_populates="employees")
    # Relationship to User
    user = db.relationship("User", back_populates="employee_profile", uselist=False)

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
            "created_at": self.created_at.isoformat(),
            "user_id": self.user_id,
            "company_id": self.company_id
        }
