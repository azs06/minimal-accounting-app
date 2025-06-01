from flask import Blueprint, jsonify, request
from src.models.user import User, db
from werkzeug.security import check_password_hash # generate_password_hash is in User model
from sqlalchemy.exc import IntegrityError

user_bp = Blueprint('user', __name__)

@user_bp.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])

@user_bp.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    if not data:
        return jsonify({"message": "Request body must be JSON"}), 400

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({"message": "Missing required fields (username, email, password)"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"message": f"User with username '{username}' already exists"}), 409
    if User.query.filter_by(email=email).first():
        return jsonify({"message": f"User with email '{email}' already exists"}), 409

    new_user = User(username=username, email=email)
    new_user.set_password(password)

    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify(new_user.to_dict()), 201
    except IntegrityError: # Should be caught by above checks, but as a safeguard
        db.session.rollback()
        return jsonify({"message": "Database error: User with that username or email might already exist."}), 409

@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())

@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()

    if not data:
        return jsonify({"message": "Request body must be JSON"}), 400

    if 'username' in data and data['username'] != user.username:
        if User.query.filter(User.id != user_id, User.username == data['username']).first():
            return jsonify({"message": f"Username '{data['username']}' is already taken"}), 409
        user.username = data['username']

    if 'email' in data and data['email'] != user.email:
        if User.query.filter(User.id != user_id, User.email == data['email']).first():
            return jsonify({"message": f"Email '{data['email']}' is already in use"}), 409
        user.email = data['email']

    if 'password' in data:
        # For a real app, you might want to require the old password
        # or have this as a separate, more privileged action.
        if not data['password']:
             return jsonify({"message": "New password cannot be empty"}), 400
        user.set_password(data['password'])

    if 'role' in data: # Allow role updates if necessary, potentially with authorization checks
        user.role = data['role']

    try:
        db.session.commit()
        return jsonify(user.to_dict()), 200
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Database error during update. Username or email might conflict."}), 409

@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return '', 204
