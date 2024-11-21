from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set your secret key for session management

# MySQL Database Connection
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host='localhost',  # Your MySQL host (use 'localhost' if running locally)
            user='root',  # Your MySQL username
            password='Sanjay@2005',  # Your MySQL password
            database='Railway_management_system'  # Your MySQL database name
        )
        if conn.is_connected():
            print("Successfully connected to MySQL.")
        return conn
    except mysql.connector.Error as e:
        print(f"Error: {e}")
        return None


# Route for the login page
@app.route('/')
def login():
    return render_template('login.html')


# Route to handle login authentication
@app.route('/login', methods=['POST'])
def login_user():
    username = request.form['username']
    password = request.form['password']
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM Users WHERE username = %s', (username,))
        user = cursor.fetchone()
        
        if user:
            session['user_id'] = user['user_id']  # Store user_id in the session
            conn.close()
            return redirect(url_for('train_details'))
        else:
            conn.close()
            return "Invalid credentials, please try again."
    return "Database connection error."


# Route for displaying train details
@app.route('/train_details')
def train_details():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM TrainDetails')
        trains = cursor.fetchall()
        conn.close()
        return render_template('train_details.html', trains=trains)
    return "Database connection error."

#Route for booking
@app.route('/book_train/<int:train_id>', methods=['GET', 'POST'])
def book_train(train_id):
    # Check if the user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Establish a database connection
    conn = get_db_connection()
    if not conn:
        return "Database connection error."

    # Initialize the cursor and fetch train details
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM TrainDetails WHERE train_id = %s', (train_id,))
        train = cursor.fetchone()
    except Exception as e:
        conn.close()
        print(f"Error fetching train details: {e}")
        return "Error fetching train details."

    # Check if train exists in the database
    if not train:
        conn.close()
        return "Train not found."

    # Handle booking submission
    if request.method == 'POST':
        try:
            seats = int(request.form['seats'])
        except ValueError:
            conn.close()
            return "Invalid seat number. Please enter a valid integer."

        # Check if there are enough seats available
        if seats > train['seat_capacity']:
            conn.close()
            return "Not enough seats available!"

        # Proceed to create the booking
        booking_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            cursor.execute(
                'INSERT INTO Bookings (user_id, train_id, booking_date, seats_booked) VALUES (%s, %s, %s, %s)',
                (session['user_id'], train_id, booking_date, seats)
            )
            conn.commit()  # Commit the transaction
        except Exception as e:
            conn.rollback()  # Roll back in case of an error
            print(f"Error creating booking: {e}")
            return "Error creating booking. Please try again."
        finally:
            conn.close()
        
        return redirect(url_for('train_details'))

    # Close the connection if GET request
    conn.close()
    return render_template('booking.html', train=train)



# Route for logging out
@app.route('/logout')
def logout():
    session.pop('user_id', None)  # Remove the user_id from the session
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
