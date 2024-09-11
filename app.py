from flask import Flask, request, jsonify, render_template
import sqlite3

app = Flask(__name__)

# Function to establish a database connection
def db_connection():
    conn = None
    try:
        conn = sqlite3.connect("database.sqlite", check_same_thread=False)  # Added check_same_thread=False for multi-threaded Flask app
    except sqlite3.Error as e:
        print(e)
    return conn

# Function to create the 'users' table
def create_table():
    conn = db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            password TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# Create table when the script runs
create_table()

# Login route
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Fetch form data
        username = request.form.get('username')
        password = request.form.get('password')

        # Database connection
        conn = db_connection()
        cursor = conn.cursor()

        # Check if user exists with the provided username and password
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()
        
        conn.close()

        # If user is found, login successful
        if user:
            return jsonify({"message": "Login successful", "username": username})
        else:
            return jsonify({"message": "Invalid username or password"}), 401  # Unauthorized

