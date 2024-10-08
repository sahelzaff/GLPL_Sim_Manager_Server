from flask import Flask, jsonify, request
from flask_cors import CORS
import pyodbc
from datetime import datetime
import win32com.client  # Import the win32com.client module for Outlook automation
from routes import email_bp, approval_email_bp, percentage_email_bp
import pythoncom
from auth import auth_bp
import logging
import os

# Initialize Flask app
app = Flask(__name__)

# Enable CORS for the app
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Register blueprints
app.register_blueprint(email_bp)
app.register_blueprint(approval_email_bp)
app.register_blueprint(percentage_email_bp)
app.register_blueprint(auth_bp)


# Configure your database connection
db_connection_string = (
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=GLPL-MUM-L74;'
    'DATABASE=glpl_phonebook;'
    'UID=sqlserversahel;'
    'PWD=Sahel@2003'
)

# Function to get a database connection
def get_db_connection():
    conn = pyodbc.connect(db_connection_string)
    return conn

# Helper function to convert row to dict
def row_to_dict(row):
    return {
        'Sr_no': row.Sr_no,
        'Cell_no': row.Cell_no,
        'Cost': row.Cost,
        'PlanName': row.PlanName,
        'SIM_No': row.SIM_No,
        'Previous_User': row.Previous_User,
        'Current_User_Name': row.Current_User_Name,
        'Location': row.Location,
        'Mode': row.Mode,
        'Remark': row.Remark,
        'Asset_Mapping': row.Asset_Mapping,
        'Vi_Status': row.Vi_Status,
        'Last_Edited': row.Last_Edited,
        'Edited_By_Role': row.Edited_By_Role,
        'Created_At': row.Created_At,
        'Updated_At': row.Updated_At,
        'Expiration_Date': row.Expiration_Date,
        'Last_Updated_By': row.Last_Updated_By,
        'Department': row.Department,
        'Reporting_Manager': row.Reporting_Manager,
        'Manager_Email': row.Manager_Email,
        'Current_User_Email': row.Current_User_Email,
    }

# Create API endpoints

# GET: Retrieve all users
@app.route('/api/users', methods=['GET'])
def get_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Data_table2")
    rows = cursor.fetchall()
    users = [row_to_dict(row) for row in rows]
    conn.close()
    return jsonify(users)

# POST: Add a new user
@app.route('/api/users', methods=['POST'])
def add_user():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"""
        INSERT INTO Data_table2 (Cell_no, Cost, PlanName, SIM_No, Previous_User, Current_User_Name,
                           Location, Mode, Remark, Asset_Mapping, Vi_Status, Last_Edited, 
                           Edited_By_Role, Created_At, Updated_At, Expiration_Date, 
                           Last_Updated_By, Department, Reporting_Manager, Manager_Email, 
                           Current_User_Email)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data['Cell_no'], data.get('Cost'), data.get('PlanName'), data.get('SIM_No'), 
        data.get('Previous_User'), data.get('Current_User_Name'), data.get('Location'), 
        data.get('Mode'), data.get('Remark'), data.get('Asset_Mapping'), 
        data.get('Vi_Status'), data.get('Last_Edited'), data.get('Edited_By_Role'), 
        datetime.now(), datetime.now(), data.get('Expiration_Date'), 
        data.get('Last_Updated_By'), data.get('Department'), 
        data.get('Reporting_Manager'), data.get('Manager_Email'), 
        data.get('Current_User_Email')
    ))
    conn.commit()
    new_user_id = cursor.execute("SELECT @@IDENTITY AS id").fetchone()[0]
    conn.close()
    
    return jsonify({'Sr_no': new_user_id, **data}), 201


# GET: Retrieve a specific user by ID
@app.route('/api/users/<int:id>', methods=['GET'])
def get_user(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Data_table2 WHERE Sr_no = ?", (id,))
    row = cursor.fetchone()
    if row is None:
        return jsonify({'error': 'User not found'}), 404
    user = row_to_dict(row)
    conn.close()
    return jsonify(user)

# PUT: Update an existing user by ID
@app.route('/api/users/<int:id>', methods=['PUT'])
def update_user(id):
    data = request.json
    update_fields = []
    update_values = []
    
    # Check for fields to update and create the SQL query dynamically
    if 'Cell_no' in data:
        update_fields.append("Cell_no = ?")
        update_values.append(data['Cell_no'])
    if 'Current_User_Name' in data:
        update_fields.append("Current_User_Name = ?")
        update_values.append(data['Current_User_Name'])
    if 'Current_User_Email' in data:
        update_fields.append("Current_User_Email = ?")
        update_values.append(data['Current_User_Email'])
    if 'Previous_User' in data:
        update_fields.append("Previous_User = ?")
        update_values.append(data['Previous_User'])
    if 'Location' in data:
        update_fields.append("Location = ?")
        update_values.append(data['Location'])
    if 'Mode' in data:
        update_fields.append("Mode = ?")
        update_values.append(data['Mode'])
    if 'Remark' in data:
        update_fields.append("Remark = ?")
        update_values.append(data['Remark'])
    if 'Vi_Status' in data:
        update_fields.append("Vi_Status = ?")
        update_values.append(data['Vi_Status'])
    if 'Asset_Mapping' in data:
        update_fields.append("Asset_Mapping = ?")
        update_values.append(data['Asset_Mapping'])
    if 'Department' in data:
        update_fields.append("Department = ?")
        update_values.append(data['Department'])
    if 'Reporting_Manager' in data:
        update_fields.append("Reporting_Manager = ?")
        update_values.append(data['Reporting_Manager'])
    if 'Manager_Email' in data:
        update_fields.append("Manager_Email = ?")
        update_values.append(data['Manager_Email'])
    if 'SIM_No' in data:
        update_fields.append("SIM_No = ?")
        update_values.append(data['SIM_No'])
    if 'Cost' in data:
        update_fields.append("Cost = ?")
        update_values.append(data['Cost'])

    # Add timestamps to update
    update_fields.append("Last_Edited = ?")
    update_values.append(datetime.now())
    
    # Append the ID for the WHERE clause
    update_values.append(id)

    if not update_fields:
        return jsonify({'error': 'No fields to update'}), 400
    
    # Join fields to create the update statement
    update_statement = ", ".join(update_fields)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(f"""
            UPDATE Data_table2 SET {update_statement} WHERE Sr_no = ?
        """, update_values)
        
        conn.commit()

        # Return the updated information (only the fields that were updated)
        updated_user_info = {field.split(' = ')[0]: value for field, value in zip(update_fields, update_values[:-1])}
        updated_user_info['Sr_no'] = id  # Include the Sr_no in the response
        return jsonify(updated_user_info), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    finally:
        conn.close()

# DELETE: Delete a user by ID
@app.route('/api/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Data_table2 WHERE Sr_no = ?", (id,))
    conn.commit()
    conn.close()
    return '', 204

# Email route for 100% email
@app.route('/api/email/100', methods=['GET'])
def send_100_percent_email():
    # Initialize COM
    pythoncom.CoInitialize()

    try:
        # Extract the query parameters
        recipient = request.args.get('to')  # Get the recipient email
        subject = request.args.get('subject')  # Get the email subject
        body = request.args.get('body')  # Get the email body

        # Create Outlook mail object
        outlook = win32com.client.Dispatch('outlook.application')
        mail = outlook.CreateItem(0)

        # Set the email details
        mail.Subject = subject if subject else "100% Data Usage Alert"
        mail.Body = body if body else "Your data usage has reached 100%."
        mail.To = recipient if recipient else "recipient@example.com"  

        mail.Display()  # Display the mail window
        outlook.ActiveWindow.WindowState = 2  # 2 means maximize
        outlook.ActiveWindow.Activate()  # Bring the window to the front
        return "90% Email Composed", 200 
    except Exception as e:
        return str(e), 500
    finally:
        # Uninitialize COM
        pythoncom.CoUninitialize()


# Email route for 90% email
@app.route('/api/email/90', methods=['GET'])
def send_90_percent_email():
    # Initialize COM
    pythoncom.CoInitialize()

    try:
        # Extract the query parameters
        recipient = request.args.get('to')  # Get the recipient email
        subject = request.args.get('subject')  # Get the email subject
        body = request.args.get('body')  # Get the email body

        # Create Outlook mail object
        outlook = win32com.client.Dispatch('outlook.application')
        mail = outlook.CreateItem(0)

        # Set the email details
        mail.Subject = subject if subject else "90% Data Usage Alert"
        mail.Body = body if body else "Your data usage has reached 90%."
        mail.To = recipient if recipient else "recipient@example.com"  

        mail.Display()  # Display the mail window
        outlook.ActiveWindow.WindowState = 2  # 2 means maximize
        outlook.ActiveWindow.Activate()  # Bring the window to the front
        return "90% Email Composed", 200 
    except Exception as e:
        return str(e), 500
    finally:
        # Uninitialize COM
        pythoncom.CoUninitialize()

@app.route('/api/email/dataOveremail', methods=['GET'])
def send_dataOveremail_email():
    # Initialize COM
    pythoncom.CoInitialize()

    try:
        # Extract the query parameters
        recipient = request.args.get('to')  # Get the recipient email
        subject = request.args.get('subject')  # Get the email subject
        body = request.args.get('body')  # Get the email body

        # Create Outlook mail object
        outlook = win32com.client.Dispatch('outlook.application')
        mail = outlook.CreateItem(0)

        # Set the email details
        mail.Subject = subject if subject else "90% Data Usage Alert"
        mail.Body = body if body else "Your data usage has reached 90%."
        mail.To = recipient if recipient else "recipient@example.com"  

        mail.Display()  # Display the mail window
        outlook.ActiveWindow.WindowState = 2  # 2 means maximize
        outlook.ActiveWindow.Activate()  # Bring the window to the front
        return "90% Email Composed", 200 
    except Exception as e:
        return str(e), 500
    finally:
        # Uninitialize COM
        pythoncom.CoUninitialize()


# Main entry point to run the application
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

