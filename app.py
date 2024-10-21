from flask import Flask, jsonify, request, render_template_string, redirect
from flask_cors import CORS
import pyodbc
from datetime import datetime
from routes import email_bp, approval_email_bp, percentage_email_bp
from auth import auth_bp
import logging
import os
from flask_caching import Cache
from functools import wraps
from io import StringIO
from urllib.parse import quote

# Initialize Flask app
app = Flask(__name__)

# Enable CORS for the app
CORS(app, resources={r"/*": {"origins": ["http://192.168.45.129:3010",  "http://localhost:3000"]}})

# Configure caching
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a StringIO object to capture logs
log_capture_string = StringIO()
ch = logging.StreamHandler(log_capture_string)
ch.setLevel(logging.INFO)
logger.addHandler(ch)

# Register blueprints
app.register_blueprint(email_bp)
app.register_blueprint(approval_email_bp)
app.register_blueprint(percentage_email_bp)
app.register_blueprint(auth_bp)


# Configure your database connection
db_connection_string = (
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=192.168.45.129;'
    'DATABASE=glpl_phonebook;'
    'UID=sa;'
    'PWD=hiba@2002'
)

# Function to get a database connection
def get_db_connection():
    try:
        conn = pyodbc.connect(db_connection_string)
        logger.info(f"Database connection established successfully at {datetime.now()}.")
        return conn
    except pyodbc.Error as e:
        logger.error(f"Failed to connect to the database at {datetime.now()}: {str(e)}")
        return None

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
        'Designation': row.Designation,  # Add this line
        'Department': row.Department,
        'Reporting_Manager': row.Reporting_Manager,
        'Manager_Email': row.Manager_Email,
        'Current_User_Email': row.Current_User_Email,
    }

# Add a caching decorator
def cached_endpoint(timeout=300):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            cache_key = request.full_path
            cached_response = cache.get(cache_key)
            if cached_response:
                return cached_response
            response = f(*args, **kwargs)
            cache.set(cache_key, response, timeout=timeout)
            return response
        return decorated_function
    return decorator

# Create API endpoints

# GET: Retrieve all users
@app.route('/api/users', methods=['GET'])
@cached_endpoint(timeout=60)  # Cache for 1 minute
def get_users():
    logger.info(f"API hit: GET /api/users at {datetime.now()}")
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)
    search_term = request.args.get('searchTerm', '')
    search_param = request.args.get('searchParam', 'Name')
    status_filter = request.args.get('statusFilter', '')

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor()

    # Build the SQL query based on search parameters
    query = "SELECT * FROM Data_table2 WHERE 1=1"
    params = []

    if search_term:
        if search_param == 'Name':
            query += " AND Current_User_Name LIKE ?"
            params.append(f'%{search_term}%')
        elif search_param == 'Phone Number':
            query += " AND Cell_no LIKE ?"
            params.append(f'%{search_term}%')
        elif search_param == 'Sim No':
            query += " AND SIM_No LIKE ?"
            params.append(f'%{search_term}%')

    if status_filter:
        query += " AND Vi_Status = ?"
        params.append(status_filter)

    # Get total count for pagination
    count_query = f"SELECT COUNT(*) FROM ({query}) AS count_query"
    cursor.execute(count_query, params)
    total_count = cursor.fetchone()[0]

    # Add pagination
    query += " ORDER BY Sr_no OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
    params.extend([(page - 1) * per_page, per_page])

    cursor.execute(query, params)
    rows = cursor.fetchall()
    users = [row_to_dict(row) for row in rows]

    conn.close()

    return jsonify({
        'users': users,
        'totalPages': (total_count + per_page - 1) // per_page,
        'currentPage': page,
        'totalCount': total_count
    })

# POST: Add a new user
@app.route('/api/users', methods=['POST'])
def add_user():
    data = request.json
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor()
    cursor.execute(f"""
        INSERT INTO Data_table2 (Cell_no, Cost, PlanName, SIM_No, Previous_User, Current_User_Name,
                           Location, Mode, Remark, Asset_Mapping, Vi_Status, Last_Edited, 
                           Edited_By_Role, Created_At, Updated_At, Expiration_Date, 
                           Last_Updated_By, Department, Designation, Reporting_Manager, Manager_Email, 
                           Current_User_Email)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data['Cell_no'], data.get('Cost'), data.get('PlanName'), data.get('SIM_No'), 
        data.get('Previous_User'), data.get('Current_User_Name'), data.get('Location'), 
        data.get('Mode'), data.get('Remark'), data.get('Asset_Mapping'), 
        data.get('Vi_Status'), data.get('Last_Edited'), data.get('Edited_By_Role'), 
        datetime.now(), datetime.now(), data.get('Expiration_Date'), 
        data.get('Last_Updated_By'), data.get('Department'), data.get('Designation'), 
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
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
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
    if 'Designation' in data:
        update_fields.append("Designation = ?")
        update_values.append(data['Designation'])

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
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        
        cursor.execute(f"""
            UPDATE Data_table2 SET {update_statement} WHERE Sr_no = ?
        """, update_values)
        
        conn.commit()

        # Fetch the updated user data
        cursor.execute("SELECT * FROM Data_table2 WHERE Sr_no = ?", (id,))
        updated_user = row_to_dict(cursor.fetchone())

        return jsonify(updated_user), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    finally:
        conn.close()

# DELETE: Delete a user by ID
@app.route('/api/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Data_table2 WHERE Sr_no = ?", (id,))
    conn.commit()
    conn.close()
    return '', 204

# Email route for 100% email
@app.route('/api/email/100', methods=['GET'])
def send_100_percent_email():
    recipient = request.args.get('to')
    subject = request.args.get('subject')
    body = request.args.get('body')

    encoded_subject = quote(subject)
    encoded_body = quote(body)

    mailto_link = f"mailto:{recipient}?subject={encoded_subject}&body={encoded_body}"
    return redirect(mailto_link)

# Email route for 90% email
@app.route('/api/email/90', methods=['GET'])
def send_90_percent_email():
    recipient = request.args.get('to')
    subject = request.args.get('subject')
    body = request.args.get('body')

    encoded_subject = quote(subject)
    encoded_body = quote(body)

    mailto_link = f"mailto:{recipient}?subject={encoded_subject}&body={encoded_body}"
    return redirect(mailto_link)

@app.route('/api/email/dataOveremail', methods=['GET'])
def send_dataOveremail_email():
    recipient = request.args.get('to')
    subject = request.args.get('subject')
    body = request.args.get('body')

    encoded_subject = quote(subject)
    encoded_body = quote(body)

    mailto_link = f"mailto:{recipient}?subject={encoded_subject}&body={encoded_body}"
    return redirect(mailto_link)

# Email route for approval email
@app.route('/api/email/approval', methods=['GET'])
def send_approval_email():
    recipient = request.args.get('to')
    subject = request.args.get('subject')
    body = request.args.get('body')

    print(f"Received approval email request: To: {recipient}, Subject: {subject}, Body: {body}")

    # Encode the subject and body
    encoded_subject = quote(subject)
    encoded_body = quote(body)

    mailto_link = f"mailto:{recipient}?subject={encoded_subject}&body={encoded_body}"
    return redirect(mailto_link)

@app.route('/status', methods=['GET'])
def server_status():
    # Check database connection
    db_status = "Connected" if get_db_connection() else "Disconnected"
    
    # Get captured logs
    log_contents = log_capture_string.getvalue()
    
    # HTML template
    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Server Status Dashboard</title>
        <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap" rel="stylesheet">
        <style>
            body {
                font-family: 'Roboto', sans-serif;
                margin: 0;
                padding: 0;
                background-color: #f0f2f5;
                color: #333;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }
            h1 {
                color: #2c3e50;
                text-align: center;
                margin-bottom: 30px;
            }
            .status-card {
                background-color: #fff;
                border-radius: 8px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                padding: 20px;
                margin-bottom: 20px;
            }
            .status-item {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 10px;
            }
            .status-label {
                font-weight: bold;
            }
            .status-value {
                padding: 5px 10px;
                border-radius: 20px;
                color: #fff;
            }
            .status-active {
                background-color: #2ecc71;
            }
            .status-inactive {
                background-color: #e74c3c;
            }
            .logs {
                background-color: #fff;
                border-radius: 8px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                padding: 20px;
            }
            .logs h2 {
                color: #2c3e50;
                margin-top: 0;
            }
            .logs pre {
                background-color: #f7f9fc;
                padding: 15px;
                border-radius: 5px;
                overflow-x: auto;
                font-size: 14px;
                line-height: 1.5;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Server Status Dashboard</h1>
            <div class="status-card">
                <div class="status-item">
                    <span class="status-label">Server Status:</span>
                    <span class="status-value status-active">Active</span>
                </div>
                <div class="status-item">
                    <span class="status-label">Database Status:</span>
                    <span class="status-value {{ 'status-active' if db_status == 'Connected' else 'status-inactive' }}">{{ db_status }}</span>
                </div>
            </div>
            <div class="logs">
                <h2>Recent Logs</h2>
                <pre>{{ logs }}</pre>
            </div>
        </div>
        <script>
            setTimeout(function(){ location.reload(); }, 5000);
        </script>
    </body>
    </html>
    """
    
    return render_template_string(html_template, db_status=db_status, logs=log_contents)

# Main entry point to run the application
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5021)

