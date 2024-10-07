import pyodbc

# Database connection string
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