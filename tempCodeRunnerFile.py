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
    # Clear any existing session data
    session.clear()

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # LDAP login for domain users
        if '@traxtech.com' in username:
            result = ldap_manager.authenticate(username, password)
            if result.status:
                login_user(result.user)
                return redirect(url_for('home'))
        #* TEMP ONLY: Local admin fallback
        elif username == "admin" and password == "admin":
            session["username"] = "admin"
            return redirect(url_for('home'))
            
        return render_template('login.html', show_modal='incorrect_password')
        
    return render_template('login.html')