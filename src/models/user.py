from src.extensions import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from .company import company_users # Import the association table

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False) # Increased length for stronger hashes
    role = db.Column(db.String(50), nullable=True, default='user') # System-level role: e.g., 'system_admin', 'user'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # --- Relationships ---
    # Companies this user owns (one-to-many)
    owned_companies = db.relationship("Company", back_populates="owner", lazy="dynamic", foreign_keys="Company.owner_id")

    # Companies this user is a member of (many-to-many)
    member_of_companies = db.relationship("Company", secondary=company_users, back_populates="members", lazy="dynamic")

    # Employee profile linked to this user (one-to-one)
    employee_profile = db.relationship("Employee", back_populates="user", uselist=False)

    # Records created by this user (these indicate who *recorded* the item within a company context)
    income_records = db.relationship("Income", back_populates="recorder", lazy="dynamic")
    expense_records = db.relationship("Expense", back_populates="recorder", lazy="dynamic")
    invoices_created = db.relationship("Invoice", back_populates="creator", lazy="dynamic")
    salaries_recorded = db.relationship("Salary", back_populates="recorder", lazy="dynamic", foreign_keys="Salary.recorded_by_user_id")


    def __repr__(self):
        return f"<User {self.username}>"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role, # System-level role
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "employee_id": self.employee_profile.id if self.employee_profile else None,
            # "owned_company_ids": [c.id for c in self.owned_companies],
            # "member_of_company_ids": [c.id for c in self.member_of_companies]
        }
