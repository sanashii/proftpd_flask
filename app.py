# !/usr/bin/env python
from flask import Flask, jsonify, render_template, url_for, request, redirect, session
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
# app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+mysqlconnector://proftpd_stage:C{7#iUoNc82@FXCEBFS0304?charset=utf8"
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+mysqlconnector://proftpd_stage:C{7#iUoNc82@FXCEBFS0304/proftpd?charset=utf8"
app.config['SECRET_KEY'] = 'smiskisecretkey1738dummydingdong'

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
        if not self.enabled:
            return 'Disabled'
            
        if not self.last_accessed:
            return 'Inactive (Never accessed)'
            
        days_inactive = (func.now() - self.last_accessed).days
        
        if days_inactive >= 150:  # ~5 months
            return 'Disabled'
        elif days_inactive > 7:
            return f'Inactive ({days_inactive} days)'
        else:
            return 'Active'

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
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(128), db.ForeignKey('users.username', ondelete='CASCADE', onupdate='CASCADE'))
    filename = db.Column(db.Text)
    size = db.Column(db.BigInteger)
    host = db.Column(db.Text)
    address = db.Column(db.String(128))
    action = db.Column(db.Text)
    duration = db.Column(db.Text)
    localtime = db.Column(db.DateTime)
    success = db.Column(db.Text)


try:
    with app.app_context():
        db.engine.connect()
        print("Database connection successful!")
except Exception as e:
    print(f"Error connecting to database: {e}")

@app.route('/', methods=['GET', 'POST'])
def login():
    # Clear any existing session data
    session.clear()

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == "admin" and password == "admin":
            session["username"] = "admin"
            return redirect(url_for('home'))
        return render_template("login.html", show_modal='incorrect_password')

    return render_template("login.html")


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
    
    # Get base query
    query = get_filtered_sorted_users(sort_by, filter_status, search_query)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template('user_table.html',
                                users=pagination.items,
                                pagination=pagination)

    return render_template('home.html',
                            users=pagination.items,
                            pagination=pagination)


# manage user component
@app.route('/manage_user/<string:username>', methods=['GET'])
def manage_user(username):
    if not session.get("username"):
        return redirect("/login")

    user = User.query.get_or_404(username)
    return render_template('manage_user.html', user=user)

# app.py
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
        if filter_status == 'active':
            # Active: last accessed within 7 days and enabled
            seven_days_ago = now - timedelta(days=7)
            query = query.filter(
                User.enabled == True,
                User.last_accessed >= seven_days_ago
            )
        elif filter_status == 'inactive':
            # Inactive: last accessed > 7 days ago but < 150 days and enabled
            seven_days_ago = now - timedelta(days=7)
            five_months_ago = now - timedelta(days=150)
            query = query.filter(
                User.enabled == True,
                db.or_(
                    User.last_accessed.between(five_months_ago, seven_days_ago),
                    User.last_accessed == None
                )
            )
        elif filter_status == 'disabled':
            # Disabled: either explicitly disabled or inactive > 150 days
            five_months_ago = now - timedelta(days=150)
            query = query.filter(
                db.or_(
                    User.enabled == False,
                    User.last_accessed < five_months_ago
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
            new_user = User(
                username=request.form.get('username'),
                password=request.form.get('password'),
                directory=request.form.get('directory'),
                status=request.form.get('status'),
                login_count=0,
                bytes_uploaded=0,
                bytes_downloaded=0,
                files_uploaded=0,
                files_downloaded=0
                # last_modified will be set automatically
            )
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
        now = func.now()
        seven_days_ago = now - timedelta(days=7)
        five_months_ago = now - timedelta(days=150)

        # Active users: enabled and accessed within 7 days
        active_users = User.query.filter(
            User.enabled == True,
            User.last_accessed >= seven_days_ago
        ).count()

        # Inactive users: enabled but not accessed for > 7 days but < 150 days
        inactive_users = User.query.filter(
            User.enabled == True,
            db.or_(
                User.last_accessed.between(five_months_ago, seven_days_ago),
                User.last_accessed == None
            )
        ).count()

        # Disabled users: either explicitly disabled or inactive > 150 days
        disabled_users = User.query.filter(
            db.or_(
                User.enabled == False,
                User.last_accessed < five_months_ago
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

# for updating user info in manage_user.html
@app.route('/update_user', methods=['POST'])
def update_user():
    if not session.get("username"):
        return redirect("/login")

    username = request.form.get('username')
    user = User.query.get_or_404(username)

    user.username = request.form.get('username')
    user.directory = request.form.get('directory')

    # Status switch handling
    if 'status_switch' in request.form:
        user.status = 'Disabled'
    else:
        user.status = 'Active'

    # Password update
    new_password = request.form.get('password')
    if new_password and new_password.strip():
        user.password = new_password

    # last_modified will update automatically due to onupdate
    try:
        db.session.commit()
        return redirect(url_for('home'))
    except Exception as e:
        db.session.rollback()
        return redirect(url_for('manage_user', user_id=user_id))

# for deleting user in manage_user.html
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
