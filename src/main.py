import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, jsonify, request
from src.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate

# Import models
from src.models.user import User
from src.models.income import Income
from src.models.expense import Expense
from src.models.inventory_item import InventoryItem
from src.models.invoice import Invoice, InvoiceItem
from src.models.employee import Employee, Salary
# Import other models here as they are created

# Import blueprints
from src.routes.user import user_bp
from src.routes.income_bp import income_bp
from src.routes.expense_bp import expense_bp
from src.routes.inventory_bp import inventory_bp
from src.routes.invoice_bp import invoice_bp
from src.routes.employee_bp import employee_bp
from src.routes.reports_bp import reports_bp # Added reports_bp
# from src.routes.auth import auth_bp # Example for auth blueprint

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'), instance_relative_config=True)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a_very_secret_key_that_should_be_changed_in_production')

# Configure SQLite database
os.makedirs(app.instance_path, exist_ok=True)
db_path = os.path.join(app.instance_path, 'accounting_database.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)

# Register Blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(income_bp, url_prefix='/api')
app.register_blueprint(expense_bp, url_prefix='/api')
app.register_blueprint(inventory_bp, url_prefix='/api')
app.register_blueprint(invoice_bp, url_prefix='/api')
app.register_blueprint(employee_bp, url_prefix='/api')
app.register_blueprint(reports_bp, url_prefix='/api') # Registered reports_bp
# app.register_blueprint(auth_bp, url_prefix='/auth')

# Basic User Registration and Login (Example - to be moved to auth blueprint)
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Username and password are required'}), 400
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'message': 'Username already exists'}), 400
    
    new_user = User(username=data['username'])
    new_user.set_password(data['password'])
    if data.get('role'): # Optional role assignment
        new_user.role = data.get('role')
        
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Username and password are required'}), 400
    
    user = User.query.filter_by(username=data['username']).first()
    if not user or not user.check_password(data['password']):
        return jsonify({'message': 'Invalid username or password'}), 401
    
    # In a real app, you would return a JWT token or set a session cookie here
    return jsonify({'message': 'Login successful', 'user_id': user.id, 'role': user.role}), 200

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

with app.app_context():
    db.create_all() # Create database tables for all models imported

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

