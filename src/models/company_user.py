from src.extensions import db
from datetime import datetime
from .enums import CompanyRoleEnum
# Import User model for to_dict_with_user_details, handled carefully to avoid circular import issues if User imports CompanyUser
# It's generally safer if the to_dict method in the association object doesn't try to fetch full related objects by default
# or does so within the method scope.

class CompanyUser(db.Model):
    __tablename__ = 'company_users' # Explicitly naming the table

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), primary_key=True)
    # Use SQLAlchemy's Enum type, storing string values from CompanyRoleEnum
    role_in_company = db.Column(db.Enum(CompanyRoleEnum, name="company_role_enum", native_enum=False), nullable=False, default=CompanyRoleEnum.VIEWER)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    # --- Relationships ---
    user = db.relationship("User", back_populates="company_associations")
    company = db.relationship("Company", back_populates="user_associations")

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "company_id": self.company_id,
            "role_in_company": self.role_in_company.value if self.role_in_company else None,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None
        }

    def to_dict_with_user_details(self):
        # This method is as hinted in company_bp.py. Be mindful of performance if used for lists.
        from .user import User # Local import to avoid circular dependency at module level
        user_details = User.query.get(self.user_id)
        return {
            "user_id": self.user_id,
            "username": user_details.username if user_details else None,
            "email": user_details.email if user_details else None,
            "company_id": self.company_id,
            "role_in_company": self.role_in_company.value if self.role_in_company else None
        }