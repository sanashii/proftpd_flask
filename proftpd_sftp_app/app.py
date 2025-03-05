# !/usr/bin/env python
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
from flask_session import Session
from datetime import timedelta
import os
import json
from werkzeug.utils import secure_filename

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

# Demo user data - Replace with actual user data from your authentication system
DEMO_USERS = {
    'user1': {
        'directories': {
            'Documents': {'read': True, 'write': True},
            'Downloads': {'read': True, 'write': False},
            'Public': {'read': True, 'write': True}
        }
    },
    'user2': {
        'directories': {
            'Projects': {'read': True, 'write': True},
            'Shared': {'read': True, 'write': False}
        }
    }
}

def get_user_directories(username):
    """Get the list of directories a user has access to."""
    if username in DEMO_USERS:
        return DEMO_USERS[username]['directories']
    return {}

def get_directory_contents(username, directory):
    """Get the contents of a directory for a user."""
    # Demo implementation - replace with actual directory listing logic
    contents = []
    if username in DEMO_USERS and directory in DEMO_USERS[username]['directories']:
        # Demo files and folders
        contents = [
            {
                'name': 'report.pdf',
                'type': 'file',
                'size': '2.5 MB',
                'modified': '2024-03-04 11:45',
                'permissions': DEMO_USERS[username]['directories'][directory]
            },
            {
                'name': 'data.xlsx',
                'type': 'file',
                'size': '1.2 MB',
                'modified': '2024-03-04 12:00',
                'permissions': DEMO_USERS[username]['directories'][directory]
            }
        ]
    return contents

@app.route('/')
def index():
    if not session.get('username'):
        return redirect(url_for('login'))
    
    username = session['username']
    directories = get_user_directories(username)
    return render_template('index.html', directories=directories)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Demo authentication - replace with actual authentication
        if username in DEMO_USERS:
            session['username'] = username
            return redirect(url_for('index'))
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/api/directory/', defaults={'directory': ''})
@app.route('/api/directory/<path:directory>')
def list_directory(directory):
    """API endpoint to list directory contents."""
    if not session.get('username'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    username = session['username']
    
    # Handle root directory or empty path
    if not directory or directory == '/':
        directories = get_user_directories(username)
        contents = [
            {
                'name': dirname,
                'type': 'directory',
                'size': '-',
                'modified': '-',
                'permissions': perms
            }
            for dirname, perms in directories.items()
        ]
        return jsonify({
            'contents': contents,
            'directory_permissions': {'write': False}  # Root directory is always read-only
        })
    
    # For specific directories
    directory = directory.strip('/')
    user_dirs = get_user_directories(username)
    
    # Check if the directory exists and get its permissions
    if directory not in user_dirs:
        return jsonify({'error': 'Directory not found'}), 404
    
    directory_permissions = user_dirs[directory]
    contents = get_directory_contents(username, directory)
    
    return jsonify({
        'contents': contents,
        'directory_permissions': directory_permissions
    })

@app.route('/api/upload/<path:directory>', methods=['POST'])
def upload_file(directory):
    """API endpoint to handle file uploads."""
    if not session.get('username'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    username = session['username']
    if not DEMO_USERS[username]['directories'].get(directory, {}).get('write'):
        return jsonify({'error': 'Permission denied'}), 403
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Demo implementation - just return success
    return jsonify({'message': 'File uploaded successfully'})

@app.route('/api/download/<path:filepath>')
def download_file(filepath):
    """API endpoint to handle file downloads."""
    if not session.get('username'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Demo implementation - just return a message
    return jsonify({'message': 'Download initiated'})

if __name__ == '__main__':
    app.run(debug=True, port=5001)  # Different port from admin app 