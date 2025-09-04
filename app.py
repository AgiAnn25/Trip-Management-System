from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
from mysql.connector import Error
import random
import string
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a secure secret key

# Function to create a database connection
def get_db_connection():
    try:
        return mysql.connector.connect(
            host='localhost',
            user='root',  
            password='password',  
            database='trip'  
        )
    except Error as e:
        print(f"Error connecting to database: {str(e)}")
        return None

# Home route
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')  
@app.route('/contact')
def contact():
    return render_template('contact.html')

def get_current_user():
    if 'user_id' in session:
        user_id = session['user_id']
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        return user
    return None

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        phone_no = request.form.get('phone_no')
        email = request.form.get('email')
        address = request.form.get('address')

        # Check if all required fields are provided
        if not all([name, phone_no, email, address]):
            flash('All fields are required!', 'error')
            return redirect(url_for('register'))

        # Generate username and random password
        first_name = name.split()[0]
        random_digits = ''.join(random.choices(string.digits, k=4))
        username = first_name + random_digits
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

        try:
            # Connect to the database
            conn = get_db_connection()
            if conn is None:
                flash('Database connection failed.', 'error')
                return redirect(url_for('register'))

            cursor = conn.cursor()
            
            # Check if username already exists
            cursor.execute("SELECT COUNT(*) FROM users WHERE username = %s", (username,))
            exists = cursor.fetchone()[0]
            
            if exists:
                flash('Username already exists. Please choose a different one.', 'error')
                return redirect(url_for('register'))

            # Insert new user into the database
            query = """
                INSERT INTO users (name, address, phone_no, email, username, password)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            values = (name, address, phone_no, email, username, password)

            print(f"Executing Query: {query} with values: {values}")  
            
            cursor.execute(query, values)
            conn.commit()  # Commit the transaction
            
            print(f"Registration successful for user: {username}")  

            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))

        except Error as e:
            print(f"Error occurred while registering: {str(e)}")  # Debugging output
            flash(f"An error occurred while registering: {str(e)}", 'error')
            return redirect(url_for('register'))

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    return render_template('register.html')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Check if both email and password are provided
        if not email or not password:
            flash('Both email and password are required', 'danger')
            return redirect(url_for('login'))

        conn = get_db_connection()  # Use the function to get the database connection
        if conn is None:
            flash('Database connection failed', 'danger')
            return redirect(url_for('login'))

        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()

            if user:
                stored_password = user[3]  # Password is in the 4th column (0-indexed)

                if password == stored_password:
                    session['user_id'] = user[0]  # user_id is the 1st column (0-indexed)
                    flash('Login successful!', 'success')
                    return redirect(url_for('user_dashboard'))
                else:
                    flash('Invalid email or password', 'danger')
            else:
                flash('Invalid email or password', 'danger')

        except Exception as e:
            flash(f"An error occurred: {str(e)}", 'error')
        finally:
            cursor.close()  # Ensure cursor is closed even if an error occurs
            conn.close()  # Close the database connection

    return render_template('login.html')


@app.route('/user_dashboard')
def user_dashboard():
    # Ensure the user is logged in
    if 'user_id' not in session:
        flash('Please log in to access the dashboard', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)  # Fetch as dictionary

        # Fetch user information
        cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()

        # Create a user dictionary if user is found
        if user:
            user_data = {
                'user_id': user['user_id'],
                'name': user['name'],
                'username': user['username'],
                'address': user['address'],
                'phone_no': user['phone_no'],
                'email': user['email']
            }

            # Fetch user's bookings with payment amounts
            cursor.execute(
                "SELECT b.booking_id, b.booking_date, b.no_of_seats, b.total_amount, t.trip_name, p.amount AS payment_amount "
                "FROM bookings b "
                "JOIN trips t ON b.trip_id = t.trip_id "
                "LEFT JOIN payments p ON b.booking_id = p.booking_id "
                "WHERE b.user_id = %s", 
                (user_id,)
            )
            bookings = cursor.fetchall()

            return render_template('user_dashboard.html', user=user_data, bookings=bookings)
        else:
            flash('User not found', 'danger')
            return redirect(url_for('login'))

    except Exception as e:
        flash(f"An error occurred: {str(e)}", 'error')
        return redirect(url_for('login'))

    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()




@app.route('/booking', methods=['GET', 'POST'])
def booking():
    trip_id = request.args.get('trip_id')  # Get trip_id from query parameters

    # Check if user is logged in
    if 'user_id' not in session:
        flash('You need to log in to make a booking.', 'warning')
        return redirect(url_for('login'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch trip details including price
        cursor.execute("SELECT trip_name, price FROM trips WHERE trip_id = %s", (trip_id,))
        trip = cursor.fetchone()
        if not trip:
            flash('Trip not found.', 'error')
            return redirect(url_for('trips'))

        trip_name = trip[0]
        trip_price = trip[1]  # Get the price from the result

    except Error as e:
        flash(f"An error occurred while fetching trip details: {str(e)}", 'error')
        return redirect(url_for('trips'))

    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

    if request.method == 'POST':
        user_id = session['user_id']
        booking_date = request.form['booking_date']
        no_of_seats = request.form['no_of_seats']

        try:
            no_of_seats = int(no_of_seats)
        except ValueError:
            flash('Number of seats must be a valid number.', 'error')
            return render_template('booking.html', trip_name=trip_name, trip_price=trip_price, trip_id=trip_id)

        # Calculate total_amount based on trip_price and no_of_seats
        total_amount = trip_price * no_of_seats

        # Debugging: Print the captured data
        print(f"user_id: {user_id}, booking_date: {booking_date}, no_of_seats: {no_of_seats}, total_amount: {total_amount}, trip_id: {trip_id}")

        # Input validation
        if no_of_seats <= 0:
            flash('Invalid number of seats. Please select at least one seat.', 'error')
            return render_template('booking.html', trip_name=trip_name, trip_price=trip_price, trip_id=trip_id)

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO bookings (user_id, trip_id, booking_date, no_of_seats, total_amount) VALUES (%s, %s, %s, %s, %s)", 
                (user_id, trip_id, booking_date, no_of_seats, total_amount)
            )
            conn.commit()

            # Check if any rows were affected
            if cursor.rowcount > 0:
                flash('Booking created successfully!', 'success')
                
                # Redirect to booking confirmation page with total amount
                return redirect(url_for('user_dashboard', booking_amount=total_amount))  # Redirect to user dashboard or booking confirmation

            else:
                flash('Failed to create booking. Please try again.', 'error')

        except Error as e:
            flash(f"An error occurred while creating the booking: {str(e)}", 'error')
            print(f"SQL Error: {str(e)}")  # Debugging: Print SQL error

        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    return render_template('booking.html', trip_name=trip_name, trip_price=trip_price, trip_id=trip_id)


@app.route('/trips')
def trips():
    trips = []  # Initialize an empty list for trips
    try:
        # Use a context manager for the database connection
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT trip_id, trip_name, description, price, start_date, end_date, image FROM trips")
                trips = cursor.fetchall()  # Fetch all trips
    except Error as e:
        flash(f"An error occurred while fetching trips: {str(e)}", 'error')
        return redirect(url_for('home'))

    # Check if trips is empty and flash a message if no trips are available
    if not trips:
        flash("No trips available at the moment.", 'info')

    # Prepare the trips data for rendering
    trips_data = [
        {
            'trip_id': trip[0],
            'trip_name': trip[1],
            'description': trip[2],
            'price': trip[3],
            'start_date': trip[4],
            'end_date': trip[5],
            'image': trip[6] or 'default_image.jpg'  # Use a default image if None
        }
        for trip in trips
    ]

    return render_template('trips.html', trips=trips_data)
@app.route('/destinations')
def destinations():
    destinations = []  # Initialize an empty list for destinations
    try:
        # Use a context manager for the database connection
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Update the query to select the image field as well
                cursor.execute("SELECT location, description, country, image FROM destinations")
                destinations = cursor.fetchall()  # Fetch all destinations

    except Error as e:
        flash(f"An error occurred while fetching destinations: {str(e)}", 'error')
        return redirect(url_for('home'))

    # Prepare the destinations data for rendering
    destinations_data = [
        {
            'location': destination[0],
            'description': destination[1],
            'country': destination[2],
            'image': destination[3] if destination[3] else 'default_destination.jpg'  # Use a default image if None
        }
        for destination in destinations
    ]

    # Render the destinations template with the fetched data
    return render_template('destinations.html', destinations=destinations_data)


from flask import Flask, render_template, request, redirect, url_for, flash, session
from mysql.connector import Error

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        # Extract form data
        trip_id = request.form.get('trip_id')  # Use get() to avoid KeyError
        comments = request.form.get('feedback')  # Match with form field name 'feedback'
        rating = request.form.get('rating')
        user_id = session.get('user_id')

        # Ensure user is logged in
        if not user_id:
            flash('You need to be logged in to submit feedback.', 'error')
            return redirect(url_for('login'))

        # Validate the form data
        if not trip_id or not comments or not rating:
            flash('All fields are required.', 'error')
            return redirect(url_for('feedback'))

        try:
            # Save feedback to the database
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO feedback (user_id, trip_id, comments, rating) VALUES (%s, %s, %s, %s)",
                (user_id, trip_id, comments, rating)
            )
            conn.commit()

            # Success message and redirection
            flash('Feedback submitted successfully!', 'success')
            return redirect(url_for('home'))

        except Exception as e:
            flash(f"An error occurred while submitting feedback: {str(e)}", 'error')

        finally:
            # Close cursor and connection
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    # Fetch trips for the user to populate the dropdown in feedback form
    user_id = session.get('user_id')
    trips = []

    if user_id:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT trip_id, trip_name FROM trips WHERE user_id = %s", (user_id,))
            trips = cursor.fetchall()
        except Exception as e:
            flash(f"An error occurred while fetching trips: {str(e)}", 'error')
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    # Render feedback page with trips list
    return render_template('feedback.html', trips=trips)






@app.route('/process_payment', methods=['POST'])
def process_payment():
    if 'user_id' not in session:
        flash('Please log in to make a payment', 'danger')
        return redirect(url_for('login'))

    booking_id = request.form['booking_id']
    payment_amount = request.form['payment_amount']
    user_id = session['user_id']

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert the payment record into the payments table (dummy simulation)
        cursor.execute(
            "INSERT INTO payments (booking_id, amount) VALUES (%s, %s)",
            (booking_id, payment_amount)
        )
        
        # Update the booking status to 'Completed' (dummy simulation)
        cursor.execute(
            "UPDATE bookings SET status = %s WHERE booking_id = %s AND user_id = %s",
            ('Completed', booking_id, user_id)
        )

        conn.commit()

        # Flash a success message for dummy payment
        flash('Dummy payment processed successfully!', 'success')

        return redirect(url_for('user_dashboard'))

    except Exception as e:
        if conn:
            conn.rollback()  # Rollback if there's an error
        flash(f"An error occurred while processing the payment: {str(e)}", 'error')
        return redirect(url_for('user_dashboard'))

    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
from mysql.connector import Error

@app.route('/payment', methods=['GET', 'POST'])
def payment():
    if 'user_id' not in session:
        flash('Please log in to access the payment page.', 'warning')
        return redirect(url_for('login'))

    booking_amount = None  # Initialize booking_amount
    payments = []  # Initialize payments list

    if request.method == 'POST':
        # Handle the payment submission
        booking_id = request.form['booking_id']
        amount = request.form['amount']
        payment_date = datetime.now().date()  # Get the current date
        payment_status = 'Success'  # Set payment status to Success

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            # Insert payment into the payments table
            cursor.execute(
                "INSERT INTO payments (booking_id, payment_date, amount, payment_status) VALUES (%s, %s, %s, %s)",
                (booking_id, payment_date, amount, payment_status)
            )
            conn.commit()
            flash('Payment submitted successfully!', 'success')
            booking_amount = amount  # Store the booking amount after successful payment
        except Error as e:
            flash(f"An error occurred while processing the payment: {str(e)}", 'error')
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

        # Redirect to the feedback page after successful payment
        return redirect(url_for('feedback'))  # Change this to your actual feedback route

    # Fetch the user's bookings from the database
    user_id = session['user_id']
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT booking_id, trip_name, booking_date, no_of_seats, total_amount FROM bookings WHERE user_id = %s", (user_id,))
        bookings = cursor.fetchall()
        for booking in bookings:
            payments.append({
                'booking_id': booking[0],
                'trip_name': booking[1],
                'booking_date': booking[2],
                'no_of_seats': booking[3],
                'total_amount': booking[4],
                'payment_status': 'Pending'  # Initial status can be set to 'Pending'
            })
    except Error as e:
        flash(f"An error occurred while fetching bookings: {str(e)}", 'error')
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

    return render_template('payment.html', payments=payments, booking_amount=booking_amount)


@app.route('/make_payment', methods=['POST'])
def make_payment():
    # Check if user is logged in
    if 'user_id' not in session:
        flash('Please log in to access the payment page.', 'warning')
        return redirect(url_for('login'))

    # Get the form data
    booking_id = request.form.get('booking_id')
    amount = request.form.get('amount')
    payment_date = datetime.now().date()  # Get the current date
    payment_status = 'Pending'  # Set initial payment status

    # Ensure amount is present and valid
    if not amount or float(amount) <= 0:
        flash('Invalid amount. Please check your booking details.', 'error')
        return redirect(url_for('payment'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Insert payment into the payments table
        cursor.execute(
            "INSERT INTO payments (booking_id, payment_date, amount, payment_status) VALUES (%s, %s, %s, %s)",
            (booking_id, payment_date, amount, payment_status)
        )
        conn.commit()
        flash('Payment submitted successfully!', 'success')
    except Error as e:
        flash(f"An error occurred while processing the payment: {str(e)}", 'error')
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

    return redirect(url_for('payment'))  # Redirect back to the payment page




# Logout route
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))

# Main block
if __name__ == '__main__':
    app.run(debug=True)
