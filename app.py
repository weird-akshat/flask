from flask import Flask, request, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS


app = Flask(__name__)

# Enable CORS for specific origins
CORS(app, resources={r"/*": {"origins": "https://myapp-20051.vercel.app"}})  # Adjust origins as needed

# Function to establish a database connection
def db_connection():
    conn = None
    try:
        conn = sqlite3.connect("database.sqlite", check_same_thread=False)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    except sqlite3.Error as e:
        print(e)
    return conn

# Function to create the 'users' table
def create_table():
    conn = db_connection()
    cursor = conn.cursor()
    cursor.execute("""
       CREATE TABLE IF NOT EXISTS  real_chart( patient_id INTEGER, week INTEGER, weight REAL, bmi REAL, albumin_level REAL, hbalc REAL, bp REAL);
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS  expected_chart( patient_id INTEGER, week INTEGER, weight REAL, bmi REAL, albumin_level REAL, hbalc REAL, bp REAL);
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS otp (
            patient_id INTEGER,
            otp INTEGER,
            expires_at DATETIME,
            verified BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (patient_id) REFERENCES erms(patient_id)
        )
    """)
    cursor.execute(""" 
    CREATE TABLE IF NOT EXISTS erms (
    patient_id INTEGER,
    patient_name TEXT NOT NULL,
    date_of_birth DATE NOT NULL,
    gender TEXT CHECK( gender IN ('Male', 'Female', 'Other') ) NOT NULL,
    contact_number TEXT,
    password TEXT,
    email TEXT,
    address TEXT,
    diagnosis TEXT,
    treatment TEXT,
    doctor_id INTEGER,
    date_of_admission DATE,
    date_of_discharge DATE,
    follow_up_date DATE,
    insurance_provider TEXT,
    medical_history TEXT,
    current_medication TEXT,
    surgery_details TEXT,
    test_results TEXT,
    foreign key (doctor_id) REFERENCES doctors(doctor_id)
);

    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS spirometry_exercises (
    patient_id INTEGER NOT NULL,
    day INTEGER NOT NULL,
    exercise_type TEXT CHECK( exercise_type IN ('Single Ball', 'Two Ball', 'Three Balls') ) NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES erms(patient_id)
);

    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cessation_of_habit (
    patient_id INTEGER,
    habit_type TEXT,
    date TEXT,
    PRIMARY KEY (patient_id, habit_type)
);
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS patient_exercise_data (
    patient_id TEXT NOT NULL,             
    day INTEGER NOT NULL,                 
    time_of_day TEXT NOT NULL,             
    mood_rating INTEGER NOT NULL         
);
""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pain_scale (
    patient_id INTEGER NOT NULL,
    day INTEGER NOT NULL,
    time_period TEXT ,
    pain_rating INTEGER,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
);


""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS doctors (
    doctor_id INTEGER PRIMARY KEY,  -- Unique identifier for each doctor
    password TEXT NOT NULL            -- Password for the doctor
);

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
@app.route('/doctor_login',methods=['POST'])
def log():
    if request.method=='POST':
        doctor_id= request.form.get('doctor_id')
        password= request.form.get('password')
        conn=db_connection()
        cursor=conn.cursor()
        cursor.execute("SELECT doctor_id FROM doctors WHERE doctor_id=? AND password=?", (doctor_id, password))
        user = cursor.fetchone()
        patient_id=user[0]
        print(user)
        
        
        conn.close()

        # If user is found, login successful
        if user:
            return jsonify({"message": "Login successful","doctor_id": doctor_id})
        else:
            return jsonify({"message": "Invalid username or password"}), 401  # Unauthorized

@app.route('/login',methods=['POST'])
def login():
    if request.method =='POST':
        # Fetch form data
        contact_number = request.form.get('contact_number')
        password = request.form.get('password')


        # Database connection
        conn = db_connection()
        cursor = conn.cursor()
        

        # Check if user exists with the provided username and password
        cursor.execute("SELECT patient_id FROM erms WHERE contact_number=? AND password=?", (contact_number, password))
        user = cursor.fetchone()
        patient_id=user[0]
        print(user)
        
        
        conn.close()

        # If user is found, login successful
        if user:
            return jsonify({"message": "Login successful", "username": contact_number,"patient_id": patient_id})
        else:
            return jsonify({"message": "Invalid username or password"}), 401  # Unauthorized

# Login route
@app.route('/real_chart',methods=['GET','POST'])
def real_chart():
    if request.method=='GET':
        patient_id= request.args.get('patient_id')
        conn = db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM real_chart WHERE patient_id=?", (patient_id,))
        rows = cursor.fetchall()
        if rows:
            # Assuming the real_chart table has columns like 'id', 'data1', 'data2', etc.
            column_names = [description[0] for description in cursor.description]
            
            result = [dict(zip(column_names, row)) for row in rows]

            return jsonify(result), 200  # Return the result as JSON with a 200 OK status
        else:
            return jsonify([]), 40
    elif request.method == 'POST':
        # Get data from the request form (for POST requests)
        patient_id = request.form.get('patient_id')
        week = request.form.get('week')
        weight = request.form.get('weight')
        bmi = request.form.get('bmi')
        albumin_level = request.form.get('albumin_level')
        hbalc = request.form.get('hbalc')
        bp = request.form.get('bp')

        # Connect to the database
        conn = db_connection()
        cursor = conn.cursor()

        # Check if the record already exists for the same patient and week
        cursor.execute("SELECT * FROM real_chart WHERE patient_id=? AND week=?", (patient_id, week))
        rows = cursor.fetchall()
        if rows:
            # If the record exists, update it
            cursor.execute("""
                UPDATE real_chart 
                SET weight=?, bmi=?, albumin_level=?, hbalc=?, bp=? 
                WHERE patient_id=? AND week=?""",
                (weight, bmi, albumin_level, hbalc, bp, patient_id, week))
            conn.commit()
            return jsonify({"message": "Record updated successfully"}), 200  # Return success response
        else:
            # If the record does not exist, insert a new one
            cursor.execute("""
                INSERT INTO real_chart (patient_id, week, weight, bmi, albumin_level, hbalc, bp) 
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (patient_id, week, weight, bmi, albumin_level, hbalc, bp))
            conn.commit()
            return jsonify({"message": "Record added successfully"}), 201  # Return success response

        conn.close()
@app.route('/expected_chart',methods=['GET','POST'])
def expected_chart():
    if request.method=='GET':
        patient_id= request.args.get('patient_id')
        conn = db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM expected_chart WHERE patient_id=?", (patient_id,))
        rows = cursor.fetchall()
        if rows:
            # Assuming the real_chart table has columns like 'id', 'data1', 'data2', etc.
            column_names = [description[0] for description in cursor.description]
            
            result = [dict(zip(column_names, row)) for row in rows]

            return jsonify(result), 200  # Return the result as JSON with a 200 OK status
        else:
            return jsonify([]), 40
    elif request.method == 'POST':
        # Get data from the request form (for POST requests)
        patient_id = request.form.get('patient_id')
        week = request.form.get('week')
        weight = request.form.get('weight')
        bmi = request.form.get('bmi')
        albumin_level = request.form.get('albumin_level')
        hbalc = request.form.get('hbalc')
        bp = request.form.get('bp')

        # Connect to the database
        conn = db_connection()
        cursor = conn.cursor()

        # Check if the record already exists for the same patient and week
        cursor.execute("SELECT * FROM expected_chart WHERE patient_id=? AND week=?", (patient_id, week))
        rows = cursor.fetchall()
        if rows:
            # If the record exists, update it
            cursor.execute("""
                UPDATE expected_chart 
                SET weight=?, bmi=?, albumin_level=?, hbalc=?, bp=? 
                WHERE patient_id=? AND week=?""",
                (weight, bmi, albumin_level, hbalc, bp, patient_id, week))
            conn.commit()
            return jsonify({"message": "Record updated successfully"}), 200  # Return success response
        else:
            # If the record does not exist, insert a new one
            cursor.execute("""
                INSERT INTO expected_chart (patient_id, week, weight, bmi, albumin_level, hbalc, bp) 
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (patient_id, week, weight, bmi, albumin_level, hbalc, bp))
            conn.commit()
            return jsonify({"message": "Record added successfully"}), 201  # Return success response

        conn.close()

@app.route('/erms',methods=['GET', 'POST'])
def patient_details():
    if request.method=='GET':
        patient_id= request.args.get('patient_id')
        conn=db_connection()
        cursor=conn.cursor()
        cursor.execute("SELECT * FROM erms WHERE patient_id=?",(patient_id,))
        rows = cursor.fetchall()
        if rows:
            # Assuming the real_chart table has columns like 'id', 'data1', 'data2', etc.
            column_names = [description[0] for description in cursor.description]
            
            result = [dict(zip(column_names, row)) for row in rows]

            return jsonify(result), 200  # Return the result as JSON with a 200 OK status
        else:
            return jsonify([]), 40
    elif request.method == 'POST':
        # Get form data from POST request
        patient_id = request.form.get('patient_id')
        patient_name = request.form.get('patient_name')
        date_of_birth = request.form.get('date_of_birth')
        gender = request.form.get('gender')
        contact_number = request.form.get('contact_number')
        email = request.form.get('email')
        address = request.form.get('address')
        diagnosis = request.form.get('diagnosis')
        treatment = request.form.get('treatment')
        doctor_id = request.form.get('doctor_id')
        date_of_admission = request.form.get('date_of_admission')
        date_of_discharge = request.form.get('date_of_discharge')
        follow_up_date = request.form.get('follow_up_date')
        insurance_provider = request.form.get('insurance_provider')
        medical_history = request.form.get('medical_history')
        current_medication = request.form.get('current_medication')
        surgery_details = request.form.get('surgery_details')
        test_results = request.form.get('test_results')

        conn = db_connection()
        cursor = conn.cursor()

        # Check if the record for this patient already exists
        cursor.execute("SELECT * FROM erms WHERE patient_id=?", (patient_id,))
        rows = cursor.fetchall()

        if rows:
            # If the patient record exists, update it
            cursor.execute("""
                UPDATE erms 
                SET patient_name=?, date_of_birth=?, gender=?, contact_number=?, email=?, 
                    address=?, diagnosis=?, treatment=?, doctor_id=?, date_of_admission=?, 
                    date_of_discharge=?, follow_up_date=?, insurance_provider=?, 
                    medical_history=?, current_medication=?, surgery_details=?, test_results=? 
                WHERE patient_id=?""",
                (patient_name, date_of_birth, gender, contact_number, email, address, diagnosis, 
                 treatment, doctor_id, date_of_admission, date_of_discharge, follow_up_date, 
                 insurance_provider, medical_history, current_medication, surgery_details, 
                 test_results, patient_id))
            conn.commit()
            return jsonify({"message": "Record updated successfully"}), 200  # Success response
        else:
            # If the patient record does not exist, insert a new one
            cursor.execute("""
                INSERT INTO erms (patient_id, patient_name, date_of_birth, gender, contact_number, 
                email, address, diagnosis, treatment, doctor_id, date_of_admission, date_of_discharge, 
                follow_up_date, insurance_provider, medical_history, current_medication, surgery_details, 
                test_results) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (patient_id, patient_name, date_of_birth, gender, contact_number, email, address, 
                 diagnosis, treatment, doctor_id, date_of_admission, date_of_discharge, follow_up_date, 
                 insurance_provider, medical_history, current_medication, surgery_details, test_results))
            conn.commit()
            return jsonify({"message": "Record added successfully"}), 201  # Success response

        conn.close()

@app.route('/light_exercises',methods=['GET', 'POST'])
def light_exercises():
    if request.method=='GET':
        patient_id= request.args.get('patient_id')

        conn=db_connection()
        cursor=conn.cursor()
        cursor.execute("SELECT * FROM light_exercises WHERE patient_id=?",(patient_id,))
        rows = cursor.fetchall()
        if rows:
            # Assuming the real_chart table has columns like 'id', 'data1', 'data2', etc.
            column_names = [description[0] for description in cursor.description]
            
            result = [dict(zip(column_names, row)) for row in rows]

            return jsonify(result), 200  # Return the result as JSON with a 200 OK status
        else:
            return jsonify([]), 40
    elif request.method=='POST':
        patient_id=request.form.get('patient_id')
        day= request.form.get('day')
        steps= request.form.get('steps')
        walking_distance_km=request.form.get('walking_distance_km')
        stairs_climbed=request.form.get('stairs_climbed')
        running_km=request.form.get('running_km')
        conn=db_connection()
        cursor=conn.cursor()
        cursor.execute("SELECT * FROM light_exercises WHERE (patient_id=? AND day=?) ",(patient_id,day,))
        rows=cursor.fetchall()
        if rows: 
            cursor.execute("UPDATE light_exercises SET steps=?,walking_distance_km=?,stairs_climbed=?,running_km=? WHERE patient_id=? AND day=?",(steps,walking_distance_km,stairs_climbed,running_km,patient_id,day,))
            print(patient_id, day, steps, walking_distance_km, stairs_climbed, running_km)
            conn.commit()
            return jsonify({"message": "Record updated successfully"}), 200  # Return success response
        else:
            cursor.execute("INSERT INTO light_exercises (patient_id,day,steps,walking_distance_km,stairs_climbed,running_km) VALUES (?,?,?,?,?,?)",(patient_id,day,steps,walking_distance_km,stairs_climbed,running_km,))
            print(patient_id, day, steps, walking_distance_km, stairs_climbed, running_km)
            conn.commit()
            return jsonify({"message": "Record updated successfully"}), 200  # Return success response
@app.route('/spirometry',methods=['POST', 'GET'])
def spiro():
    if request.method=='GET':
        patient_id= request.args.get('patient_id')

        conn=db_connection()
        cursor=conn.cursor()
        cursor.execute("SELECT * FROM spirometry_exercises WHERE patient_id=?",(patient_id,))
        rows = cursor.fetchall()
        if rows:
            # Assuming the real_chart table has columns like 'id', 'data1', 'data2', etc.
            column_names = [description[0] for description in cursor.description]
            
            result = [dict(zip(column_names, row)) for row in rows]

            return jsonify(result), 200  # Return the result as JSON with a 200 OK status
    elif request.method=='POST':
        patient_id=request.form.get('patient_id')
        day= request.form.get('day')
        steps= request.form.get('steps')
        exercise_type=request.form.get('exercise_type')
        allowed_exercises = ['Single Ball', 'Two Ball', 'Three Balls']
        if exercise_type not in allowed_exercises:
            return jsonify({"error": "Invalid exercise type. Allowed values are: 'Single Ball', 'Two Ball', 'Three Balls'"}), 400
        conn=db_connection()
        cursor=conn.cursor()
        cursor.execute("SELECT * FROM spirometry_exercises WHERE (patient_id=? AND day=?) ",(patient_id,day,))
        rows=cursor.fetchall()
        if rows: 
            cursor.execute("UPDATE spirometry_exercises SET exercise_type=? WHERE patient_id=? AND day=?",(exercise_type,patient_id,day,))
            
            conn.commit()
            return jsonify({"message": "Record updated successfully"}), 200  # Return success response
        else:
            cursor.execute("INSERT INTO spirometry_exercises (patient_id,day,exercise_type) VALUES (?,?,?)",(patient_id,day,exercise_type,))
            
            conn.commit()
            return jsonify({"message": "Record updated successfully"}), 200  # Return success response


@app.route('/cessation',methods=['POST','GET'])
def cess():
    if request.method=='GET':
        patient_id= request.args.get('patient_id')
        
        conn=db_connection()
        cursor=conn.cursor()
        cursor.execute("SELECT * FROM cessation_of_habit WHERE patient_id=?",(patient_id,))
        rows = cursor.fetchall()
        if rows:
            # Assuming the real_chart table has columns like 'id', 'data1', 'data2', etc.
            column_names = [description[0] for description in cursor.description]
            
            result = [dict(zip(column_names, row)) for row in rows]
            
            return jsonify(result), 200  # Return the result as JSON with a 200 OK status
    elif request.method=='POST':
        patient_id=request.form.get('patient_id')
        habit_type= request.form.get('habit_type')
        date=request.form.get('date')
        conn=db_connection()
        cursor=conn.cursor()
        
        cursor.execute("SELECT * FROM cessation_of_habit WHERE patient_id=? AND habit_type=?",(patient_id,habit_type))
        rows=cursor.fetchall()
        if rows: 
            cursor.execute("UPDATE cessation_of_habit SET date = ? WHERE patient_id=? AND habit_type=?",(date,patient_id,habit_type,))
            conn.commit()
            return jsonify({"message": "Record updated successfully"}), 200  # Return success response
        else:
            cursor.execute("INSERT INTO cessation_of_habit (date,patient_id,habit_type) VALUES (?,?,?)",(date,patient_id,habit_type,))
            conn.commit()
            return jsonify({"message": "Record updated successfully"}), 200  # Return success response
@app.route('/pain_scale',methods=['GET','POST'])
def pain():
    if request.method=='GET':
        patient_id= request.args.get('patient_id')
        
        conn=db_connection()
        cursor=conn.cursor()
        cursor.execute("SELECT * FROM pain_scale  WHERE patient_id=?",(patient_id,))
        rows = cursor.fetchall()
        if rows:
            # Assuming the real_chart table has columns like 'id', 'data1', 'data2', etc.
            column_names = [description[0] for description in cursor.description]
            
            result = [dict(zip(column_names, row)) for row in rows]
            
            return jsonify(result), 200  # Return the result as JSON with a 200 OK status
    if request.method=='POST':
        patient_id=request.form.get('patient_id')
        day=request.form.get('day')
        time_period= request.form.get('time_period')
        pain_rating= request.form.get('pain_rating')
        conn=db_connection()
        cursor=conn.cursor()
        cursor.execute("SELECT * FROM pain_scale WHERE patient_id=? AND day=? AND time_period=?",(patient_id,day,time_period))
        rows=cursor.fetchall()
        if rows: 
            cursor.execute("UPDATE pain_scale SET pain_rating = ? WHERE patient_id=? AND day=? AND time_period=?",(pain_rating,patient_id,day,time_period))
            print(pain_rating,patient_id,day,time_period)
            conn.commit()
            return jsonify({"message": "Record updated successfully"}), 200  # Return success response
        else:
            cursor.execute("INSERT INTO pain_scale (pain_rating,patient_id,day,time_period) VALUES (?,?,?,?)",(pain_rating,patient_id,day,time_period))
            conn.commit()
            print(pain_rating,patient_id,day,time_period)
            return jsonify({"message": "Record updated successfully"}), 200  # Return success response
@app.route('/doctor',methods=['GET','POST'])
def doctor():
    if request.method=='GET':
        doctor_id=request.args.get('doctor_id')
        conn=db_connection()
        cursor=conn.cursor()
        cursor.execute("SELECT patient_id FROM erms WHERE doctor_id=?",(doctor_id,))
        rows=cursor.fetchall()
        if rows:
            # Assuming the real_chart table has columns like 'id', 'data1', 'data2', etc.
            column_names = [description[0] for description in cursor.description]
            
            result = [dict(zip(column_names, row)) for row in rows]
            
            return jsonify(result), 200  # Return the result as JSON with a 200 OK status



            
            


# @app.route('/', methods=['POST'])
# def login():
#     if request.method == 'POST':
#         # Fetch form data
#         username = request.form.get('username')
#         password = request.form.get('password')


#         # Database connection
#         conn = db_connection()
#         cursor = conn.cursor()

#         # Check if user exists with the provided username and password
#         cursor.execute("SELECT * FROM users WHERE  AND , (,))
#         user = cursor.fetchone()
#         id=user[0]
#         print(user)
        
        
#         conn.close()

#         # If user is found, login successful
#         if user:
#             return jsonify({"message": "Login successful", "username": username,"id": id})
#         else:
#             return jsonify({"message": "Invalid username or password"}), 401  # Unauthorized

# # Fetch user data
# @app.route('/data', methods=['GET','POST'])
# def fetch():
#     user_id = request.args.get('user_id')

#     conn = db_connection()
#     cursor = conn.cursor()

#     cursor.execute("SELECT * FROM record WHERE patient_id=?", (user_id,))
#     row = cursor.fetchone()

#     if row:
#         user_data = {
#             'name': row['name'],
#             'id': row['patient_id'],
#             'age': row['age'],
#             'gender': row['gender'],
#             'current_unit': row['current_unit'],
#             'doctor': row['doctor'],
#             'visit_date': row['visit_date']
#         }
#         return jsonify(user_data), 200
#     else:
#         return jsonify({'error': 'User not found'}), 404

# # Fetch nutrition data
# @app.route('/nutrition', methods=['GET'])
# def nutri():
#     user_id = request.args.get('user_id')

#     conn = db_connection()
#     cursor = conn.cursor()

#     cursor.execute("SELECT * FROM nutrition WHERE patient_id=?", (user_id,))
#     row = cursor.fetchone()

#     if row:
#         nutrition_data = {
#             'id': row['patient_id'],
#             'week1': row['week1_weight'],
#             'week2': row['week2_weight'],
#             'week3': row['week3_weight'],
#             'week4': row['week4_weight'],
#             'week5': row['week5_weight'],
#             'height': row['height'],
#             'albumin': row['albumin_level'],
#             'lds': row['lds'],
#             'lda': row['lda']
#         }
#         return jsonify(nutrition_data), 200
#     else:
#         return jsonify({'error': 'User not found'}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
