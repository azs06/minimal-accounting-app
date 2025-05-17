from src.extensions import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = "users"
    
    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False) # Increased length for stronger hashes
    role = db.Column(db.String(50), nullable=True, default='user') # e.g., 'admin', 'user'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships - to be added as other models are created
    # income_records = db.relationship(	ext'Income	ext', backref=	ext'recorder	ext', lazy=True)
    # expense_records = db.relationship(	ext'Expense	ext', backref=	ext'recorder	ext', lazy=True)
    # invoices_created = db.relationship(	ext'Invoice	ext', backref=	ext'creator	ext', lazy=True)
    # salaries_recorded = db.relationship(	ext'Salary	ext', backref=	ext'recorder	ext', lazy=True)

    def __repr__(self):
        return f"<User {self.username}>"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

