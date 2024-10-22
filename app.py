from flask import Flask, render_template, url_for, request, redirect, session
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
        
        if username not in users:
            return render_template('login.html', show_modal='user_not_found')
        elif users[username] != password:
            return render_template('login.html', show_modal='incorrect_password')
        else:
            return redirect(url_for('home'))
    
    return render_template('login.html')


@app.route('/password_reset', methods=['GET', 'POST'])
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
    return render_template('home.html')


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


@app.route('/get_users', methods=['GET', 'POST'])
def get_users():
    users = User.query.all() 
    return render_template('user_table.html', users=users) # renders the user table component


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