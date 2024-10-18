from flask import Flask, render_template, url_for, request, flash, redirect

app = Flask(__name__)
app.config['SECRET_KEY'] = 'smiskisecretkey1738dummydingdong'

users = {"admin": "admin"} # dummy acc

@app.route('/', methods=['GET', 'POST']) # default login route
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in users and users[username] == password:
            flash(f'Welcome, {username}!', 'success')
            return render_template('home.html')
        else:
            # Login failed
            flash('Invalid username or password', 'danger')
    
    # Render the login page
    return render_template('login.html')

@app.route('/password_reset', methods=['GET', 'POST']) # default login route
def password_reset():
    return render_template('password_reset.html') 

@app.route('/home') # home route
def home():
    return render_template('home.html')


if __name__ == "__main__":
    app.run(debug=True)
    