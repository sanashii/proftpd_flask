from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'smiskisecretkey1738dummydingdong'

db = SQLAlchemy(app)
users = {"admin": "admin"} # dummy acc

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

@app.route('/create_user', methods=['POST'])
def create_user():
    new_user = User(username='johndoe', password='securepassword', directory='/mnt/ftp/test', status='Active')
    db.session.add(new_user)
    db.session.commit()
    return render_template('create_user.html', show_modal='') #! not working yet

# Define your User model
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