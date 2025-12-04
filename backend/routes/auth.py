from flask import Blueprint, request, jsonify
import jwt
from datetime import datetime, timedelta
from functools import wraps
from models import db
from models.user import User
from config import Config

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]
            except IndexError:
                return jsonify({'message': 'Token format invalid'}), 401
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        try:
            data = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
            if not current_user:
                return jsonify({'message': 'User not found'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Username and password are required'}), 400
    
    user = User.query.filter_by(username=data['username']).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({'message': 'Invalid credentials'}), 401
    
    # Generate JWT token
    token = jwt.encode({
        'user_id': user.id,
        'exp': datetime.utcnow() + Config.JWT_ACCESS_TOKEN_EXPIRES
    }, Config.JWT_SECRET_KEY, algorithm='HS256')
    
    return jsonify({
        'token': token,
        'user': user.to_dict()
    }), 200

@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout(current_user):
    # In a stateless JWT system, logout is handled client-side
    return jsonify({'message': 'Logged out successfully'}), 200

@auth_bp.route('/me', methods=['GET'])
@token_required
def get_current_user(current_user):
    return jsonify(current_user.to_dict()), 200
