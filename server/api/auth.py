import bcrypt
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

from models.user import User

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400
    
    username = request.json.get('username', None)
    password = request.json.get('password', None)
    
    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400
    
    # Check if user already exists
    if User.find_by_username(username):
        return jsonify({"error": "Username already exists"}), 400
    
    # Hash the password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    # Create new user
    user = User(username=username, password=hashed_password.decode('utf-8'))
    user.save()
    
    # Create access token
    access_token = create_access_token(identity=username)
    
    return jsonify({"message": "User created successfully", "access_token": access_token}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400
    
    username = request.json.get('username', None)
    password = request.json.get('password', None)
    
    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400
    
    # Find user
    user = User.find_by_username(username)
    
    if not user or not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
        return jsonify({"error": "Invalid username or password"}), 401
    
    # Create access token
    access_token = create_access_token(identity=username)
    
    return jsonify({"message": "Login successful", "access_token": access_token}), 200

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    current_user = get_jwt_identity()
    user = User.find_by_username(current_user)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify({"username": user.username}), 200 