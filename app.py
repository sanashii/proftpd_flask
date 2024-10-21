from flask import Flask, render_template, url_for, request, redirect

app = Flask(__name__)
app.config['SECRET_KEY'] = 'smiskisecretkey1738dummydingdong'

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

if __name__ == "__main__":
    app.run(debug=True)