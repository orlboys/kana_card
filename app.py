# Description: This file contains the main Flask application for the Flashcard Web Application.
# IMPROVEMENTS TO MAKE:
# - reduce repetition, especially in the database connection and closing functions.
# - add more error handling and validation for the forms.
# - add more comments to explain the logic of the code.

import sqlite3
from flask import Flask, render_template, request, redirect, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import re
from markupsafe import escape
import pyotp
import qrcode

app = Flask(__name__)
app.secret_key = 'placeholder_secret_key' #change this for deployment >:(

# Input Validation

def is_valid_item(item):
    return isinstance(item, str) and 0 < len(item) <= 255 and re.match(r'^[a-zA-Z0-9_ ]+$', item)

# Database Initialisation
def init_db():
    conn = sqlite3.connect('database.db')
    conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
    c = conn.cursor()

    # USER MANAGEMENT TABLES #
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL, 
        password TEXT NOT NULL,
        f_name TEXT NOT NULL,
        l_name TEXT NOT NULL,
        email TEXT NOT NULL,
        admin BOOLEAN DEFAULT FALSE,
        mfa_secret TEXT
    );
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS students (
        student_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    ''')

    # LIST MANAGEMENT TABLES #
    c.execute('''
    CREATE TABLE IF NOT EXISTS flashcard_lists (
        list_id INTEGER PRIMARY KEY AUTOINCREMENT,
        list_name TEXT NOT NULL
    )
    ''')

    # MANY TO MANY RELATIONSHIP - STUDENTS AND LISTS #
    c.execute('''
    CREATE TABLE IF NOT EXISTS list_students (
        list_id INTEGER NOT NULL,
        student_id INTEGER NOT NULL,
        PRIMARY KEY (list_id, student_id),
        FOREIGN KEY (list_id) REFERENCES flashcard_lists(list_id) ON DELETE CASCADE,
        FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS flashcards (
        card_id INTEGER PRIMARY KEY AUTOINCREMENT,
        list_id INTEGER NOT NULL,
        question TEXT NOT NULL,
        answer TEXT NOT NULL,
        FOREIGN KEY (list_id) REFERENCES flashcard_lists(list_id) ON DELETE CASCADE
    )
    ''')

    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    # This will probably be like a massive 'redirect' function. Something like:
    # If user is a student, redirect to student dashboard. If user is an admin, redirect to admin dashboard. Else, redirect to the login page.

    if session.get('logged_in'):
        if session.get('admin'):
            return redirect('/admin_dashboard')
        else:
            return redirect('/student_dashboard')
    else:
        return redirect('/login')

## ACCOUNT MANAGEMENT ##

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST': #i.e. if its a form submission
        username = request.form['username']
        password = request.form['password']

        # Input Validation

        if not is_valid_item(username) or not is_valid_item(password):
            flash('Invalid Input', 'error')
            return redirect('/login')

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM users WHERE username = ?', (escape(username),))
        user = cursor.fetchone()
        conn.close()
        if user and check_password_hash(user[2], password):
            #MFA
            session['pending_user'] = user[0]
            if not user["mfa_secret"]: #if the user's first time logging in, therefore no MFA secret
                return redirect('/mfa_setup')
            return redirect('/verify_mfa')
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('login.html')

## MFA ##
@app.route('/mfa_setup', methods=['POST'])
def mfa_setup():
    if 'pending_user' not in session:
        return redirect('/login')
    
    user_id = session['pending_user']

    # Retrieves the current MFA secret key for the user
    conn = sqlite3.connect('database.db') # IF THERES AN ERROR HERE its because I haven't completely followed the code from the tutorial - check the get_db_connection() function from the tutorial and implement
    cursor = conn.cursor()
    cursor.execute("SELECT mfa_secret FROM users WHERE id = ?", (user_id,))
    secret = cursor.fetchone()[0]

    # If they don't have one, generate an MFA secret key
    if not secret:
        secret = pyotp.random_base32()
        cursor.execute("UPDATE users SET mfa_secret = ? WHERE id = ?", (secret, user_id))
        conn.commit()
    conn.close()

    # Generate a QR code for the user to scan
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=session['username'], issuer_name='Flashcard App')

    qr = qrcode.make(uri)
    qr_path = "static/qrcode.png"
    qr.save(qr_path)
    return render_template('mfa_setup.html', qr_path=qr_path) # AT SOME POINT - Implement this to be a modal on the login page.

@app.route('/verify_mfa', methods=['GET', 'POST'])
def verify_mfa():
    if 'pending_user' not in session:
        return redirect('/login')
    
    user_id = session['pending_user']
    if request.method == 'POST':
        # Retrieves the code from the form
        otp_code = request.form['otp']
        conn = sqlite3.connect('database.db') # IF THERES AN ERROR HERE its because I haven't completely followed the code from the tutorial - check the get_db_connection() function from the tutorial and implement
        cursor = conn.cursor()
        cursor.execute("SELECT mfa_secret FROM users WHERE id = ?", (user_id,))
        secret = cursor.fetchone()[0]
        conn.close()
        totp = pyotp.TOTP(secret)
        if totp.verify(otp_code):
            # Get the user's details
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            user = cursor.fetchone()
            conn.close()
            session['logged_in'] = True
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['f_name'] = user[3]
            session['l_name'] = user[4]
            session['email'] = user[5]
            session['admin'] = user[6]  # Assuming admin is the 7th column
            flash('You were successfully logged in')
            print("Logged in as:", session.get('username'))
            print("Admin status:", session.get('admin'))
            print("User ID:", session.get('user_id'))
            print("Email:", session.get('email'))
            print("First Name:", session.get('f_name'))
            print("Last Name:", session.get('l_name'))

            del session['pending_user']
            return redirect('/student_dashboard')

@app.route('/register', methods=['GET','POST'])
# NOTE: for now, this is just signing up all new users as students. 
def register():
    if request.method == 'POST': #i.e. if its a form submission
        username = request.form['username']
        password = request.form['password']
        f_name = request.form['first-name']
        l_name = request.form['last-name']
        email = request.form['email']

        # Input Validation
        if not all(map(is_valid_item, [username, password, f_name, l_name, email])):
            flash('Invalid Input', 'error')
            return redirect('/register')

        hashed_password = generate_password_hash(password)

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM users WHERE username = ?', (escape(username),))
        user_exists = cursor.fetchone()[0] > 0

        if user_exists:
            flash('User already exists.', 'error')
        else:
            #Inserting into the Users Table
            cursor.execute('INSERT INTO users (username, password, f_name, l_name, email, admin) VALUES (?, ?, ?, ?, ?, ?)', (escape(username), escape(hashed_password), escape(f_name), escape(l_name), escape(email), False))
            conn.commit()

            #Getting the user_id of the user that was just inserted
            user_id = cursor.lastrowid

            #Inserting into the Students Table
            cursor.execute('INSERT INTO students (user_id) VALUES (?)', (user_id,))
            conn.commit()

            #Adding a default list for the user
            cursor.execute('SELECT list_id FROM flashcard_lists WHERE list_name = "Introduction" AND list_id = 10')
            list_result = cursor.fetchone()
            if list_result:
                if cursor.fetchone() == 0:
                    cursor.execute('INSERT INTO list_students (list_id, student_id) VALUES (?, ?)', (10, user_id))
                conn.commit()

            flash('Registration successful.')
            conn.close()
            return redirect('/login')
        
        conn.close()
    return render_template('register.html')

@app.route('/logout', methods=['POST']) # POST request to prevent CSRF
def logout():
    session.clear()
    flash('You were logged out')
    return redirect('/login')

## STUDENT ROUTES ##
@app.route('/student_dashboard')
def student_dashboard():
    if not session.get('logged_in') or session.get('admin'):
        return redirect('/login')
    
    def get_student_lists(user_id): 
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT student_id FROM students WHERE user_id = ?', (user_id,))
        student_id = cursor.fetchone()[0]
        print("Session user_id:", session.get('user_id'))
        print("Fetched Student_id", student_id)

        cursor.execute('''
        SELECT list_id, list_name
        FROM flashcard_lists
        WHERE list_id IN (
            SELECT list_id
            FROM list_students
            WHERE student_id = ?
        )
        ''', (student_id,)) # logic explanation: get all list records where the list_id is in the many-to-many table for the student

        lists = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]
        print (lists)
        conn.close()
        return lists
    
    return render_template('student_dashboard.html', lists = get_student_lists(session.get('user_id')))

@app.route('/student_list/<int:list_id>/<int:card_index>', methods=['GET', 'POST'])
def list_card(list_id, card_index=0):
    if not session.get('logged_in') or session.get('admin'):
        return redirect('/login')

    def get_list_name(list_id):
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT list_name FROM flashcard_lists WHERE list_id = ?', (list_id,))
        list_name = cursor.fetchone()[0]
        conn.close()
        return list_name

    def get_flashcards(list_id):
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT question, answer FROM flashcards WHERE list_id = ?', (list_id,))
        flashcards = cursor.fetchall()
        conn.close()
        return flashcards

    flashcards = get_flashcards(list_id)
    total_cards = len(flashcards)

    if total_cards == 0 or card_index < 0 or card_index >= total_cards:
        return "No flashcards found", 404
    
    print(f"Showing card {card_index}: {flashcards[card_index]}")

    return render_template(
        'list.html',
        list_name=get_list_name(list_id),
        flashcard=flashcards[card_index],  # Single flashcard for this page
        list_id=list_id,
        card_index=card_index,
        total_cards=total_cards
    )

## ADMIN ROUTES ##
@app.route('/admin_dashboard')
def admin_dashboard():
    if not session.get('logged_in') or not session.get('admin'):
        return redirect('/login')
    return render_template('admin_dashboard.html')

## LIST MANAGEMENT ##

@app.route('/admin_dashboard/lists', methods=['GET', 'POST'])
def list_management():
    if not session.get('logged_in') or not session.get('admin'):
        return redirect('/login')

    def get_all_lists():
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        cursor.execute('SELECT list_id, list_name FROM flashcard_lists')
        lists = cursor.fetchall()
        conn.close()
        return lists
    
    def get_all_usernames():
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        cursor.execute('SELECT username FROM users')
        usernames = [row[0] for row in cursor.fetchall()]
        conn.close()
        return usernames

    def get_all_listnames():
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        cursor.execute('SELECT list_name FROM flashcard_lists')
        listnames = [row[0] for row in cursor.fetchall()]
        conn.close()
        return listnames

    return render_template('list_management.html', lists = get_all_lists(), usernames = get_all_usernames(), listnames = get_all_listnames())

## USER MANAGEMENT ##

@app.route('/admin_dashboard/users', methods=['GET', 'POST'])
def user_management():
    if not session.get('logged_in') or not session.get('admin'):
        return redirect('/login')

    def get_all_users():
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        cursor.execute('SELECT id, username, f_name, l_name, email, admin FROM users')
        users = cursor.fetchall()
        print("Fetched Users:", users)  # Debug print
        conn.close()
        return users

    return render_template('user_management.html', users=get_all_users())

@app.route('/edit_item', methods=["POST"])
def edit_item():
    type = request.form.get("edit_type")
    id = request.form.get("edit_index")
    print("Edit Type:", type)

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    if type == "list":
        new_listname = request.form.get("new_listname")

        # Input Validation
        if not is_valid_item(new_listname):
            flash('Invalid Input', 'error')
            return redirect('/admin_dashboard/lists')

        print("New List Name:", new_listname)
        cursor.execute(
            "UPDATE flashcard_lists SET list_name = ? WHERE list_id = ?",
            (escape(new_listname), id)
        )
    elif type == "user":
        new_username = request.form.get("new_username")
        new_first_name = request.form.get("new_first_name")
        new_last_name = request.form.get("new_last_name")
        new_email = request.form.get("new_email")
        new_role = request.form.get("new_role")

        # Input Validation
        if not all(map(is_valid_item, [new_username, new_first_name, new_last_name, new_email])):
            flash('Invalid Input', 'error')
            return redirect('/admin_dashboard/users')

        print("User ID:", id)
        print("New Username:", new_username)
        print("New First Name:", new_first_name)
        print("New Last Name:", new_last_name)
        print("New Email:", new_email)
        print("New Role:", new_role)
        admin_value = 1 if new_role == 'admin' else 0
        try:
            cursor.execute(
                "UPDATE users SET username = ?, f_name = ?, l_name = ?, email = ?, admin = ? WHERE id = ?",
                (escape(new_username), escape(new_first_name), escape(new_last_name), escape(new_email), admin_value, id)
            )
        except sqlite3.Error as e:
            flash(f'Database error: {e}', 'error')
            conn.rollback()
            
    conn.commit()
    conn.close()
    if type == "list":
        return redirect('/admin_dashboard/lists')
    elif type == "user":
        return redirect('/admin_dashboard/users')
    else:
        return redirect('/admin_dashboard')

@app.route('/delete_item', methods=["POST"])
def delete_item():
    id = request.form.get("delete_index")
    type = request.form.get("delete_type")
    conn = sqlite3.connect('database.db')
    conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
    cursor = conn.cursor()
    if type == "list":
        cursor.execute(
            "DELETE FROM flashcard_lists WHERE list_id = ?",
            (id,)
        )
        cursor.execute(
            "DELETE FROM flashcards WHERE list_id = ?", 
            (id,))
    elif type == "user":
        cursor.execute(
            "DELETE FROM users WHERE id = ?",
            (id,)
        )
    conn.commit()
    conn.close()
    if type == "list":
        return redirect('/admin_dashboard/lists')
    elif type == "user":
        return redirect('/admin_dashboard/users')
    else:
        return redirect('/admin_dashboard')

@app.route('/admin_dashboard/lists/add_list', methods=['GET', 'POST'])
def add_list():
    if not session.get('logged_in') or not session.get('admin'):
        return redirect('/login')

    if request.method == 'POST':
        list_name = request.form.get('list_name')
        flashcard_count = request.form.get('flashcard_count')  # Get the flashcard count from the form

        # Input Validation
        if not is_valid_item(list_name):
            flash('Invalid Input', 'error')
            return redirect('/admin_dashboard/lists')
        
        if flashcard_count is None:
            flashcard_count = 0
        else:
            flashcard_count = int(flashcard_count)
        
        # Collect flashcards
        flashcards = []
        for i in range(1, flashcard_count + 1):
            question = request.form.get(f'flashcard_question_{i}')
            answer = request.form.get(f'flashcard_answer_{i}')
            if question and answer:
                flashcards.append((question, answer))

        #Input Validation
        if not all(map(is_valid_item, ([question, answer] for question, answer in flashcards))):
            flash('Invalid Input', 'error')

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # Insert the new list
        cursor.execute('INSERT INTO flashcard_lists (list_name) VALUES (?)', (escape(list_name,)))
        list_id = cursor.lastrowid

        # Insert the flashcards
        for question, answer in flashcards:
            cursor.execute('INSERT INTO flashcards (list_id, question, answer) VALUES (?, ?, ?)', (list_id, escape(question), escape(answer)))

        conn.commit()
        conn.close()

        flash('List added successfully', 'success')
        return redirect('/admin_dashboard/lists')

    return render_template('add_list.html')

@app.route('/assign_lists', methods=['POST'])
def assign_lists():
    if not session.get('logged_in') or not session.get('admin'):
        return redirect('/login')

    username = request.form.get('username')
    listname = request.form.get('listname')
    # Input Validation
    if not is_valid_item(username) or not is_valid_item(listname):
        flash('Invalid Input', 'error')
        return redirect('/admin_dashboard/lists')
    
    try:
        conn = sqlite3.connect('database.db')
        conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
        cursor = conn.cursor()

        user_result = cursor.execute('SELECT id FROM users WHERE username = ?', (escape(username),)).fetchone()
        if user_result is None:
            flash('User does not exist', 'error')
            return redirect('/admin_dashboard/lists')

        list_result = cursor.execute('SELECT list_id FROM flashcard_lists WHERE list_name = ?', (escape(listname),)).fetchone()
        if list_result is None:
            flash('List does not exist', 'error')
            return redirect('/admin_dashboard/lists')

        user_id = user_result[0]
        list_id = list_result[0]

        student_result = cursor.execute('SELECT student_id FROM students WHERE user_id = ?', (user_id,)).fetchone()
        if student_result is None:
            flash('User is not a student', 'error')
            return redirect('/admin_dashboard/lists')

        student_id = student_result[0]

        cursor.execute('SELECT COUNT(*) FROM list_students WHERE student_id = ? AND list_id = ?', (student_id, list_id))
        if cursor.fetchone()[0] > 0:
            flash('List already assigned to user', 'error')
            return redirect('/admin_dashboard/lists')

        cursor.execute('INSERT INTO list_students (student_id, list_id) VALUES (?, ?)', (student_id, list_id))

        conn.commit()
        flash('List assigned successfully', 'success')
    except sqlite3.IntegrityError as e:  # using this to catch the foreign key constraint error
        flash(f'Integrity error: {e}', 'error')
    except sqlite3.Error as e:  # using this to catch any other database error
        flash(f'Database error: {e}', 'error')
    finally:  # will always run - connection with the database must always be closed
        conn.close()

    return redirect('/admin_dashboard/lists')