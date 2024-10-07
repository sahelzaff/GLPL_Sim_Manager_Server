from flask import jsonify, request
from . import email_bp

@email_bp.route('/api/email', methods=['POST'])
def send_email():
    # Logic to send email
    data = request.json
    # Assuming you have a function to handle sending emails
    # send_email_function(data)
    return jsonify({"message": "Email sent successfully!"}), 201
