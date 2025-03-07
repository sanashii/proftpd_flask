# !/usr/bin/env python
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
from flask_session import Session
from datetime import timedelta, datetime
import os
import json
from werkzeug.utils import secure_filename
import calendar


APP_ROOT = os.path.dirname(os.path.abspath(__file__))

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

Session(app)
app.config['SECRET_KEY'] = 'sftp-secret-key-change-in-production'

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
    
    # Demo implementation - just return success ;; to be replaced with actual file upload logic
    return jsonify({'message': 'File uploaded successfully'})

@app.route('/api/download/<path:filepath>')
def download_file(filepath):
    """API endpoint to handle file downloads."""
    if not session.get('username'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Demo implementation - just return a message
    return jsonify({'message': 'Download initiated'})

def get_month_start_end(months_ago):
    """Get start and end dates for the specified number of months ago."""
    today = datetime.now()
    if months_ago == 1:
        # Last month
        first_day = today.replace(day=1) - timedelta(days=1)
        first_day = first_day.replace(day=1)
    else:
        # Multiple months ago
        first_day = today.replace(day=1)
        for _ in range(months_ago - 1):
            first_day = (first_day - timedelta(days=1)).replace(day=1)
    
    last_day = today.replace(day=1) - timedelta(days=1)
    return first_day, last_day

@app.route('/api/stats/upload/<int:months>')
def get_upload_stats(months):
    """Get upload statistics for the specified time period."""
    if not session.get('username'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    username = session['username']
    start_date, end_date = get_month_start_end(months)
    
    # Demo implementation - replace with actual database query
    # This would typically query the xferlog table for uploads
    demo_stats = {
        'total_size': 1024 * 1024 * 150  # 150 MB for demo
    }
    
    return jsonify(demo_stats)

@app.route('/api/stats/download/<int:months>')
def get_download_stats(months):
    """Get download statistics for the specified time period."""
    if not session.get('username'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    username = session['username']
    start_date, end_date = get_month_start_end(months)
    
    # Demo implementation - replace with actual database query
    # This would typically query the xferlog table for downloads
    demo_stats = {
        'total_size': 1024 * 1024 * 75  # 75 MB for demo
    }
    
    return jsonify(demo_stats)

@app.route('/api/stats/files/<int:months>')
def get_files_stats(months):
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    username = session['username']
    start_date, end_date = get_month_start_end(months)
    
    # TODO: Replace with actual database query
    # This is a demo implementation
    # In prod, we'd query the xferlog table:
    # SELECT COUNT(*) as total_files 
    # FROM xferlog 
    # WHERE username = %s 
    # AND date BETWEEN %s AND %s 
    # AND type = 'a' (for uploads)
    
    return jsonify({
        'total_files': 25  # Demo value only
    })

if __name__ == '__main__':
    app.run(debug=True, port=5001)  # Different port from admin app (5000)