#!/usr/bin/env python
from flask import Flask, jsonify, render_template, url_for, request, redirect, session
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy.sql import func
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+mysqldb://proftpd_stage:###@FXCEBFS0304?charset=utf8"
app.config['SECRET_KEY'] = '###'

# Session(app)
db = SQLAlchemy(app)
users = {"admin": "admin"} # dummy acc for admin -- in actuality, ppl with the @traxtech.com domain can access this [to implement: LDAP]

migrate = Migrate(app, db)

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


@app.route('/home', methods=['GET'])
def home():
    if not session.get("username"):
        return redirect("/login")

    # Get all parameters
    page = request.args.get('page', 1, type=int)
    per_page = 10
    sort_by = request.args.get('sort_by', 'id')
    filter_status = request.args.get('filter_by', 'all')
    search_query = request.args.get('search', '')

    # Get filtered and sorted query
    query = get_filtered_sorted_users(sort_by, filter_status, search_query)

    # Apply pagination to the query
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template('user_table.html',
                            users=pagination.items,
                            pagination=pagination)

    return render_template('home.html',
                         users=pagination.items,
                         pagination=pagination)

# manage user component
@app.route('/manage_user/<int:user_id>', methods=['GET'])
def manage_user(user_id):
    if not session.get("username"):
        return redirect("/login")

    user = User.query.get_or_404(user_id)
    return render_template('manage_user.html', user=user)

def get_filtered_sorted_users(sort_by='id', filter_status='all', search_query=''):
    query = User.query

    seven_days_ago = func.now() - timedelta(days=7)

    if filter_status == 'active':
        query = query.filter(
            User.status != 'Disabled',
            User.last_login >= seven_days_ago
        )
    elif filter_status == 'inactive':
        query = query.filter(
            User.status != 'Disabled',
            db.or_(
                User.last_login < seven_days_ago,
                User.last_login == None
            )
        )
    elif filter_status == 'all':
        query = query.filter(User.status.in_(['Active', 'Inactive', 'Disabled']))


    if sort_by == 'username':
        query = query.order_by(User.username)
    elif sort_by == 'id':
        query = query.order_by(User.id)
    elif sort_by == 'directory':
        query = query.order_by(User.directory)

    if search_query:
        query = query.filter(User.username.like(f'%{search_query}%'))  # case insensitive search

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
# In app.py, update the route
@app.route('/api/user_status_counts', methods=['GET'])
def get_user_status_counts():
    seven_days_ago = func.now() - timedelta(days=7)

    active_users = User.query.filter(
        User.status != 'Disabled',
        User.last_login >= seven_days_ago
    ).count()

    inactive_users = User.query.filter(
        User.status != 'Disabled',
        db.or_(
            User.last_login < seven_days_ago,
            User.last_login == None
        )
    ).count()

    disabled_users = User.query.filter_by(status='Disabled').count()

    return jsonify({
        'active_users': active_users,
        'inactive_users': inactive_users,
        'disabled_users': disabled_users
    })

# for updating user info in manage_user.html
@app.route('/update_user', methods=['POST'])
def update_user():
    if not session.get("username"):
        return redirect("/login")

    user_id = request.form.get('user_id')
    user = User.query.get_or_404(user_id)

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
@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if not session.get("username"):
        return redirect("/login")

    user = User.query.get_or_404(user_id)
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

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    password = db.Column(db.String(120), nullable=False)
    directory = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(10), nullable=False)

    # Existing fields
    login_count = db.Column(db.Integer, default=0)
    last_login = db.Column(db.DateTime, nullable=True)
    last_modified = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    bytes_uploaded = db.Column(db.BigInteger, default=0)
    bytes_downloaded = db.Column(db.BigInteger, default=0)
    files_uploaded = db.Column(db.Integer, default=0)
    files_downloaded = db.Column(db.Integer, default=0)

    @property
    def computed_status(self):
        if self.status == 'Disabled':
            return 'Disabled'

        if self.last_login is None:
            return 'Inactive'

        seven_days_ago = func.now() - timedelta(days=7)
        return 'Inactive' if self.last_login < seven_days_ago else 'Active'



if __name__ == "__main__":
    app.run(debug=True)
