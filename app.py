# !/usr/bin/env python
from flask import Flask, jsonify, render_template, url_for, request, redirect, session
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

# LDAP Config
# ldap_manager = LDAP3LoginManager(app)
# login_manager = LoginManager(app)

# app.config['LDAP_HOST'] = 'ldap://your-ldap-server'
# app.config['LDAP_PORT'] = 389
# app.config['LDAP_USE_SSL'] = False
# app.config['LDAP_BASE_DN'] = 'dc=traxtech,dc=com'
# app.config['LDAP_USER_DN'] = 'ou=users'
# app.config['LDAP_GROUP_DN'] = 'ou=groups'
# app.config['LDAP_USER_RDN_ATTR'] = 'uid'
# app.config['LDAP_USER_LOGIN_ATTR'] = 'mail'
# app.config['LDAP_BIND_USER_DN'] = None
# app.config['LDAP_BIND_USER_PASSWORD'] = None

# Session(app)
db = SQLAlchemy(app)
users = {"admin": "admin"} # dummy acc for admin -- in actuality, ppl with the @traxtech.com domain can access this [to implement: LDAP]

migrate = Migrate(app, db)

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

# @login_manager.user_loader
# def load_user(id):
#     return User.query.get(id)

# @ldap_manager.save_user
# def save_user(dn, username, data, memberships):
#     user = User.query.filter_by(username=username).first()
#     if not user:
#         user = User(
#             username=username,
#             email=data.get('mail', [None])[0],
#             name=data.get('displayName', [None])[0]
#         )
#         db.session.add(user)
#         db.session.commit()
#     return user

@app.route('/', methods=['GET', 'POST'])
def login():
    # Clear any existing session data
    session.clear()

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # # LDAP login for domain users
        # if '@traxtech.com' in username:
        #     result = ldap_manager.authenticate(username, password)
        #     if result.status:
        #         login_user(result.user)
        #         return redirect(url_for('home'))
        #* TEMP ONLY: Local admin fallback
        if username == "admin" and password == "admin": #elif
            session["username"] = "admin"
            return redirect(url_for('home'))
            
        return render_template('login.html', show_modal='incorrect_password')
        
    return render_template('login.html')


@app.route('/password_reset', methods=['GET', 'POST']) #! NOTE: to be updated / changed when using the actual trax domain
def password_reset():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if username not in users:
            return render_template('password_reset.html', show_modal='user_not_found')
        elif password != confirm_password:
            return render_template('password_reset.html', show_modal='error', error_message='Passwords do not match')
        else:
            users[username] = password
            return render_template('password_reset.html',
                                   show_modal='success',
                                   success_message='Your password has been successfully reset.',
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
    
    query = get_filtered_sorted_users(sort_by, filter_status, search_query)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # # Check if it's an AJAX request
    # if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
    #     # Return only the table content
    #     return render_template('components/user_table.html',
    #                          users=pagination.items,
    #                          pagination=pagination)

    #! CURRENT ISSUE: sorting & filtering works but after about 3 seconds, the doubling nav bar  issue resurfaces and only disappears on refresh
    return render_template('home.html',
                         users=pagination.items,
                         pagination=pagination)


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

if __name__ == "__main__":
    app.run(debug=True)
