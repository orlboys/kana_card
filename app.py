import sqlite3
from flask import Flask, render_template, request, redirect, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'placeholder_secret_key' #change this for deployment >:(

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL, 
        password TEXT NOT NULL,
        admin BOOLEAN DEFAULT FALSE
    )
    ''')

    # ADD TABLE FOR STUDENTS, ADMINS SEPERATELY

    # ADD TABLE FOR LISTS, AND CONNECT THEM TO USERS (MANY TO MANY)

    # BASICALLY, JUST LOOK AT THE ERD !

    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    # This will probably be like a massive 'redirect' function. Something like:
    # If user is a student, redirect to student dashboard. If user is an admin, redirect to admin dashboard. Else, redirect to the login page.

    if session.get('logged_in'):
        return render_template('index.html')
        # if session.get('admin'):
        #     return redirect('/admin')
        # else:
        #     return redirect('/student')
    else:
        return redirect('/login')

## ACCOUNT MANAGEMENT ##

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST': #i.e. if its a form submission
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        if user and check_password_hash(user[2], password):
            session['logged_in'] = True
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['admin'] = user[3]
            flash('You were successfully logged in')
            return redirect('/')
        else:
            flash('Invalid credentials')
    
    return render_template('login.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST': #i.e. if its a form submission
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM users WHERE username = ?', (username,))
        user_exists = cursor.fetchone()[0] > 0

        if user_exists:
            flash('User already exists.', 'error')
        else:
            cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
            conn.commit()
            flash('Registration successful.')
            conn.close()
            return redirect('/login')
        
        conn.close()
    return render_template('register.html')
