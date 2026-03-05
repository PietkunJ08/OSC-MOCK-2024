from flask import Flask, render_template, request, redirect, url_for, flash
from enum import Enum
import sqlite3, hashlib
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.secret_key = '329396485'
db_locale = "users.db"

class User(UserMixin):
    def __init__(self, id, username, email, is_admin):
        self.id = id
        self.username = username
        self.email = email
        self.is_admin = is_admin

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    connection = sqlite3.connect(db_locale)
    cursor = connection.cursor()

    cursor.execute("SELECT id, username, email, is_admin FROM user WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    connection.close()

    if user:
        return User(id=user[0], username=user[1], email=user[2], is_admin=user[3])
    return None

class TicketType(str, Enum):
    PEAK = "peak"
    OFF_PEAK = "off-peak"

class RoomType(str, Enum):
    STANDARD = "standard"
    PREMIUM = "premium"
    LUXURY = "luxury"
    ULTIMATE = "ultimate"

class VisitType(str, Enum):
    ZOO_VISIT = "zoo-visit"
    SAFARI_RIDE = "safari-ride"
    ZOO_VISIT_SAFARI_RIDE = "zoo-visit-safari-ride"

#Database creation function
def db_create():
    connection = sqlite3.connect(db_locale)
    cursor = connection.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username VARCHAR(50) UNIQUE NOT NULL,
        email VARCHAR(100) NOT NULL,
        password VARCHAR(255) NOT NULL,
        is_admin INTEGER NOT NULL DEFAULT 0
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ticket_booking (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_type TEXT NOT NULL CHECK(ticket_type IN ('peak', 'off-peak')),
        adult_tickets INTEGER NOT NULL,
        child_tickets INTEGER NOT NULL,
        student_tickets INTEGER NOT NULL,
        senior_tickets INTEGER NOT NULL,
        family_tickets INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        FOREIGN KEY(user_id) REFERENCES user(id)
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS hotel_booking (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        adults INTEGER NOT NULL,
        children INTEGER NOT NULL,
        room_type TEXT NOT NULL CHECK(room_type IN ('standard' ,'premium', 'luxury', 'ultimate')),
        rooms INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        FOREIGN KEY(user_id) REFERENCES user(id)
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS school_visits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        school VARCHAR(50) NOT NULL,
        supervisor_name VARCHAR(50) NOT NULL,
        supervisor_email VARCHAR(100) NOT NULL,
        supervisor_number INTEGER NOT NULL,
        visit_type TEXT NOT NULL CHECK(visit_type IN ('zoo-visit', 'safari-ride', 'zoo-visit-safari-ride')),
        children INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        FOREIGN KEY(user_id) REFERENCES user(id)
    )
    """)

    connection.commit()
    connection.close()

#Routing function
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/booking')
@login_required
def booking():
    return render_template('booking.html')

@app.route('/ticket-booking', methods=["GET", "POST"])
@login_required
def ticket_booking():
    if request.method == "POST":
        ticket_type = request.form['ticket-type']
        adult_tickets = int(request.form['adult-tickets'])
        child_tickets = int(request.form['child-tickets'])
        student_tickets = int(request.form['student-tickets'])
        senior_tickets = int(request.form['senior-tickets'])
        family_tickets = int(request.form['family-tickets'])
        user_id = current_user.id
        connection = sqlite3.connect(db_locale)
        cursor = connection.cursor()
        
        family_tickets_persons = family_tickets * 4
        if adult_tickets + student_tickets + senior_tickets + family_tickets == 0 and child_tickets >= 0:
            flash('You must select at least 1 adult, student, senior, or family ticket.')
            return redirect(url_for('ticket_booking'))
        elif adult_tickets + child_tickets + student_tickets + senior_tickets + family_tickets_persons > 20:
            flash('You cannot exceed the 20 person limit.')
            return redirect(url_for('ticket_booking'))
        try:
            cursor.execute("""INSERT INTO ticket_booking 
                           (ticket_type, adult_tickets, child_tickets, student_tickets, senior_tickets, family_tickets, user_id) 
                           VALUES(?, ?, ?, ?, ?, ?, ?)""", 
                           (ticket_type, adult_tickets, child_tickets, student_tickets, senior_tickets, family_tickets, user_id))
            connection.commit()
            flash("Booking Successful!")
        finally:
            connection.close()
            return redirect(url_for('ticket_booking'))
    return render_template('ticket_booking.html')

@app.route('/hotel-booking', methods=["GET", "POST"])
@login_required
def hotel_booking():
    if request.method == "POST":
        adults = int(request.form['adults'])
        children = int(request.form['children'])
        room_type = request.form['room-type']
        rooms = int(request.form['rooms'])
        user_id = current_user.id
        connection = sqlite3.connect(db_locale)
        cursor = connection.cursor()
        if adults + children > 20:
            flash('You cannot exceed the 20 person limit.')
            return redirect(url_for('hotel_booking'))
        elif adults + children < rooms:
            flash('You cannot book more rooms than there are persons.')
            return redirect(url_for('hotel_booking'))
        try:
            cursor.execute("""INSERT INTO hotel_booking
                           (adults, children, room_type, rooms, user_id) 
                           VALUES(?, ?, ?, ?, ?)""",
                           (adults, children, room_type, rooms, user_id))
            connection.commit()
            flash('Booking Successful!')
        finally:
            connection.close()
            return redirect(url_for('hotel_booking'))
    return render_template('hotel_booking.html')

@app.route('/education')
@login_required
def education():
    return render_template('education.html')

@app.route('/worksheets')
@login_required
def worksheets():
    return render_template('worksheets.html')

@app.route('/school-visits', methods=["GET", "POST"])
@login_required
def school_visits():
    if request.method == "POST":
        school = request.form['school']
        supervisor_name = request.form['supervisor-name']
        supervisor_email = request.form['supervisor-email']
        supervisor_number = request.form['supervisor-number']
        visit_type = request.form['visit-type']
        children = int(request.form['children'])
        user_id = current_user.id
        connection = sqlite3.connect(db_locale)
        cursor = connection.cursor()
        try:
            cursor.execute("""INSERT INTO school_visits
                           (school, supervisor_name, supervisor_email, supervisor_number, visit_type, children, user_id)
                           VALUES(?, ?, ?, ?, ?, ?, ?)""",
                           (school, supervisor_name, supervisor_email, supervisor_number, visit_type, children, user_id))
            connection.commit()
            flash('Booking Successful!')
        finally:
            connection.close()
            return redirect(url_for('school_visits'))
    return render_template('school_visits.html')

@app.route('/animals')
@login_required
def animals():
    return render_template('animals.html')

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        email = request.form['email']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        connection = sqlite3.connect(db_locale)
        cursor = connection.cursor()
        cursor.execute("SELECT id, username, email, is_admin FROM user WHERE username=? AND email=? AND password=?", (username, email, password))
        user = cursor.fetchone()
        if user:
            login_user(User(user[0], user[1], user[2], user[3]))
            flash("Login successful!")
            if current_user.is_admin:
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
        username = request.form['username']
        email = request.form['email']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        connection = sqlite3.connect(db_locale)
        cursor = connection.cursor()
        try:
            cursor.execute("INSERT INTO user (username, email, password) VALUES (?, ?, ?)", (username, email, password))
            connection.commit()
            flash("Register successful. Please log in.")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Username already exists.")
            return redirect(url_for("register"))
        finally:
            connection.close()
    return render_template('register.html')

@app.route('/account')
@login_required
def account():
    connection = sqlite3.connect(db_locale)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, ticket_type, adult_tickets, child_tickets,
                student_tickets, senior_tickets, family_tickets
        FROM ticket_booking
        WHERE user_id = ?
    """, (current_user.id,))
    ticket_bookings = cursor.fetchall()

    cursor.execute("""
        SELECT id, adults, children, room_type, rooms
        FROM hotel_booking
        WHERE user_id = ?
    """, (current_user.id,))
    hotel_bookings = cursor.fetchall()

    connection.close()

    return render_template(
        'account.html',
        ticket_bookings=ticket_bookings,
        hotel_bookings=hotel_bookings
    )
    
@app.route('/delete-ticket/<int:booking_id>', methods=["POST"])
@login_required
def delete_ticket_booking(booking_id):
    connection = sqlite3.connect(db_locale)
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM ticket_booking
        WHERE id = ? AND user_id = ?
    """, (booking_id, current_user.id))

    connection.commit()
    connection.close()

    flash('Ticket booking deleted')
    return redirect(url_for('account'))

@app.route('/delete-hotel/<int:booking_id>', methods=["POST"])
@login_required
def delete_hotel_booking(booking_id):
    connection = sqlite3.connect(db_locale)
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM hotel_booking
        WHERE id = ? AND user_id = ?
    """, (booking_id, current_user.id))

    connection.commit()
    connection.close()

    flash('Hotel booking deleted')
    return redirect(url_for('account'))

@app.route('/admin-account')
@login_required
def admin_account():
    if current_user.is_admin:
        return render_template('admin_account.html')
    else:
        flash("This is an admin only area, you cannot access this.")
        return redirect(url_for('account'))

@app.route('/terms-and-conditions')
def terms_and_conditions():
    return render_template('terms_and_conditions.html')

@app.route('/privacy-policy')
def privacy_policy():
    return render_template('privacy_policy.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out.')
    return redirect(url_for('index'))

if __name__ == '__main__':
    db_create()
    app.run(debug=True)
