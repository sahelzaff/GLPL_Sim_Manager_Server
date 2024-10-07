from flask import Blueprint

# Create a blueprint for email routes
email_bp = Blueprint('email', __name__)

# Create a blueprint for approval email routes
approval_email_bp = Blueprint('approval_email', __name__)

# Create a blueprint for percentage email routes
percentage_email_bp = Blueprint('percentage_email', __name__)

# Import the routes
from . import email, approval_email, percentage_email
