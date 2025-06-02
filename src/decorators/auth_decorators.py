from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from src.models.user import User, RoleEnum # Import RoleEnum

def system_admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request() # Ensures a valid JWT is present
        current_user_id_str = get_jwt_identity()
        try:
            current_user_id = int(current_user_id_str)
        except ValueError:
            return jsonify(message="Invalid user identity in token"), 401
            
        user = User.query.get(current_user_id)
        if not user or user.role != RoleEnum.SYSTEM_ADMIN: # Check only for SYSTEM_ADMIN
            return jsonify(message="System administrator access required"), 403
        return fn(*args, **kwargs)
    return wrapper