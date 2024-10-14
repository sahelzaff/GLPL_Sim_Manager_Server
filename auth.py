from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from db_connection import get_db_connection
from datetime import datetime, timedelta
import jwt
import os

auth_bp = Blueprint('auth', __name__)

# Secret key for JWT
SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your-secret-key')  # Use an environment variable in production

# Function to generate a token
def generate_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=1)  # Token expires in 1 day
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

# Function to verify a token
def verify_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        return None  # Token has expired
    except jwt.InvalidTokenError:
        return None  # Invalid token

# Route to register a new user
@auth_bp.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({'error': 'All fields are required'}), 400

    # Hash the password
    password_hash = generate_password_hash(password)

    conn = get_db_connection()
    cursor = conn.cursor()

    # Insert user into the database
    try:
        cursor.execute("""
            INSERT INTO users_phonebook_web (username, email, password_hash, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (username, email, password_hash, datetime.now(), datetime.now()))
        conn.commit()
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

    return jsonify({'message': 'User registered successfully'}), 201

# Route to login a user
@auth_bp.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Retrieve user by username
    cursor.execute("SELECT id, password_hash FROM users_phonebook_web WHERE username = ?", (username,))
    user = cursor.fetchone()

    if user is None:
        return jsonify({'error': 'User not found'}), 404

    user_id, password_hash = user

    # Check the password
    if not check_password_hash(password_hash, password):
        return jsonify({'error': 'Invalid password'}), 401

    # Update last login timestamp
    cursor.execute("UPDATE users_phonebook_web SET last_login = ? WHERE id = ?", (datetime.now(), user_id))
    conn.commit()
    conn.close()

    # Generate token
    token = generate_token(user_id)

    return jsonify({'message': 'Login successful', 'token': token}), 200

# New route to verify a token
@auth_bp.route('/api/verify-token', methods=['POST'])
def verify_token_route():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': 'Token is missing'}), 401
    
    # Remove 'Bearer ' prefix if present
    token = token.replace('Bearer ', '', 1)
    
    user_id = verify_token(token)
    if user_id is None:
        return jsonify({'error': 'Invalid or expired token'}), 401
    
    return jsonify({'message': 'Token is valid', 'user_id': user_id}), 200