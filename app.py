# !/usr/bin/env python
import csv
from io import StringIO, TextIOWrapper
from flask import Flask, Response, jsonify, render_template, url_for, request, redirect, session
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta, timezone
import os
import hashlib
import binascii
import random
import string

from flask_ldap3_login import LDAP3LoginManager
from flask_login import LoginManager, login_user, UserMixin, current_user

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

# LDAP Config
ldap_manager = LDAP3LoginManager(app)
login_manager = LoginManager(app)

app.config['LDAP_HOST'] = 'ldap://dc0100.s03.filex.com'
app.config['LDAP_PORT'] = 389
app.config['LDAP_USE_SSL'] = False
app.config['LDAP_BASE_DN'] = 'dc=filex,dc=com'
app.config['LDAP_USER_DN'] = 'ou=Trax Personnel'
app.config['LDAP_GROUP_DN'] = 'ou=Security Groups'
# app.config['LDAP_USER_RDN_ATTR'] = 'uid'
# app.config['LDAP_USER_LOGIN_ATTR'] = 'mail'
app.config['LDAP_BIND_USER_DN'] = '###'
app.config['LDAP_BIND_USER_PASSWORD'] = '###'

Session(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class TraxUser(db.Model):
    __tablename__ = 'trax_users'
    
    username = db.Column(db.String(50), primary_key=True, nullable=False)
    f_name = db.Column(db.String(50))
    l_name = db.Column(db.String(50))
    login_ldap = db.Column(db.Boolean)
    is_enabled = db.Column(db.Boolean)
    user_type = db.Column(db.String(50))
    password = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        # Generate salt and hash password
        salt = ''.join(random.choice(string.ascii_lowercase) for x in range(2))
        self.password = salt + binascii.hexlify(hashlib.md5((salt + password).encode('utf-8')).digest()).decode('utf-8').upper()

    def check_password(self, password):
        # Verify password
        salt = self.password[:2]
        return self.password == salt + binascii.hexlify(hashlib.md5((salt + password).encode('utf-8')).digest()).decode('utf-8').upper()

class User(db.Model):
    __tablename__ = 'users'
    
    username = db.Column(db.String(128), primary_key=True)
    password = db.Column(db.String(128), nullable=False)
    uid = db.Column(db.Integer)
    gid = db.Column(db.Integer)
    homedir = db.Column(db.String(255))
    shell = db.Column(db.String(255))
    enabled = db.Column(db.Boolean, default=True)
    name = db.Column(db.String(255))
    phone = db.Column(db.String(45))
    email = db.Column(db.String(255))
    last_accessed = db.Column(db.DateTime)

    # Relationships
    login_history = relationship('LoginHistory', backref='user', cascade='all, delete-orphan')
    user_keys = relationship('UserKey', backref='user', cascade='all, delete-orphan')
    xfer_logs = relationship('XferLog', backref='user', cascade='all, delete-orphan')
    
    @property
    def computed_status(self):
        # First check if manually disabled
        if not self.enabled:
            return 'Disabled'
            
        # Check if never accessed
        if self.last_accessed is None:
            return 'Inactive (Never accessed)'
            
        try:
            # Use timezone-aware datetime
            now = datetime.now(timezone.utc)
            if self.last_accessed.tzinfo is None:
                # Make naive datetime timezone-aware
                last_accessed = self.last_accessed.replace(tzinfo=timezone.utc)
            else:
                last_accessed = self.last_accessed
                
            days_inactive = (now - last_accessed).days
            
            if days_inactive > 150:
                return 'Disabled'
            elif days_inactive > 7:
                return f'Inactive ({days_inactive} days)'
            else:
                return 'Active'
        except Exception as e:
            print(f"Error calculating status: {e}")
            return 'Inactive (Error calculating days)'
        
    def set_password(self, password):
        salt = ''.join(random.choice(string.ascii_lowercase) for x in range(2))
        self.password = salt + binascii.hexlify(hashlib.md5((salt + password).encode('utf-8')).digest()).decode('utf-8').upper()

    def check_password(self, password):
        salt = self.password[:2]
        return self.password == salt + binascii.hexlify(hashlib.md5((salt + password).encode('utf-8')).digest()).decode('utf-8').upper()

class Group(db.Model):
    __tablename__ = 'groups'
    
    groupname = db.Column(db.String(128), primary_key=True)
    gid = db.Column(db.Integer, nullable=False)
    members = db.Column(db.Text)

class HostKey(db.Model):
    __tablename__ = 'host_keys'
    
    host = db.Column(db.String(255), primary_key=True)
    public_key = db.Column(db.Text, nullable=False)

class LoginHistory(db.Model):
    __tablename__ = 'login_history'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(128), db.ForeignKey('users.username', ondelete='CASCADE', onupdate='CASCADE'))
    client_ip = db.Column(db.String(128), nullable=False)
    server_ip = db.Column(db.String(128), nullable=False)
    protocol = db.Column(db.String(8), nullable=False)
    ts = db.Column(db.DateTime)

class UserKey(db.Model):
    __tablename__ = 'user_keys'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(128), db.ForeignKey('users.username', ondelete='CASCADE', onupdate='CASCADE'))
    public_key = db.Column(db.Text, nullable=False)

class XferLog(db.Model):
    __tablename__ = 'xferlog'
    
    # Remove id field since it doesn't exist in database
    username = db.Column(db.String(128), db.ForeignKey('users.username', ondelete='CASCADE', onupdate='CASCADE'))
    filename = db.Column(db.Text)
    size = db.Column(db.BigInteger)
    host = db.Column(db.Text)
    address = db.Column(db.String(128))
    action = db.Column(db.Text)
    duration = db.Column(db.Text)
    localtime = db.Column(db.DateTime)
    success = db.Column(db.Text)

    __mapper_args__ = {
        'primary_key': [username, localtime]  # Using composite key
    }

# try:
#     with app.app_context():
#         db.engine.connect()
#         print("Database connection successful!")
# except Exception as e:
#     print(f"Error connecting to database: {e}")

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
        password = request.form.get("password")

        # Check if user exists and is enabled in trax_users table
        user = TraxUser.query.filter_by(username=username, is_enabled=True).first()
        if not user:
            return render_template('login.html', show_modal='error',
                                                    error_message='Account does not exist. Please contact your administrator.')

        # Check password
        if user.check_password(password):
            session["username"] = username
            return redirect(url_for('home'))

        # LDAP authentication (for future)
        if user.login_ldap:
            result = ldap_manager.authenticate(username, password)
            if result.status:
                login_user(result.user)
                return redirect(url_for('home'))
            else:
                return render_template('login.html', show_modal='no_access_to_filex')

        return render_template('login.html', show_modal='error',
                                            error_message='Incorrect password. Please try again.')

    return render_template('login.html')


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


# manage user component
@app.route('/manage_user/<string:username>', methods=['GET'])
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
        return render_template('manage_user.html',
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
