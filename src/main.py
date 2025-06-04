import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, jsonify, request
from src.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, JWTManager
from flask_migrate import Migrate
from flask_cors import CORS # Import CORS

# Import models
from src.models.user import User, RoleEnum
from src.models.income import Income
from src.models.expense import Expense
from src.models.inventory_item import InventoryItem
from src.models.invoice import Invoice, InvoiceItem
from src.models.employee import Employee
from src.models.salary import Salary # Import Salary from its new file
from datetime import datetime # For hire_date parsing
# Import other models here as they are created

# Import blueprints
from src.routes.user import user_bp
from src.routes.income_bp import income_bp
from src.routes.expense_bp import expense_bp
from src.routes.inventory_bp import inventory_bp
from src.routes.invoice_bp import invoice_bp
from src.routes.employee_bp import employee_bp
from src.routes.reports_bp import reports_bp 
from src.routes.company_bp import company_bp # Import the company blueprint

from src.seeder.db_seed import register_seed_commands # Import the seeder function
from sqlalchemy.exc import IntegrityError



app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'), instance_relative_config=True)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a_very_secret_key_that_should_be_changed_in_production')
app.config["JWT_SECRET_KEY"] = os.environ.get('JWT_SECRET_KEY', "another_super_secret_jwt_key_change_me") # Change this in your environment!

# Configure SQLite database
# Ensure the instance folder exists
os.makedirs(app.instance_path, exist_ok=True)
db_path = os.path.join(app.instance_path, 'accounting_database.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
jwt = JWTManager(app)

# Initialize CORS
# For development, you can allow all origins:
CORS(app)
# For production, you should restrict origins:
# CORS(app, resources={r"/api/*": {"origins": "https://your-frontend-domain.com"}})

migrate = Migrate(app, db)

# Register seed commands
register_seed_commands(app)

# Register Blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(company_bp, url_prefix='/api') 
app.register_blueprint(income_bp, url_prefix='/api/companies/<int:company_id>')
app.register_blueprint(expense_bp, url_prefix='/api/companies/<int:company_id>')
app.register_blueprint(inventory_bp, url_prefix='/api/companies/<int:company_id>')
app.register_blueprint(invoice_bp, url_prefix='/api/companies/<int:company_id>')
app.register_blueprint(employee_bp, url_prefix='/api/companies/<int:company_id>')
app.register_blueprint(reports_bp, url_prefix='/api/companies/<int:company_id>') # Make reports company-scoped

# Basic User Registration and Login (Example - to be moved to auth blueprint)
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password') or not data.get('email'):
        return jsonify({'message': 'Username, email, and password are required'}), 400
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'message': 'Username already exists'}), 400
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already exists'}), 400
    
    new_user = User(username=data['username'], email=data['email'])
    new_user.set_password(data['password'])
    new_user.role = RoleEnum.USER  # Default role is USER, can be overridden later
    db.session.add(new_user)
    
    try:
        db.session.commit()
        # If you want to return the user's ID or other details:
        # return jsonify({'message': 'User registered successfully', 'user_id': new_user.id}), 201
        return jsonify({'message': 'User registered successfully'}), 201 # Original response
    except IntegrityError:
        db.session.rollback()
        return jsonify({'message': 'Database error during registration.'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Email and password are required'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    if not user or not user.check_password(data['password']):
        return jsonify({'message': 'Invalid email or password'}), 401
    
    # Identity can be any data that is json serializable
    access_token = create_access_token(identity=str(user.id)) # Cast user.id to string
    return jsonify(access_token=access_token, user_id=user.id, role=user.role.value if user.role else None), 200

@app.route('/api/health', methods=['GET'])
def health_check():
    """Simple health check endpoint."""
    return jsonify({"status": "ok"}), 200

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return f"Welcome to the Minimal Accounting Software! DB: {db_path}. API endpoints available at /api/..., including /api/reports/profit_and_loss etc.", 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
