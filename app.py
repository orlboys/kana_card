# Description: This file contains the main Flask application for the Flashcard Web Application.
# IMPROVEMENTS TO MAKE:

# - add more comments to explain the logic of the code.

# Flask / Functionality Imports
import sqlite3 # For database operations
from flask import Flask, render_template, request, redirect, session, flash # Flask imports

# Security Imports
from werkzeug.security import generate_password_hash, check_password_hash # For hashing passwords
from markupsafe import escape # For escaping user input
from flask_wtf import CSRFProtect # For CSRF protection
from forms import LoginForm, RegisterForm, ListForm, UserEditForm, ListEditForm, AssignListForm, MFAVerificationForm, LogoutForm, DeleteItemForm # For input validation and CSRF protection
from flask_limiter import Limiter # For rate limiting
from flask_limiter.util import get_remote_address # For rate limiting
from datetime import timedelta # For session timeout
import logging # For logging
from error_handlers import register_error_handlers # For error handling

# MFA Imports
import pyotp # For MFA
import qrcode # For generating QR codes

app = Flask(__name__)
app.secret_key = 'placeholder_secret_key' #change this for deployment >:(

# Session Timeout
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=15)

# Rate Limiting
limiter = Limiter(get_remote_address, app=app, default_limits=["10 per minute"])

# CSRF Protection
csrf = CSRFProtect(app)

# Logging
logging.basicConfig(
    filename='app.log', # Log file
    level=logging.DEBUG, # Log level
    format='%(asctime)s - %(levelname)s - %(message)s' # Log format
)
# Cookie Security
app.config.update(
    SESSION_COOKIE_SECURE=True, # Enforces HTTPS
    SESSION_COOKIE_HTTPONLY=True, # Prevents client-side JS from accessing session cookies
    SESSION_COOKIE_SAMESITE="Strict" # Prevents CSRF attacks - cookies can only be sent to the same site that set them
    )

# Enforcing HTTPS usage
@app.before_request
def enforce_https():
    if not request.is_secure and app.env != "development":
        return redirect(request.url.replace("http://", "https://")) # NOTE: THIS IS A TEMPORARY SOLUTION FOR OFFLINE TESTING PURPOSES. PLEASE USE redirect("https://domain_name.com/" + request.path) FOR PRODUCTION!

def make_session_permanent():
    session.permanent = True

# Error Handlers
register_error_handlers(app)

# Context Processor to make Logout Form available Globally
@app.context_processor
def inject_logout_form():
    return dict(logout_form=LogoutForm())

def init_db():
    conn = sqlite3.connect('database.db')
    conn.execute("PRAGMA foreign_keys = ON")
    c = conn.cursor()

    try:
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

        c.execute('''
        CREATE TABLE IF NOT EXISTS flashcard_lists (
            list_id INTEGER PRIMARY KEY AUTOINCREMENT,
            list_name TEXT NOT NULL
        )
        ''')

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
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        conn.rollback()
        # Handle the error appropriately (e.g., log it, display an error message)
        # It might be appropriate to re-raise the exception in some cases
    finally:
        conn.close()

init_db()

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
    return conn

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
    login_form = LoginForm()
    mfa_form = MFAVerificationForm()
    if login_form.validate_on_submit():  # If the form is submitted... A POST request. Combines submission and validation methods.
        username = escape(login_form.username.data)
        password = login_form.password.data

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            user = cursor.fetchone()

        if user and check_password_hash(user[2], password):
            # MFA
            session['pending_user'] = user[0]
            session['username'] = user[1]
            logging.info(f"User {username} logged in")
            if not user[7]:  # if the user's first time logging in, therefore no MFA secret
                return redirect('/mfa_setup')
            return render_template('login.html', login_form=login_form, mfa_form=mfa_form, show_mfa_modal=True)
        else:
            flash('The username or password you entered is incorrect. Please try again.', 'error')
            logging.warning(f'Failed login attempt for user {username}')

    return render_template('login.html', login_form=login_form, mfa_form=mfa_form, show_mfa_modal=False)

## MFA ##
@app.route('/mfa_setup', methods=['GET', 'POST'])
def mfa_setup():
    if 'pending_user' not in session:
        logging.warning("User attempted to access MFA setup without logging in")
        return redirect('/login')
    
    user_id = session['pending_user']

    # Retrieves the current MFA secret key for the user
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT mfa_secret FROM users WHERE id = ?", (user_id,))
        secret = cursor.fetchone()[0]

        # If they don't have one, generate an MFA secret key
        if not secret:
            secret = pyotp.random_base32()
            cursor.execute("UPDATE users SET mfa_secret = ? WHERE id = ?", (secret, user_id))
            conn.commit()

    # Generate a QR code for the user to scan
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=session['username'], issuer_name='Flashcard App')

    qr = qrcode.make(uri)
    qr_path = 'static/qrcode.png'
    qr.save(qr_path)
    return render_template('mfa_setup.html', qr_path=qr_path)

@app.route('/verify_mfa', methods=['POST'])
def verify_mfa():
    if 'pending_user' not in session:
        return redirect('/login')
    
    form = MFAVerificationForm()
    if form.validate_on_submit():
        user_id = session['pending_user']
        otp_code = form.verification_code.data
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT mfa_secret FROM users WHERE id = ?", (user_id,))
            secret = cursor.fetchone()[0]

        totp = pyotp.TOTP(secret)
        if totp.verify(otp_code):
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
                user = cursor.fetchone()

            session['logged_in'] = True
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['f_name'] = user[3]
            session['l_name'] = user[4]
            session['email'] = user[5]
            session['admin'] = user[6]  # Assuming admin is the 7th column
            flash('You were successfully logged in', 'success')
            print("Logged in as:", session.get('username'))
            print("Admin status:", session.get('admin'))
            print("User ID:", session.get('user_id'))
            print("Email:", session.get('email'))
            print("First Name:", session.get('f_name'))
            print("Last Name:", session.get('l_name'))

            del session['pending_user']
            logging.info(f"User {session['username']} successfully logged in")
            return redirect('/')
        else:
            flash('The OTP you entered is incorrect. Please try again.', 'error')
            logging.warning(f'Failed MFA verification for userid {session["pending_user"]}')
            return redirect('/login')
    return redirect('/login')


@app.route('/register', methods=['GET', 'POST'])
def register():
    register_form = RegisterForm()
    if register_form.validate_on_submit():  # i.e. if it's a form submission
        username = escape(register_form.username.data)
        password = register_form.password.data
        f_name = escape(register_form.first_name.data)
        l_name = escape(register_form.last_name.data)
        email = escape(register_form.email.data)

        hashed_password = generate_password_hash(password)
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('SELECT COUNT(*) FROM users WHERE username = ?', (username,))
                user_exists = cursor.fetchone()[0] > 0

                if user_exists:
                    flash('The username you entered is already taken. Please choose a different username.', 'error')
                    logging.warning(f'User attempted to register as {username}, who already exists')
                else:
                    # Inserting into the Users Table
                    cursor.execute('INSERT INTO users (username, password, f_name, l_name, email, admin) VALUES (?, ?, ?, ?, ?, ?)', (username, hashed_password, f_name, l_name, email, False))
                    conn.commit()

                    # Getting the user_id of the user that was just inserted
                    user_id = cursor.lastrowid

                    # Inserting into the Students Table
                    cursor.execute('INSERT INTO students (user_id) VALUES (?)', (user_id,))
                    conn.commit()

                    # Adding a default list for the user
                    cursor.execute('SELECT list_id FROM flashcard_lists WHERE list_name = "Introduction"')
                    list_result = cursor.fetchone()
                    if list_result:
                        list_id = list_result[0]  # Extract the list_id
                        cursor.execute('SELECT student_id FROM students WHERE user_id = ?', (user_id,))
                        student_id = cursor.fetchone()[0]
                        
                        # Check if the student is already in the list
                        cursor.execute('SELECT 1 FROM list_students WHERE list_id = ? AND student_id = ?', (list_id, student_id))
                        if not cursor.fetchone():  # If no row exists, the student is not registered
                            cursor.execute('INSERT INTO list_students (list_id, student_id) VALUES (?, ?)', (list_id, student_id))
                            conn.commit()
                            flash('Registration successful.', 'success')
                        else:
                            flash('Student is already registered for this list.', 'info')
                    logging.info(f"User {username} registered successfully")
        except sqlite3.Error as e:
            flash('An unexpected error occurred while processing your request. Please try again later.', 'error')
            logging.error(f'Database error: {e} on user registration')
            conn.rollback()
        return redirect('/login')
    else:
        flash('There was an error with your form submission. Please check your input and try again.', 'error')
        logging.warning("User made an invalid request to register")
        logging.debug(f"Form data: {register_form.data}")
        logging.debug(f"Form errors: {register_form.errors}")

    return render_template('register.html', register_form=register_form)

@app.route('/logout', methods=['POST']) # POST request to prevent CSRF
def logout():
    form = LogoutForm()
    if form.submit.data:
        logging.info(f"User {session['username']} logged out")
        session.clear()
        flash('You were logged out')
        return redirect('/login')
    else:
        flash('Invalid request', 'error')
        logging.warning(f"Invalid request to logout made by {session['username']}")
        return redirect('/')

## STUDENT ROUTES ##
@app.route('/student_dashboard')
def student_dashboard():
    if not session.get('logged_in') or session.get('admin'):
        logging.warning(f'User attempted to access student dashboard without logging in as a student')
        return redirect('/login')
    
    def get_student_lists(user_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            try:
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
            except sqlite3.Error as e:
                flash(f'Database error: {e}', 'error')
                logging.error(f'Database error: {e} on fetching student lists')
                lists = []
        print(lists)
        return lists
    logging.info(f"User {session['username']} accessed the student dashboard")
    return render_template('student_dashboard.html', lists = get_student_lists(session.get('user_id')))

@app.route('/student_list/<int:list_id>/<int:card_index>', methods=['GET', 'POST'])
def list_card(list_id, card_index=0):
    if not session.get('logged_in') or session.get('admin'):
        logging.warning(f'User attempted to access flashcard view without logging in as a student')
        return redirect('/login')
    
    def get_list_name(list_id):
        with get_db_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute('SELECT list_name FROM flashcard_lists WHERE list_id = ?', (list_id,))
                list_name = cursor.fetchone()[0]
            except sqlite3.Error as e:
                flash(f'Database error, unable to fetch list name: {e}', 'error')
                logging.error(f'Database error: {e} on fetching list name')
                list_name = None
        return list_name

    def get_flashcards(list_id):
        with get_db_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute('SELECT question, answer FROM flashcards WHERE list_id = ?', (list_id,))
                flashcards = cursor.fetchall()
            except sqlite3.Error as e:
                flash(f'Database error, unable to fetch flashcards: {e}', 'error')
                logging.error(f'Database error: {e} on fetching flashcards')
                flashcards = []
        return flashcards

    flashcards = get_flashcards(list_id)
    total_cards = len(flashcards)

    if total_cards == 0 or card_index < 0 or card_index >= total_cards:
        logging.error(f"User {session['username']} attempted to access a non-existent flashcard. List ID: {list_id}, Card Index: {card_index}")
        return "No flashcards found", 404
    
    logging.info(f"User {session['username']} accessed flashcard {card_index} in list {list_id}")

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
        logging.warning(f'User attempted to access admin dashboard without logging in as an admin')
        return redirect('/login')
    logging.info(f"User {session['username']} accessed the admin dashboard")
    return render_template('admin_dashboard.html')

## LIST MANAGEMENT ##

@app.route('/admin_dashboard/lists', methods=['GET', 'POST'])
def list_management():
    if not session.get('logged_in') or not session.get('admin'):
        logging.warning(f'User attempted to access list management without logging in as an admin')
        return redirect('/login')

    def get_all_lists():
        with get_db_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute('SELECT list_id, list_name FROM flashcard_lists')
                lists = cursor.fetchall()
            except sqlite3.Error as e:
                flash(f'Database error - Unable to fetch Lists: {e}', 'error')
                logging.error(f'Database error: {e} on fetching lists')
                lists = []
        return lists
    
    def get_all_usernames(): # Get all usernames for the assign list form
        with get_db_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute('SELECT username FROM users')
                usernames = [row[0] for row in cursor.fetchall()]
            except sqlite3.Error as e:
                flash(f'Database error - Unable to fetch Usernames: {e}', 'error')
                logging.error(f'Database error: {e} on fetching usernames')
                usernames = []
        return usernames

    def get_all_listnames():
        with get_db_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute('SELECT list_name FROM flashcard_lists')
                listnames = [row[0] for row in cursor.fetchall()]
            except sqlite3.Error as e:
                flash(f'Database error - Unable to fetch Listnames: {e}', 'error')
                logging.error(f'Database error: {e} on fetching listnames')
                listnames = []
        return listnames
    
    list_form = ListEditForm()
    delete_form = DeleteItemForm()
    add_list_form = ListForm()
    assign_form = AssignListForm()
    logging.info(f"User {session['username']} accessed the list management page")
    return render_template('list_management.html', lists = get_all_lists(), usernames = get_all_usernames(), listnames = get_all_listnames(), list_form=list_form, delete_form=delete_form, add_list_form=add_list_form, assign_form=assign_form)

## USER MANAGEMENT ##

@app.route('/admin_dashboard/users', methods=['GET', 'POST'])
def user_management():
    if not session.get('logged_in') or not session.get('admin'):
        logging.warning(f'User attempted to access user management without logging in as an admin')
        return redirect('/login')
    
    def get_all_users():
        with get_db_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute('SELECT id, username, f_name, l_name, email, admin FROM users')
                users = cursor.fetchall()
                print("Fetched Users:", users)  # Debug print
            except sqlite3.Error as e:
                flash(f'Database error - Unable to fetch Users: {e}', 'error')
                logging.error(f'Database error: {e} on fetching users')
                users = []
        return users
    
    user_form = UserEditForm()
    delete_form = DeleteItemForm(request.form)
    logging.info(f"User {session['username']} accessed the user management page")
    return render_template('user_management.html', users=get_all_users(), user_form=user_form, delete_form=delete_form)


@app.route('/edit_item', methods=["POST"])
@limiter.limit("5 per minute")
def edit_item():
    user_form = UserEditForm()
    list_form = ListEditForm()

    # Debug statements
    logging.debug("User Form Data:", user_form.data)
    logging.debug("List Form Data:", list_form.data)
    logging.debug("User Form Validation:", user_form.validate_on_submit())
    logging.debug("List Form Validation:", list_form.validate_on_submit())

    # User Edit Form
    if user_form.validate_on_submit() and user_form.edit_index.data:
        id = user_form.edit_index.data
        new_username = user_form.new_username.data
        new_first_name = user_form.new_first_name.data
        new_last_name = user_form.new_last_name.data
        new_email = user_form.new_email.data
        new_role = user_form.new_role.data

        with get_db_connection() as conn:
            cursor = conn.cursor()
            admin_value = 1 if new_role == 'admin' else 0
            try:
                cursor.execute(
                    "UPDATE users SET username = ?, f_name = ?, l_name = ?, email = ?, admin = ? WHERE id = ?",
                    (new_username, new_first_name, new_last_name, new_email, admin_value, id)
                )
                conn.commit()
                logging.info(f"User {session['username']} updated user {id} with new values: {new_username}, {new_first_name}, {new_last_name}, {new_email}, {new_role}")
            except sqlite3.Error as e:
                flash(f'Database error: {e}', 'error')
                logging.error(f'Database error: {e} on updating user')
                conn.rollback()
            return redirect('/admin_dashboard/users')
        
    # List Edit Form #
    elif list_form.validate_on_submit() and list_form.edit_index.data:
        id = list_form.edit_index.data
        new_listname = list_form.new_listname.data

        with get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "UPDATE flashcard_lists SET list_name = ? WHERE list_id = ?",
                    (new_listname, id)
                )
                conn.commit()
                logging.info(f"User {session['username']} updated list {id} with new name: {new_listname}")
            except sqlite3.Error as e:
                flash(f'Database error: {e}', 'error')
                logging.error(f'Database error: {e} on updating list')
                conn.rollback()
            return redirect('/admin_dashboard/lists')

    flash('Invalid request', 'error')
    logging.warning(f"User {session['username']} made an invalid request to edit an item")
    return redirect('/admin_dashboard')

@app.route('/delete_item', methods=["POST"])
@limiter.limit("4 per minute")
def delete_item():
    delete_form = DeleteItemForm(request.form)
    logging.debug('Delete Index: ', delete_form.delete_index.data)
    logging.debug('Delete Type: ', delete_form.delete_type.data)
    if delete_form.validate_on_submit():
        id = delete_form.delete_index.data
        type = delete_form.delete_type.data
        print(f"Delete Type: {type}")
        print(f"Delete ID: {id}")
        with get_db_connection() as conn:
            try:
                cursor = conn.cursor()
                if type == "list":
                    cursor.execute(
                        "DELETE FROM flashcard_lists WHERE list_id = ?",
                        (id,)
                    ) # This will cascade delete the flashcards as well
                    conn.commit()
                    logging.info(f"User {session['username']} deleted list {id}")
                elif type == "user":
                    cursor.execute(
                        "DELETE FROM users WHERE id = ?",
                        (id,)
                    ) # This will cascade delete the student record as well
                    logging.info(f"User {session['username']} deleted user {id}")
                conn.commit()
            except sqlite3.Error as e:
                flash(f'Database error: {e}', 'error')
                logging.error(f'Database error: {e} on deleting item')
                conn.rollback()
        if type == "list":
            return redirect('/admin_dashboard/lists')
        elif type == "user":
            return redirect('/admin_dashboard/users')
        
    logging.warning(f"User {session['username']} made an invalid request to delete an item")
    flash('Invalid request', 'error')
    return redirect('/admin_dashboard')

@app.route('/admin_dashboard/lists/add_list', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def add_list():
    if not session.get('logged_in') or not session.get('admin'):
        logging.warning(f'User attempted to access list addition without logging in as an admin')
        return redirect('/login')
    
    add_list_form=ListForm()
    if add_list_form.validate_on_submit() and add_list_form.flashcards.data:
        list_name = add_list_form.list_name.data
        flashcards = [{'question': fc.question.data, 'answer': fc.answer.data} for fc in add_list_form.flashcards]
        with get_db_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO flashcard_lists (list_name) VALUES (?)', (list_name,))
                list_id = cursor.lastrowid
                for flashcard in flashcards:
                    cursor.execute('INSERT INTO flashcards (list_id, question, answer) VALUES (?, ?, ?)', (list_id, flashcard['question'], flashcard['answer'] ))
                conn.commit()
                flash('List Added', 'success')
                logging.info(f"User {session['username']} added list {list_name}")
            except sqlite3.Error as e:
                flash(f'Database error: {e}', 'error')
                logging.error(f'Database error: {e} on adding list')
                conn.rollback()
    return redirect('/admin_dashboard/lists')

@app.route('/assign_lists', methods=['POST'])
def assign_lists():
    if not session.get('logged_in') or not session.get('admin'):
        logging.warning(f'User attempted to access list assignment without logging in as an admin')
        return redirect('/login')
    
    assign_form = AssignListForm()

    username = escape(assign_form.username.data)
    listname = escape(assign_form.listname.data)
    
    try:
        if assign_form.validate_on_submit():
            with get_db_connection() as conn:
                cursor = conn.cursor()

                user_result = cursor.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
                if user_result is None:
                    flash('The specified user does not exist. Please check the username and try again.', 'error')
                    logging.warning(f'User {session["username"]} attempted to assign a list to a non-existent user')
                    return redirect('/admin_dashboard/lists')

                list_result = cursor.execute('SELECT list_id FROM flashcard_lists WHERE list_name = ?', (listname,)).fetchone()
                if list_result is None:
                    flash('The specified list does not exist. Please check the list name and try again.', 'error')
                    logging.warning(f'User {session["username"]} attempted to assign a non-existent list to a user')
                    return redirect('/admin_dashboard/lists')

                user_id = user_result[0]
                list_id = list_result[0]

                student_result = cursor.execute('SELECT student_id FROM students WHERE user_id = ?', (user_id,)).fetchone()
                if student_result is None:
                    flash('The specified user is not a student. Please check the user details and try again.', 'error')
                    logging.warning(f'User {session["username"]} attempted to assign a list to a non-student user')
                    return redirect('/admin_dashboard/lists')

                student_id = student_result[0]

                cursor.execute('SELECT COUNT(*) FROM list_students WHERE student_id = ? AND list_id = ?', (student_id, list_id))
                if cursor.fetchone()[0] > 0:
                    logging.warning(f'User {session["username"]} attempted to assign a list to a user that already has it')
                    flash('The list is already assigned to the specified user.', 'error')
                    return redirect('/admin_dashboard/lists')

                cursor.execute('INSERT INTO list_students (student_id, list_id) VALUES (?, ?)', (student_id, list_id))

                conn.commit()
                flash('List assigned successfully', 'success')
                logging.info(f"User {session['username']} assigned list {listname} to user {username}")
        else:
            flash('There was an error with your form submission. Please check your input and try again.', 'error')
            logging.warning(f'User {session["username"]} made an invalid request to assign a list')
    except sqlite3.IntegrityError as e:  # using this to catch the foreign key constraint error
        flash('An unexpected error occurred while processing your request. Please try again later.', 'error')
        logging.error(f'Integrity error: {e} on assigning list')
    except sqlite3.Error as e:  # using this to catch any other database error
        flash('An unexpected error occurred while processing your request. Please try again later.', 'error')
        logging.error(f'Database error: {e} on assigning list')
    except Exception as e:
        flash('An unexpected error occurred. Please try again later.', 'error')
        logging.error(f'An error occurred: {e} on assigning list')
    return redirect('/admin_dashboard/lists')

# Making Flask run on SSL
if __name__ == '__main__':
    app.run(debug=True, ssl_context=('cert.pem', 'key.pem'), host="0.0.0.0", port=443) # Change to debug=False for production