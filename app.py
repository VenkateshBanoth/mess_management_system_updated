from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector

app = Flask(__name__)

# Set the secret key
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

# Connect to MySQL
db = mysql.connector.connect(
    host="localhost",
    user="root",  # Use your MySQL username here
    password="Banoth06@",  # Use your MySQL password here
    database="mess_management_system"
)
cursor = db.cursor()


# Routes
@app.route('/', methods=['GET', 'POST'])
def index():
    print("Session data in index route:", session)  # Add this line at the beginning of index route
    # Check if the sign-in form is submitted
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        # Check if user exists in the database
        cursor.execute("SELECT id FROM students WHERE email = %s AND password = %s", (email, password))
        user_id = cursor.fetchone()
        if user_id:
            session['user_id'] = user_id[0]  # Store user's ID in session
            print("User ID stored in session:", session['user_id'])
            return redirect(url_for('student_dashboard')) # Redirect to student dashboard if user exists
        else:
            return "Invalid credentials. Please try again."
    return render_template('index.html') # Render the sign-in page

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Handle sign-up form submission
        email = request.form['email']
        password = request.form['password']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        phone_number = request.form['phone_number']
        # Insert new user into the database
        cursor.execute("INSERT INTO students (first_name, last_name, email, password, phone_number) VALUES (%s, %s, %s, %s, %s)",
                       (first_name, last_name, email, password, phone_number))
        db.commit() # Commit the transaction
        return redirect(url_for('index')) # Redirect to index (sign-in page) after sign-up
    return render_template('signup.html') # Render the sign-up page

# Routes
@app.route('/student_dashboard')
def student_dashboard():
    # Get user ID from session
    user_id = session.get('user_id')
    
    if user_id:
        # Get weekly menu from the database
        cursor.execute("SELECT day, meal_type, dish FROM menu ORDER BY day")
        menu = cursor.fetchall()
        
        # Get meal status for the current student
        meal_status = {}
        for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
            meal_status[day] = {}
            for meal_type in ['breakfast', 'lunch', 'dinner']:
                cursor.execute("SELECT status FROM meal WHERE student_id = %s AND day = %s AND meal_type = %s",
                               (user_id, day, meal_type))
                status = cursor.fetchone()
                meal_status[day][meal_type] = status[0] if status else None
        
        # Fetch booked meals for the current student
        cursor.execute("SELECT day, meal_type FROM meal WHERE student_id = %s AND status = 'booked'", (user_id,))
        booked_meals = cursor.fetchall()
        
        return render_template('student_dashboard.html', menu=menu, meal_status=meal_status, booked_meals=booked_meals, user_id=user_id)
    else:
        return redirect(url_for('index'))


@app.route('/book_meal/<day>/<meal_type>', methods=['POST'])
def book_meal(day, meal_type):
    # Book a meal for the student on the specified day and meal type
    # Update the meal status in the database
    cursor.execute("INSERT INTO meal (student_id, day, meal_type, status) VALUES (%s, %s, %s, %s)",
                   (1, day, meal_type, 'booked'))  # Assuming student ID is 1 (replace with actual student ID)
    db.commit()
    return redirect(url_for('student_dashboard'))

@app.route('/cancel_meal/<day>/<meal_type>', methods=['POST'])
def cancel_meal(day, meal_type):
    # Cancel a meal for the student on the specified day and meal type
    # Update the meal status in the database
    cursor.execute("INSERT INTO meal (student_id, day, meal_type, status) VALUES (%s, %s, %s, %s)",
                   (1, day, meal_type, 'cancelled'))  # Assuming student ID is 1 (replace with actual student ID)
    db.commit()
    return redirect(url_for('student_dashboard'))

@app.route('/book_cancel_meal/<day>/<meal_type>', methods=['POST'])
def book_cancel_meal(day, meal_type):
    # Check if the meal is already booked
    user_id = session.get('user_id')
    if user_id:
        cursor.execute("SELECT status FROM meal WHERE student_id = %s AND day = %s AND meal_type = %s",
                       (user_id, day, meal_type))
        status = cursor.fetchone()
        if status and status[0] == 'booked':
            # Meal is booked, cancel it
            cursor.execute("DELETE FROM meal WHERE student_id = %s AND day = %s AND meal_type = %s",
                           (user_id, day, meal_type))
            db.commit()
        else:
            # Meal is not booked, book it
            try:
                cursor.execute("INSERT INTO meal (student_id, day, meal_type, status) VALUES (%s, %s, %s, %s)",
                               (user_id, day, meal_type, 'booked'))
                db.commit()
            except mysql.connector.errors.IntegrityError:
                # Duplicate entry error
                cursor.execute("DELETE FROM meal WHERE student_id = %s AND day = %s AND meal_type = %s",
                               (user_id, day, meal_type))
                db.commit()
    return redirect(url_for('student_dashboard'))


@app.route('/admin_dashboard')
def admin_dashboard():
    # Fetch meal counts from the database
    cursor.execute("SELECT day, SUM(CASE WHEN meal_type='breakfast' THEN 1 ELSE 0 END) AS breakfast_count, "
                   "SUM(CASE WHEN meal_type='lunch' THEN 1 ELSE 0 END) AS lunch_count, "
                   "SUM(CASE WHEN meal_type='dinner' THEN 1 ELSE 0 END) AS dinner_count "
                   "FROM meal GROUP BY day")
    meal_counts = cursor.fetchall()

    return render_template('admin_dashboard.html', meal_counts=meal_counts)

if __name__ == "__main__":
    app.run(debug=True)
