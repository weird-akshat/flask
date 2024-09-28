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
    conn.row_factory = sqlite3.Row
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
        albumin_levl INTEGER,
        lds DATE,
        lda DATE
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
        id=user[0];
        print(user)
        
        
        conn.close()

        # If user is found, login successful
        if user:
            return jsonify({"message": "Login successful", "username": username,"id": id})
        else:
            return jsonify({"message": "Invalid username or password"}), 401  # Unauthorized
@app.route('/data', methods=['GET'])
def fetch():
    if request.method=='GET':
        id=request.args.get('user_id')
        conn=db_connection()
        cursor=conn.cursor()
        cursor.execute("SELECT * FROM record WHERE patient_id =?",(id,))
        row=cursor.fetchone()
        conn.close()
        if row:
            # Convert the row to a dictionary and return it as JSON
            user_data = {'name':row[1],'id':row[2],'age':row[3],'gender':row[4],'condition':row[5],'doctor':row[6],'date':row[7]}
            return jsonify(user_data), 200
        else:
            return jsonify({'error': 'User not found'}), 404
@app.route('/nutrition', methods=['GET'])
def nutri():
    if request.method=='GET':
        id =request.args.get('user_id')
        conn=db_connection()
        cursor=conn.cursor()
        cursor.execute("SELECT * FROM nutrition WHERE patient_id =?",(id,))
        row=cursor.fetchone()
        conn.close()
        if row:
         
            user_data = {'id':row[1],'week1':row[2],'week2':row[3],'week3':row[4],'week4':row[5],'week5':row[6],'height':row[7],'albumin':row[8],'lds':row[9],'lda':row[10]}
            return jsonify(user_data), 200
        else:
            return jsonify({'error': 'User not found'}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
