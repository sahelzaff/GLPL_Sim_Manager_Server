import pyodbc
import os

# Database connection string using environment variables
db_connection_string = (
    'DRIVER={ODBC Driver 17 for SQL Server};'
    f'SERVER={os.getenv("DB_SERVER", "192.168.45.129")};'
    f'DATABASE={os.getenv("DB_NAME", "glpl_phonebook")};'
    f'UID={os.getenv("DB_USER", "sa")};'
    f'PWD={os.getenv("DB_PASSWORD", "hiba@2002")}'
)

# Function to get a database connection
def get_db_connection():
    try:
        conn = pyodbc.connect(db_connection_string)
        print("Database connection successful")
        return conn
    except pyodbc.Error as e:
        print(f"Database connection error: {str(e)}")  # Log connection error
        return None
