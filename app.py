from flask import Flask, jsonify, render_template, url_for, request, redirect, session
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy.sql import func
import os

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'smiskisecretkey1738dummydingdong'

Session(app)
db = SQLAlchemy(app)
users = {"admin": "admin"} # dummy acc for admin -- in actuality, ppl with the @traxtech.com domain can access this

migrate = Migrate(app, db)

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        session["username"] = request.form.get("username")
        
        if username not in users:
            return render_template('login.html', show_modal='user_not_found')
        elif users[username] != password:
            return render_template('login.html', show_modal='incorrect_password')
        else:
            return redirect(url_for('home'))
    
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


@app.route('/home', methods=['GET'])
def home():
    if not session.get("username"):
        return redirect("/login")
    
    sort_by = request.args.get('sort_by', 'id')
    filter_status = request.args.get('filter_by', 'all')
    search_query = request.args.get('search', '')

    users = get_filtered_sorted_users(sort_by, filter_status, search_query)
    return render_template('index.html', users=users, content_template='home.html')

def get_filtered_sorted_users(sort_by='id', filter_status='all', search_query=''):
    query = User.query

    if filter_status == 'active':
        query = query.filter_by(status='Active')
    elif filter_status == 'inactive':
        query = query.filter(User.status.in_(['Inactive', 'Disabled']))
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

    return query.all()

# for logout button
@app.route('/logout')
def logout():
    session.clear()
    return redirect("/login")

# sample data
@app.route('/populate_test_data')
def populate_test_data():
    user4 = User(id=105483, username='user111', password='user111', directory='/mnt/ftp/test1', status='Inactive')
    user5 = User(id=119003, username='name1234', password='name1234', directory='/mnt/ftp/test2', status='Inactive')
    user6 = User(id=101223, username='user85', password='user85', directory='/mnt/ftp/test7', status='Disabled')
    
    db.session.add_all([user4, user5, user6])
    db.session.commit()
    
    return 'Test users added to database!'


@app.route('/create_user', methods=['POST'])
def create_user():
    new_user = User(username='johndoe', password='securepassword', directory='/mnt/ftp/test', status='Active') # TODO: will be filled and passed through the inputs sa frontend
    
    db.session.add(new_user)
    db.session.commit()
    return render_template('create_user.html', show_modal=' ') #TODO: not working yet

# card component for home.html
@app.route('/api/user_status_counts', methods=['GET'])
def get_user_status_counts():
    active_users_count = User.query.filter_by(status='Active').count()
    inactive_users_count = User.query.filter(User.status.in_(['Inactive'])).count()
    disabled_users_count = User.query.filter_by(status='Disabled').count()

    return jsonify({
        'active_users': active_users_count,
        'inactive_users': inactive_users_count,
        'disabled_users': disabled_users_count
    })

# manage user component
@app.route('/manage_user/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('index.html', user=user, content_template='manage_user.html')


# for updating user info in manage_user.html
@app.route('/update_user', methods=['POST'])
def update_user():
    user_id = request.form['user_id']
    user = User.query.get_or_404(user_id)
    
    user.username = request.form['username']
    user.directory = request.form['directory']
    user.status = request.form['status']
    
    db.session.commit()
    return redirect(url_for('home'))


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    password = db.Column(db.String(120), nullable=False)
    directory = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(10), nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

# Run this once to initialize the database
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)