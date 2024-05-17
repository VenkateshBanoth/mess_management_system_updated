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
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Check if user is an admin
        cursor.execute("SELECT id FROM admin WHERE email = %s AND password = %s", (email, password))
        admin_id = cursor.fetchone()
        if admin_id:
            session['admin_id'] = admin_id[0]
            return redirect(url_for('admin_dashboard'))
        
        # Check if user is a student
        cursor.execute("SELECT id FROM students WHERE email = %s AND password = %s", (email, password))
        student_id = cursor.fetchone()
        if student_id:
            session['user_id'] = student_id[0]
            return redirect(url_for('student_dashboard'))
        else:
            return "Invalid credentials. Please try again."
    
    return render_template('index.html')


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
    admin_id = session.get('admin_id')
    if not admin_id:
        return redirect(url_for('index'))
    
    # Get meal counts for each day and meal type
    meal_counts = {}
    for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']:
        meal_counts[day] = {}
        for meal_type in ['breakfast', 'lunch', 'dinner']:
            cursor.execute("SELECT COUNT(*) FROM meal WHERE day = %s AND meal_type = %s AND status = 'booked'", (day, meal_type))
            count = cursor.fetchone()[0]
            meal_counts[day][meal_type] = count
    
    return render_template('admin_dashboard.html', meal_counts=meal_counts)

@app.route('/manage_students', methods=['GET', 'POST'])
def manage_students():
    admin_id = session.get('admin_id')
    if not admin_id:
        return redirect(url_for('index'))

    search_query = request.args.get('search')
    if search_query:
        cursor.execute("SELECT * FROM students WHERE email LIKE %s OR first_name LIKE %s OR last_name LIKE %s", 
                       ('%' + search_query + '%', '%' + search_query + '%', '%' + search_query + '%'))
    else:
        cursor.execute("SELECT * FROM students")
    
    students = cursor.fetchall()
    return render_template('manage_students.html', students=students)



@app.route('/manage_menu', methods=['GET', 'POST'])
def manage_menu():
    if request.method == 'POST':
        menu_data = request.form
        for i in range(len(menu_data) // 3):
            day = menu_data.get(f'menu_data[{i}][day]')
            meal_type = menu_data.get(f'menu_data[{i}][meal_type]')
            dish = menu_data.get(f'menu_data[{i}][dish]')
            cursor.execute("UPDATE menu SET dish = %s WHERE day = %s AND meal_type = %s", (dish, day, meal_type))
        db.commit()

    cursor.execute("SELECT day, meal_type, dish FROM menu")
    menu_data = cursor.fetchall()
    print("Fetched Menu Data:", menu_data)  # Debugging statement to check data retrieval
    return render_template('manage_menu.html', menu=menu_data)

@app.route('/edit_student/<int:student_id>', methods=['GET', 'POST'])
def edit_student(student_id):
    admin_id = session.get('admin_id')
    if not admin_id:
        return redirect(url_for('index'))

    cursor.execute("SELECT * FROM students WHERE id = %s", (student_id,))
    student = cursor.fetchone()

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        phone_number = request.form.get('phone_number')
        cursor.execute(
            "UPDATE students SET email = %s, password = %s, first_name = %s, last_name = %s, phone_number = %s WHERE id = %s",
            (email, password, first_name, last_name, phone_number, student_id)
        )
        db.commit()
        return redirect(url_for('manage_students'))

    return render_template('edit_student.html', student=student)


@app.route('/delete_student/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    admin_id = session.get('admin_id')
    if not admin_id:
        return redirect(url_for('index'))

    cursor.execute("DELETE FROM students WHERE id = %s", (student_id,))
    db.commit()
    return redirect(url_for('manage_students'))

if __name__ == "__main__":
    app.run(debug=True)
