from flask import Flask, render_template, url_for

app = Flask(__name__)

@app.route('/') # default login route
def login():
    return render_template('login.html')

@app.route('/home') # home route
def home():
    return render_template('home.html')

if __name__ == "__main__":
    app.run(debug=True)
    