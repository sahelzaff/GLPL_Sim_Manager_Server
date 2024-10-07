from flask import jsonify, request
from . import approval_email_bp

@approval_email_bp.route('/api/approval_email', methods=['POST'])
def send_approval_email():
    # Logic to send approval email
    data = request.json
    # Assuming you have a function to handle sending approval emails
    # send_approval_email_function(data)
    return jsonify({"message": "Approval email sent successfully!"}), 201
