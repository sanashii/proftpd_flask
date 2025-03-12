# !/usr/bin/env python
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
from flask_session import Session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import timedelta, datetime
import os
import json
from werkzeug.utils import secure_filename
import calendar
from functools import lru_cache
import logging
from logging.handlers import RotatingFileHandler

APP_ROOT = os.path.dirname(os.path.abspath(__file__))

# Configure logging
if not os.path.exists('logs'):
    os.mkdir('logs')
file_handler = RotatingFileHandler('logs/sftp.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)

app = Flask(__name__,
           template_folder=os.path.join(APP_ROOT, 'templates'),
           static_folder=os.path.join(APP_ROOT, 'static'))

app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('SFTP app startup')

# Session configuration
app.config.update(
    SESSION_TYPE='filesystem',
    SESSION_FILE_DIR=os.path.join(APP_ROOT, 'flask_session'),
    PERMANENT_SESSION_LIFETIME=timedelta(hours=2),
    SESSION_COOKIE_SECURE=False,  # Set to False for development (no HTTPS)
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_NAME='sftp_session',
    SESSION_COOKIE_SAMESITE='Lax'
)

Session(app)
app.config['SECRET_KEY'] = 'sftp-secret-key-change-in-production'

# Initialize rate limiter
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# File upload settings
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

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

def allowed_file(filename):
    """Check if the file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@lru_cache(maxsize=100)
def get_user_directories(username):
    """Get the list of directories a user has access to with caching."""
    if username in DEMO_USERS:
        return DEMO_USERS[username]['directories']
    return {}

@lru_cache(maxsize=100)
def get_directory_contents(username, directory):
    """Get the contents of a directory for a user with caching."""
    contents = []
    if username in DEMO_USERS and directory in DEMO_USERS[username]['directories']:
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

@lru_cache(maxsize=100)
def get_cached_stats(username, months, stat_type):
    """Get cached statistics for a user."""
    start_date, end_date = get_month_start_end(months)
    
    if stat_type == 'upload':
        return {
            'total_size': 1024 * 1024 * 150  # 150 MB for demo
        }
    elif stat_type == 'download':
        return {
            'total_size': 1024 * 1024 * 75  # 75 MB for demo
        }
    elif stat_type == 'files':
        return {
            'total_files': 25
        }

@app.before_request
def check_session():
    """Check session timeout and update last active time."""
    if session.get('username'):
        last_active = session.get('last_active')
        if last_active:
            last_active = datetime.fromisoformat(last_active)
            if datetime.now() - last_active > timedelta(minutes=25):
                app.logger.info(f"Session expired for user {session['username']}")
                session.clear()
                return redirect(url_for('login'))
        session['last_active'] = datetime.now().isoformat()

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
            session['last_active'] = datetime.now().isoformat()
            app.logger.info(f"User {username} logged in successfully")
            return redirect(url_for('index'))
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/api/directory/', defaults={'directory': ''})
@app.route('/api/directory/<path:directory>')
@limiter.limit("30 per minute")
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
@limiter.limit("10 per minute")
def upload_file(directory):
    """API endpoint to handle file uploads."""
    if not session.get('username'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    username = session['username']
    if not DEMO_USERS[username]['directories'].get(directory, {}).get('write'):
        app.logger.warning(f"Upload attempt denied for user {username} in directory {directory}")
        return jsonify({'error': 'Permission denied'}), 403
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Validate file type
    if not allowed_file(file.filename):
        app.logger.warning(f"Invalid file type attempted by user {username}: {file.filename}")
        return jsonify({'error': 'File type not allowed'}), 400
    
    # Validate file size
    file_content = file.read()
    if len(file_content) > MAX_CONTENT_LENGTH:
        app.logger.warning(f"File too large attempted by user {username}: {file.filename}")
        return jsonify({'error': 'File too large'}), 413
    
    # Reset file pointer after reading
    file.seek(0)
    
    # Secure filename
    filename = secure_filename(file.filename)
    
    # Add unique identifier to prevent filename collisions
    unique_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
    
    # Save file
    try:
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
        app.logger.info(f"File uploaded successfully by user {username}: {unique_filename}")
        return jsonify({
            'message': 'File uploaded successfully',
            'filename': unique_filename
        })
    except Exception as e:
        app.logger.error(f"File upload failed for user {username}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/<path:filepath>')
@limiter.limit("20 per minute")
def download_file(filepath):
    """API endpoint to handle file downloads."""
    if not session.get('username'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    username = session['username']
    app.logger.info(f"Download initiated by user {username}: {filepath}")
    
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
@limiter.limit("30 per minute")
def get_upload_stats(months):
    """Get upload statistics for the specified time period."""
    if not session.get('username'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    username = session['username']
    return jsonify(get_cached_stats(username, months, 'upload'))

@app.route('/api/stats/download/<int:months>')
@limiter.limit("30 per minute")
def get_download_stats(months):
    """Get download statistics for the specified time period."""
    if not session.get('username'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    username = session['username']
    return jsonify(get_cached_stats(username, months, 'download'))

@app.route('/api/stats/files/<int:months>')
@limiter.limit("30 per minute")
def get_files_stats(months):
    """Get file count statistics for the specified time period."""
    if not session.get('username'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    username = session['username']
    return jsonify(get_cached_stats(username, months, 'files'))

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    app.logger.error(f"404 error: {request.url}")
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f"500 error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(413)
def too_large_error(error):
    app.logger.warning(f"413 error: File too large")
    return jsonify({'error': 'File too large'}), 413

@app.errorhandler(429)
def ratelimit_handler(e):
    app.logger.warning(f"Rate limit exceeded: {request.url}")
    return jsonify({'error': 'Rate limit exceeded'}), 429

if __name__ == '__main__':
    app.run(debug=True, port=5001)