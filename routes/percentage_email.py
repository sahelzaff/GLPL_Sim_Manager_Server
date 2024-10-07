from flask import jsonify, request
from . import percentage_email_bp

@percentage_email_bp.route('/api/90_percent_email', methods=['POST'])
def send_90_percent_email():
    # Logic for 90% email
    data = request.json
    # Assuming you have a function to handle this specific email
    # send_90_percent_email_function(data)
    return jsonify({"message": "90% email sent successfully!"}), 201

@percentage_email_bp.route('/api/100_percent_email', methods=['POST'])
def send_100_percent_email():
    # Logic for 100% email
    data = request.json
    # Assuming you have a function to handle this specific email
    # send_100_percent_email_function(data)
    return jsonify({"message": "100% email sent successfully!"}), 201
