import sqlite3
from flask import Flask, render_template, request, redirect, session, flash

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    conn = sqlite3.connect('web_app.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
    user = c.fetchone()
    conn.close()
    if user:
        session['user'] = user
        return redirect('/dashboard')
    else:
        flash('Invalid username or password')
        return redirect('/')