# !/usr/bin/env python
import csv
from functools import wraps
from io import StringIO, TextIOWrapper
from flask import Flask, Response, jsonify, render_template, url_for
from flask import request, redirect, session
from flask_session import Session
from flask_migrate import Migrate
from flask_ldap3_login import LDAP3LoginManager
from flask_login import LoginManager, login_user
from datetime import datetime, timedelta, timezone
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import hashlib
import binascii
import random
import string
from models import db, User, TraxUser, Group, HostKey, LoginHistory, UserKey, XferLog, AdminLog


app = Flask(__name__)


@app.template_filter('datetime')
def format_datetime(value):
    if value is None:
        return 'Never'
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return value
    return value.strftime('%Y-%m-%d %H:%M:%S')


# app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+mysqlconnector://proftpd_stage:####@FXCEBFS0304?charset=utf8"
# app.config['SECRET_KEY'] = '####'
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+mysqlconnector://proftpd_stage:C{7#iUoNc82@FXCEBFS0304/proftpd?charset=utf8"
app.config['SECRET_KEY'] = 'smiskisecretkey1738dummydingdong'

app.config['SESSION_TYPE'] = 'filesystem'  # Store sessions in filesystem
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)  # Session timeout
app.config['SESSION_COOKIE_SECURE'] = True  # Only send cookie over HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True

app.config['LDAP_HOST'] = 'dc0100.s03.filex.com'
app.config['LDAP_PORT'] = 389
app.config['LDAP_USE_SSL'] = False
app.config['LDAP_BASE_DN'] = 'dc=filteredsecurity,dc=filex,dc=com'
app.config['LDAP_USER_DN'] = 'FILTEREDSECURIT'
app.config['LDAP_USER_RDN_ATTR'] = 'sAMAccountName'
app.config['LDAP_BIND_USER_DN'] = ''
app.config['LDAP_BIND_USER_PASSWORD'] = ''

app.config['LDAP_GROUP_OBJECT_FILTER'] = '(objectClass=group)'
app.config['LDAP_GROUP_MEMBERS_ATTR'] = 'member'

Session(app)
db.init_app(app)
migrate = Migrate(app, db)

# LDAP Config -- load here, this must be initiated after the config binding
ldap_manager = LDAP3LoginManager(app)
login_manager = LoginManager(app)


@login_manager.user_loader
def load_user(id):
    return User.query.get(id)


@ldap_manager.save_user
def save_user(dn, username, data, memberships):
    user = User.query.filter_by(username=username).first()
    if not user:
        user = User(
            username=username,
            email=data.get('mail', [None])[0],
            name=data.get('displayName', [None])[0]
        )
        db.session.add(user)
        db.session.commit()
    return user


@app.route('/', methods=['GET', 'POST'])
def login():
    session.clear()

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")  # Keep for future LDAP implementation

        # Admin fallback
        if username == "admin" and password == "admin":
            session["username"] = "admin"
            session["user_type"] = "admin"
            session["can_view"] = True
            session["can_create"] = True
            session["can_modify"] = True
            return redirect(url_for('home'))

        # Check if user exists and is enabled in trax_users table
        user = TraxUser.query.filter_by(username=username, is_enabled=True).first()
        if not user:
            return render_template('login.html', show_modal='error',
                                error_message='Account does not exist or is disabled.')

        # Set session data based on user privileges
        session["username"] = username
        session["user_type"] = user.user_type
        session["can_view"] = user.can_view
        session["can_create"] = user.can_create
        session["can_modify"] = user.can_modify

        return redirect(url_for('home'))

    return render_template('login.html')


# Permission decorators
# *NOTE: EVERY ADMIN AND USER ARE SET TO BE ABLE TO VIEW BY DEFAULT because it doesnt make sense if they cant
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_type") != "admin":
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function


def create_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("can_create"):
            return render_template('create_profile.html', 
                                show_modal='error',
                                error_message='You do not have permission to create profiles / users.',
                                error_redirect=url_for('home'),
                                error_button_text='Back to Home')
        return f(*args, **kwargs)
    return decorated_function


def modify_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("can_modify"):
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function


def delete_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("can_delete"):
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/password_reset', methods=['GET', 'POST'])
def password_reset():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Check if passwords match
        if password != confirm_password:
            return render_template('password_reset.html', show_modal='passwordMismatch')

        # Check if user exists and is enabled
        user = TraxUser.query.filter_by(username=username, is_enabled=True).first()
        if not user:
            return render_template('password_reset.html', show_modal='userNotFound')

        # Update password
        user.set_password(password)
        db.session.commit()
        return render_template('password_reset.html', show_modal='success',
                                                        success_message='Password updated!',
                                                        success_redirect=url_for('login'),
                                                        success_button_text='Back to Login')

    return render_template('password_reset.html')


@app.route('/home')
def home():
    if not session.get("username"):
        return redirect("/login")

    page = request.args.get('page', 1, type=int)
    per_page = 10
    sort_by = request.args.get('sort_by', 'username')
    filter_status = request.args.get('filter_by', 'all')
    search_query = request.args.get('search', '')
    groups = Group.query.all()

    query = get_filtered_sorted_users(sort_by, filter_status, search_query)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template('home.html',
                         users=pagination.items,
                         pagination=pagination,
                         groups=groups)


# for admin stuff
@app.route('/create_profile', methods=['GET', 'POST'])
@admin_required
@create_required
def create_profile():
    if not session.get("username"):
        return redirect("/login")
        
    if request.method == 'POST':
        try:
            # Get form data and append domain
            username = request.form.get('username') + '@traxtech.com'
            user_type = request.form.get('userType')
            can_view = 'view' in request.form
            can_create = 'create' in request.form
            can_modify = 'modify' in request.form
            is_enabled = request.form.get('status') == 'enabled'

            new_profile = TraxUser(
                username=username, 
                user_type=user_type,
                is_enabled=is_enabled,
                can_view=can_view,
                can_create=can_create,
                can_modify=can_modify
            )

            db.session.add(new_profile)
            db.session.commit()

            # Log the admin action
            log_admin_action(f"CREATED profile for {username}")

            return render_template('create_profile.html', 
                                show_modal='success',
                                success_message='Profile created successfully!',
                                success_redirect=url_for('home'),
                                success_button_text='OK')

        except Exception as e:
            db.session.rollback()
            return render_template('create_profile.html', 
                                show_modal='error',
                                error_message=f'Error creating profile: {str(e)}')

    return render_template('create_profile.html')


# Route to render the manage profiles page
@app.route('/manage_profiles')
@admin_required
@modify_required
def manage_profiles():
    if not session.get("username"):
        return redirect("/login")

    page = request.args.get('page', 1, type=int)
    per_page = 6
    search_query = request.args.get('search', '')

    query = TraxUser.query
    if search_query:
        query = query.filter(TraxUser.username.ilike(f'%{search_query}%'))

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('manage_profiles.html',
                         profiles=pagination.items,
                         pagination=pagination)

# updating profiles
@app.route('/update_profile/<string:username>', methods=['POST'])
@admin_required
@modify_required
def update_profile(username):
    profile = TraxUser.query.get_or_404(username)
    data = request.get_json()
        
    # Update profile attributes
    profile.is_enabled = data.get('is_enabled', profile.is_enabled)
    profile.user_type = data.get('user_type', profile.user_type)
    profile.can_view = data.get('can_view', profile.can_view)
    profile.can_create = data.get('can_create', profile.can_create)
    profile.can_modify = data.get('can_modify', profile.can_modify)
        
    db.session.commit()
        
    # Log the admin action
    action = "DISABLED" if not profile.is_enabled else "UPDATED"
    log_admin_action(f"{action} profile for {username}")
        
    return jsonify({'success': True})

# admin logs component
@app.route('/admin_logs')
@admin_required
def admin_logs():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    search_query = request.args.get('search', '')

    query = AdminLog.query.join(TraxUser, AdminLog.change_made_by == TraxUser.username)

    if search_query:
        query = query.filter(AdminLog.change_done.ilike(f'%{search_query}%'))

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template('admin_logs.html',
                           logs=pagination.items,
                           pagination=pagination)
    
def log_admin_action(change_done):
    admin_log = AdminLog(
        date_time=datetime.now(timezone.utc),
        change_done=change_done,
        change_made_by=session.get("username")
    )
    db.session.add(admin_log)
    db.session.commit()

# manage user component
@app.route('/manage_user/<string:username>', methods=['GET'])
@admin_required
@modify_required
def manage_user(username):
    if not session.get("username"):
        return redirect("/login")

    user = User.query.get_or_404(username)

    # Get latest transfer log
    latest_transfer = XferLog.query.filter_by(username=username)\
        .order_by(XferLog.localtime.desc())\
        .first()

    return render_template('manage_user.html',
                         user=user,
                         latest_transfer=latest_transfer)


def get_filtered_sorted_users(sort_by='username', filter_status='all', search_query=''):
    query = User.query

    # Apply search filter
    if search_query:
        query = query.filter(
            db.or_(
                User.username.ilike(f'%{search_query}%'),
                User.email.ilike(f'%{search_query}%'),
                User.homedir.ilike(f'%{search_query}%')
            )
        )

    # Apply status filter
    if filter_status != 'all':
        now = func.now()
        seven_days_ago = now - timedelta(days=7)
        five_months_ago = now - timedelta(days=150)

        if filter_status == 'active':
            query = query.filter(
                User.enabled == True,
                User.last_accessed.isnot(None),
                User.last_accessed <= seven_days_ago
            )
        elif filter_status == 'inactive':
            query = query.filter(
                User.enabled == True,
                db.or_(
                    User.last_accessed.is_(None),
                    db.and_(
                        User.last_accessed > seven_days_ago,
                        User.last_accessed < five_months_ago
                    )
                )
            )
        elif filter_status == 'disabled':
            query = query.filter(
                db.or_(
                    User.enabled == False,  # Manually disabled
                    User.last_accessed >= five_months_ago
                )
            )

    # Apply sorting
    if sort_by == 'username':
        query = query.order_by(User.username)
    elif sort_by == 'email':
        query = query.order_by(User.email)
    elif sort_by == 'homedir':
        query = query.order_by(User.homedir)

    # Add group filtering
    if filter_status.startswith('group_'):
        try:
            group_id = int(filter_status.split('_')[1])
            query = query.filter(User.gid == group_id)
        except (IndexError, ValueError):
            pass

    return query


# for logout button
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/create_user', methods=['GET', 'POST'])
@admin_required
@create_required
def create_user():
    if request.method == 'POST':
        try:
            uid = int(request.form.get('uid', 1000))
            gid = int(request.form.get('gid', 1000))
            username = request.form.get('username')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            homedir = request.form.get('directory')
            name = request.form.get('name')
            phone = request.form.get('phone')
            email = request.form.get('email')
            enabled = not request.form.get('enabled')  # Checkbox is checked when disabled

            if password != confirm_password:
                return render_template('create_user.html',
                                       show_modal='error',
                                       error_message='Passwords do not match')

            new_user = User(
                uid=uid,
                gid=gid,
                username=username,
                homedir=homedir,
                name=name if name else None,
                phone=phone if phone else None,
                email=email if email else None,
                enabled=enabled,
                shell='/bin/bash', # default place holder
                last_accessed=None
            )
            new_user.set_password(password)

            db.session.add(new_user)
            db.session.commit()
            return render_template('create_user.html',
                                show_modal='success',
                                success_message='User created successfully',
                                success_redirect=url_for('home'),
                                success_button_text='Back to Home')
        except Exception as e:
            db.session.rollback()
            return render_template('create_user.html',
                                show_modal='error',
                                error_message='Error creating user')

    return render_template('create_user.html')


# card component for home.html
@app.route('/api/user_status_counts', methods=['GET'])
def get_user_status_counts():
    try:
        # Use timezone-aware datetime
        now = datetime.now(timezone.utc)
        seven_days_ago = now - timedelta(days=7)
        five_months_ago = now - timedelta(days=150)

        # Active users: enabled and accessed within 7 days
        active_users = User.query.filter(
            User.enabled == True,
            User.last_accessed.isnot(None),
            User.last_accessed >= seven_days_ago
        ).count()

        # Inactive users: enabled and either never accessed or inactive 7-150 days
        inactive_users = User.query.filter(
            User.enabled == True,
            db.or_(
                User.last_accessed.is_(None),
                db.and_(
                    User.last_accessed < seven_days_ago,
                    User.last_accessed >= five_months_ago
                )
            )
        ).count()

        # Disabled users: either manually disabled or inactive > 150 days
        disabled_users = User.query.filter(
            db.or_(
                User.enabled == False,
                db.and_(
                    User.last_accessed.isnot(None),
                    User.last_accessed < five_months_ago
                )
            )
        ).count()

        return jsonify({
            'active_users': active_users,
            'inactive_users': inactive_users,
            'disabled_users': disabled_users
        })

    except Exception as e:
        print(f"Error in status counts: {str(e)}")
        return jsonify({
            'active_users': 0,
            'inactive_users': 0,
            'disabled_users': 0
        }), 500


# for updating user info in manage_user.html w/ hashing is password is changed
@app.route('/update_user', methods=['POST'])
def update_user():
    if not session.get("username"):
        return redirect("/login")

    username = request.form.get('username')
    user = User.query.get_or_404(username)

    try:
        # Update user fields
        user.homedir = request.form.get('homedir')
        user.name = request.form.get('name')
        user.phone = request.form.get('phone')
        user.email = request.form.get('email')

        # Update password if provided
        new_password = request.form.get('password')
        if new_password:
            user.set_password(new_password)

        # Update enabled status
        user.enabled = not request.form.get('enabled')

        db.session.commit()
        return redirect(url_for('home'))

    except Exception as e:
        db.session.rollback()
        print(f"Error updating user: {e}")
        return render_template(
            'manage_user.html',
            user=user,
            show_modal='error',
            error_message='Error updating user')


# for deleting user in manage_user.html
#! NOTE: button is currently disabled but if enabled, the user deletion does not work yet [to be updated]
@app.route('/delete_user/<string:username>', methods=['POST'])
def delete_user(username):
    if not session.get("username"):
        return redirect("/login")

    user = User.query.get_or_404(username)
    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'User deleted successfully',
            'show_modal': 'success'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Error deleting user',
            'show_modal': 'error'
        })


@app.route('/bulk_enable', methods=['POST'])
def bulk_enable():
    users = request.json.get('users', [])
    User.query.filter(User.username.in_(users)).update({User.enabled: True}, synchronize_session=False)
    db.session.commit()
    return jsonify({'success': True})


@app.route('/bulk_disable', methods=['POST'])
def bulk_disable():
    users = request.json.get('users', [])
    User.query.filter(User.username.in_(users)).update({User.enabled: False}, synchronize_session=False)
    db.session.commit()
    return jsonify({'success': True})


#*NOTE: exported data consists of the selected users data based on the db itself (except their passwords)
@app.route('/export_users')
def export_users():
    users = request.args.get('users', '').split(',')
    users_data = User.query.filter(User.username.in_(users)).all()

    output = StringIO()
    writer = csv.writer(output)

    headers = [
        'username',
        'uid',
        'gid',
        'homedir',
        'shell',
        'enabled',
        'name',
        'phone',
        'email',
        'last_accessed'
    ]

    writer.writerow(headers)

    for user in users_data:
        row = [
            user.username,
            user.uid,
            user.gid,
            user.homedir,
            user.shell,
            user.enabled,
            user.name,
            user.phone,
            user.email,
            user.last_accessed.strftime('%Y-%m-%d %H:%M:%S') if user.last_accessed else None
        ]
        writer.writerow(row)

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=users_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'}
    )


@app.route('/import_users', methods=['POST'])
def import_users():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded'})

    try:
        file = request.files['file']
        # Use regular reader instead of DictReader
        reader = csv.reader(TextIOWrapper(file))

        # Skip header row
        next(reader)

        # Password generation function (same as in create_user)
        def generate_password(length=12):
            chars = string.ascii_letters + string.digits + string.punctuation
            return ''.join(random.choice(chars) for _ in range(length))

        for row in reader:
            if not row:  # Skip empty rows
                continue

            # Generate random password
            random_password = generate_password()

            # Map columns by position
            user = User(
                username=row[0],
                uid=int(row[1]) if row[1] else 1000,
                gid=int(row[2]) if row[2] else 1000,
                homedir=row[3] if row[3] else None,
                shell=row[4] if row[4] else None,
                enabled=row[5].lower() == 'true' if row[5] else True,
                name=row[6] if row[6] else None,
                phone=row[7] if row[7] else None,
                email=row[8] if row[8] else None
            )
            user.set_password(random_password)
            db.session.add(user)

            print(f"Generated password for {row[0]}: {random_password}")

        db.session.commit()
        return jsonify({'success': True})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


if __name__ == "__main__":
    app.run(debug=True)
