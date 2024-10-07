from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from db_connection import get_db_connection
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

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

    return jsonify({'message': 'Login successful'}), 200