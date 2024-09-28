from flask import Flask, request, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS

app = Flask(_name_)

# Enable CORS for specific origins
CORS(app, resources={r"/*": {"origins": "https://myapp-20051.vercel.app"}})  # Adjust origins as needed

# Function to establish a database connection
def db_connection():
    conn = None
    try:
        conn = sqlite3.connect("database.sqlite", check_same_thread=False)
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
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS record (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            patient_id INTEGER,
            age INTEGER,
            gender TEXT NOT NULL,
            current_unit TEXT NOT NULL,
            doctor TEXT NOT NULL,
            visit_date DATE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS nutrition(
            id INTEGER PRIMARY KEY,
            patient_id INTEGER,
            week1_weight INTEGER,
            week2_weight INTEGER,
            week3_weight INTEGER,
            week4_weight INTEGER,
            week5_weight INTEGER,
            height INTEGER,
            albumin_level INTEGER,
            lds DATE,
            lda DATE
        )
    """)
    conn.commit()
    conn.close()

# Create table when the script runs
create_table()

# Add access control headers to the response
@app.after_request
def add_access_control_headers(response):
    response.headers['Access-Control-Allow-Origin'] = 'https://myapp-20051.vercel.app'  # Allow specific origin
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'  # Allowed methods
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'  # Allowed headers
    return response

# Login route
@app.route('/', methods=['POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cursor.fetchone()

        if user and check_password_hash(user['password'], password):
            return jsonify({"message": "Login successful", "username": username, "id": user['id']}), 200
        else:
            return jsonify({"message": "Invalid username or password"}), 401

# Fetch user data
@app.route('/data', methods=['GET'])
def fetch():
    user_id = request.args.get('user_id')

    conn = db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM record WHERE patient_id=?", (user_id,))
    row = cursor.fetchone()

    if row:
        user_data = {
            'name': row['name'],
            'id': row['patient_id'],
            'age': row['age'],
            'gender': row['gender'],
            'current_unit': row['current_unit'],
            'doctor': row['doctor'],
            'visit_date': row['visit_date']
        }
        return jsonify(user_data), 200
    else:
        return jsonify({'error': 'User not found'}), 404

# Fetch nutrition data
@app.route('/nutrition', methods=['GET'])
def nutri():
    user_id = request.args.get('user_id')

    conn = db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM nutrition WHERE patient_id=?", (user_id,))
    row = cursor.fetchone()

    if row:
        nutrition_data = {
            'id': row['patient_id'],
            'week1': row['week1_weight'],
            'week2': row['week2_weight'],
            'week3': row['week3_weight'],
            'week4': row['week4_weight'],
            'week5': row['week5_weight'],
            'height': row['height'],
            'albumin': row['albumin_level'],
            'lds': row['lds'],
            'lda': row['lda']
        }
        return jsonify(nutrition_data), 200
    else:
        return jsonify({'error': 'User not found'}), 404

if _name_ == "_main_":
    app.run(host="0.0.0.0", port=3000)
