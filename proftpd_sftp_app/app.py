# !/usr/bin/env python
from flask import Flask, render_template, request, redirect, url_for, session
from flask_session import Session
from datetime import timedelta
import os

# Define the application root directory
APP_ROOT = os.path.dirname(os.path.abspath(__file__))

# Initialize Flask app with custom template and static folders
app = Flask(__name__,
           template_folder=os.path.join(APP_ROOT, 'templates'),
           static_folder=os.path.join(APP_ROOT, 'static'))

# Session configuration
app.config.update(
    SESSION_TYPE='filesystem',
    SESSION_FILE_DIR=os.path.join(APP_ROOT, 'flask_session'),
    PERMANENT_SESSION_LIFETIME=timedelta(hours=2),
    SESSION_COOKIE_SECURE=False,  # Set to False for development (no HTTPS)
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_NAME='sftp_session',  # Different cookie name from admin app
    SESSION_COOKIE_SAMESITE='Lax'  # Add SameSite policy for security
)

# Initialize Flask-Session
Session(app)

# Secret key for session management
app.config['SECRET_KEY'] = 'sftp-secret-key-change-in-production'

@app.route('/')
def index():
    if not session.get('username'):
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # TODO: Implement proper authentication
        # For now, just a simple check
        if username and password:
            session['username'] = username
            return redirect(url_for('index'))
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, port=5001)  # Different port from admin app 