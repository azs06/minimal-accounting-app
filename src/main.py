import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, jsonify, request
from src.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, JWTManager
from flask_migrate import Migrate

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



app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'), instance_relative_config=True)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a_very_secret_key_that_should_be_changed_in_production')
app.config["JWT_SECRET_KEY"] = os.environ.get('JWT_SECRET_KEY', "another_super_secret_jwt_key_change_me") # Change this in your environment!

# Configure SQLite database
os.makedirs(app.instance_path, exist_ok=True)
db_path = os.path.join(app.instance_path, 'accounting_database.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
jwt = JWTManager(app)
migrate = Migrate(app, db)

# Register seed commands
register_seed_commands(app)

# Register Blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(income_bp, url_prefix='/api')
app.register_blueprint(expense_bp, url_prefix='/api')
app.register_blueprint(inventory_bp, url_prefix='/api')
app.register_blueprint(invoice_bp, url_prefix='/api')
app.register_blueprint(employee_bp, url_prefix='/api')
app.register_blueprint(reports_bp, url_prefix='/api') 

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

    employee_details = data.get('employee_details')
    new_employee = None
    if employee_details:
        if not employee_details.get("first_name") or not employee_details.get("last_name"):
            db.session.rollback()
            return jsonify({"message": "Employee details require first_name and last_name"}), 400
        
        # Check for duplicate employee email if provided and different from user's email
        if employee_details.get("email") and employee_details.get("email") != new_user.email and \
           Employee.query.filter_by(email=employee_details["email"]).first():
            db.session.rollback()
            return jsonify({"message": f"Employee with email {employee_details['email']} already exists"}), 409

        try:
            hire_date_str = employee_details.get("hire_date")
            hire_date = datetime.strptime(hire_date_str, "%Y-%m-%d").date() if hire_date_str else None
        except ValueError:
            db.session.rollback()
            return jsonify({"message": "Invalid hire_date format (YYYY-MM-DD) for employee"}), 400

        new_employee = Employee(
            first_name=employee_details["first_name"],
            last_name=employee_details["last_name"],
            email=employee_details.get("email", new_user.email), # Default to user's email
            phone_number=employee_details.get("phone_number"),
            position=employee_details.get("position"),
            hire_date=hire_date,
            is_active=employee_details.get("is_active", True)
        )
        db.session.add(new_employee)
    
    try:
        db.session.commit()
        if new_employee:
            new_employee.user_id = new_user.id
            db.session.commit()
        return jsonify({'message': 'User registered successfully'}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({'message': 'Database error during registration.'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Username and password are required'}), 400
    
    user = User.query.filter_by(username=data['username']).first()
    if not user or not user.check_password(data['password']):
        return jsonify({'message': 'Invalid username or password'}), 401
    
    # Identity can be any data that is json serializable
    access_token = create_access_token(identity=str(user.id)) # Cast user.id to string
    return jsonify(access_token=access_token, user_id=user.id, role=user.role), 200

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
