from flask import Flask, render_template, request, redirect, url_for, flash, session
from enum import Enum
import sqlite3, hashlib

app = Flask(__name__)
app.secret_key = '329396485'
db_locale = "users.db"

connection = sqlite3.connect(db_locale)
cursor = connection.cursor()

#Database creation function
def db_create():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email VARCHAR(100) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ticket_booking (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_type ENUM,
        adult_tickets INTEGER,
        child_tickets INTEGER,
        student_tickets INTEGER,
        family_tickets INTEGER,
        user_id INTEGER,
        FOREIGN KEY(user_id) REFERENCES user(id)
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS hotel_booking (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        adults INTEGER,
        children INTEGER,
        room_type ENUM,
        rooms INTEGER,
        user_id INTEGER,
        FOREIGN KEY(user_id) REFERENCES user(id)
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS school_visits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        school VARCHAR(50),
        supervisor_name VARCHAR(50),
        supervisor_email VARCHAR(100),
        supervisor_number INTEGER,
        visit_type ENUM,
        children INTEGER
    )
    """)

    connection.commit()
    connection.close()

#Routing function
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/booking')
def booking():
    return render_template('booking.html')

@app.route('/education')
def education():
    return render_template('education.html')

@app.route('/ticket-booking')
def ticket_booking():
    return render_template('ticket_booking.html')

@app.route('/hotel-booking')
def hotel_booking():
    return render_template('hotel_booking.html')

@app.route('/worksheets')
def worksheets():
    return render_template('worksheets.html')

@app.route('/animals')
def animals():
    return render_template('animals.html')

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form['email']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        connection = sqlite3.connect(db_locale)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM user WHERE email=? AND password=?", (email, password))
        user = cursor.fetchone()
        if user:
            session['email'] = email
            flash("Login successful!")
            if email == "admin@rza.zoo":
                return redirect(url_for('admin_account'))
            else:
                return redirect(url_for('account'))
        else:
            flash("Invalid credentials.")
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form['email']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        connection = sqlite3.connect(db_locale)
        cursor = connection.cursor()
        try:
            cursor.execute("INSERT INTO user (email, password) VALUES (?, ?)", (email, password))
            connection.commit()
            flash("Register successful. Please log in.")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Email already exists.")
            return redirect(url_for("register"))
        finally:
            connection.close()
    return render_template('register.html')

@app.route('/account')
def account():
    if 'email' in session:
        return render_template('account.html', email=session['email'])
    else:
        flash('Please log in first.')
        return redirect(url_for('login'))

@app.route('/admin-account')
def admin_account():
    if 'email' in session:
        email = session['email']
        if email == 'admin@rza.zoo':
            return render_template('admin_account.html')
        else:
            flash("This is an admin only area, you cannot access this.")
            return redirect(url_for('account'))
    else:
        flash('Please log in first.')
        return redirect(url_for('login'))

@app.route('/terms-and-conditions')
def terms_and_conditions():
    return render_template('terms_and_conditions.html')

@app.route('/privacy-policy')
def privacy_policy():
    return render_template('privacy_policy.html')

@app.route('/logout')
def logout():
    session.pop('email', None)
    flash('Logged out.')
    return redirect(url_for('index'))

if __name__ == '__main__':
    db_create()
    app.run(debug=True)