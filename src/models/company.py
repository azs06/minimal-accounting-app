from src.extensions import db
from datetime import datetime

# Association table for the many-to-many relationship between User and Company
company_users = db.Table('company_users',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('company_id', db.Integer, db.ForeignKey('companies.id'), primary_key=True),
    db.Column('role_in_company', db.String(50), nullable=False, default='member'), # e.g., 'admin', 'editor', 'viewer'
    db.Column('joined_at', db.DateTime, default=datetime.utcnow)
)

class Company(db.Model):
    __tablename__ = "companies"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(150), nullable=False, unique=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) # User who created/owns the company
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # --- Relationships ---
    # User who owns this company
    owner = db.relationship("User", back_populates="owned_companies", foreign_keys=[owner_id])

    # Users who are members of this company (many-to-many)
    members = db.relationship("User", secondary=company_users, back_populates="member_of_companies", lazy="dynamic")

    # Employees belonging to this company (one-to-many)
    employees = db.relationship("Employee", back_populates="company", lazy="dynamic", cascade="all, delete-orphan")

    # Financial records belonging to this company
    income_records = db.relationship("Income", back_populates="company", lazy="dynamic", cascade="all, delete-orphan")
    expense_records = db.relationship("Expense", back_populates="company", lazy="dynamic", cascade="all, delete-orphan")
    invoices = db.relationship("Invoice", back_populates="company", lazy="dynamic", cascade="all, delete-orphan")
    inventory_items = db.relationship("InventoryItem", back_populates="company", lazy="dynamic", cascade="all, delete-orphan")
    # Salaries are linked via Employee, but if direct access is needed:
    # salaries_paid = db.relationship("Salary", back_populates="company", lazy="dynamic", cascade="all, delete-orphan")


    def __repr__(self):
        return f"<Company {self.id}: {self.name}>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "owner_id": self.owner_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            # "member_count": self.members.count() # Example of adding related data
        }

    def add_member(self, user, role='member'):
        # Helper function to add a user to the company
        # Check if user is already a member might be good here
        self.members.append(user)
        # To set the role, you'd interact with the association object directly or enhance this.