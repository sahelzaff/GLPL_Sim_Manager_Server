import pyodbc
import os

# Database connection string using environment variables
db_connection_string = (
    'DRIVER={ODBC Driver 17 for SQL Server};'
    f'SERVER={os.getenv("DB_SERVER", "192.168.45.1,1433")};'
    f'DATABASE={os.getenv("DB_NAME", "glpl_phonebook")};'
    f'UID={os.getenv("DB_USER", "sqlserversahel")};'
    f'PWD={os.getenv("DB_PASSWORD", "Sahel@2003")}'
)

# Function to get a database connection
def get_db_connection():
    conn = pyodbc.connect(db_connection_string)
    return conn