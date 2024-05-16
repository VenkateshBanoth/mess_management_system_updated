from flask import Flask, render_template, request, redirect, url_for
import mysql.connector

app = Flask(__name__)

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
    # Check if the sign-in form is submitted
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        # Check if user exists in the database
        cursor.execute("SELECT * FROM students WHERE email = %s AND password = %s", (email, password))
        user = cursor.fetchone()
        if user:
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
    # Get weekly menu from the database
    cursor.execute("SELECT day, meal_type, dish FROM menu ORDER BY day")
    menu = cursor.fetchall()  # Fetch all rows from the menu table
    
    # Get meal status for each day and meal type
    meal_status = {}
    for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
        meal_status[day] = {}
        for meal_type in ['breakfast', 'lunch', 'dinner']:
            cursor.execute("SELECT status FROM meal WHERE student_id = %s AND day = %s AND meal_type = %s",
                           (1, day, meal_type))  # Assuming student ID is 1 (replace with actual student ID)
            status = cursor.fetchone()
            meal_status[day][meal_type] = status[0] if status else None

    # Fetch booked meals for the current student
    cursor.execute("SELECT day, meal_type FROM meal WHERE student_id = %s AND status = 'booked'", (1,))
    booked_meals = cursor.fetchall()

    return render_template('student_dashboard.html', menu=menu, meal_status=meal_status, booked_meals=booked_meals)



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

# Routes
@app.route('/book_cancel_meal/<day>/<meal_type>', methods=['POST'])
def book_cancel_meal(day, meal_type):
    # Check if the meal is already booked
    cursor.execute("SELECT status FROM meal WHERE student_id = %s AND day = %s AND meal_type = %s",
                   (1, day, meal_type))  # Assuming student ID is 1 (replace with actual student ID)
    status = cursor.fetchone()
    if status and status[0] == 'booked':
        # Meal is booked, cancel it
        cursor.execute("DELETE FROM meal WHERE student_id = %s AND day = %s AND meal_type = %s",
                       (1, day, meal_type))  # Assuming student ID is 1 (replace with actual student ID)
        db.commit()
    else:
        # Meal is not booked, book it
        try:
            cursor.execute("INSERT INTO meal (student_id, day, meal_type, status) VALUES (%s, %s, %s, %s)",
                           (1, day, meal_type, 'booked'))  # Assuming student ID is 1 (replace with actual student ID)
            db.commit()
        except mysql.connector.errors.IntegrityError:
            # Duplicate entry error
            cursor.execute("DELETE FROM meal WHERE student_id = %s AND day = %s AND meal_type = %s",
                           (1, day, meal_type))  # Assuming student ID is 1 (replace with actual student ID)
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
