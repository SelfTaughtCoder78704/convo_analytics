from datetime import timedelta
from flask import Blueprint, redirect, render_template, session, url_for, current_app
from forms import LoginForm, RegisterForm, ClientSiteForm
from helpers import check_password, found_user, get_password, hash_password, email_already_registered, register_user

routes_bp = Blueprint('routes', __name__)


@ routes_bp.route("/")
def hello_world():
    return render_template('index.html')


@ routes_bp.route("/login", methods=["GET", "POST"])
def login():
    mongo = current_app.config.get('MONGO')
    form = LoginForm()

    if form.validate_on_submit():
        user_email = form.email.data
        user_password = form.password.data

        if not found_user(mongo, user_email):
            return render_template('login.html', form=form, message='Email not registered')

        if not check_password(user_password, get_password(mongo, user_email)):
            return render_template('login.html', form=form, message='Incorrect password')

        session.permanent = True
        current_app.permanent_session_lifetime = timedelta(minutes=30)
        session['email'] = user_email

        return redirect(url_for('routes.display_dashboard'))

    return render_template('login.html', form=form)


@ routes_bp.route("/logout", methods=["GET"])
def logout():
    session.clear()
    return redirect(url_for("routes.login"))


@ routes_bp.route("/register", methods=["GET", "POST"])
def register():
    mongo = current_app.config.get('MONGO')
    form = RegisterForm()

    if form.validate_on_submit():
        user_name = form.username.data
        user_email = form.email.data
        user_password = form.password.data

        if email_already_registered(mongo, user_email):
            return render_template('register.html', form=form, message='Email already registered')

        hashed_password = hash_password(user_password)
        register_user(mongo, user_name, user_email, hashed_password)
        return redirect(url_for('routes.login'))

    return render_template('register.html', form=form)


@ routes_bp.route("/dashboard", methods=["GET", "POST"])
def display_dashboard():
    mongo = current_app.config.get('MONGO')
    # Check if the user is logged in
    if not session.get("email"):
        return redirect(url_for("routes.display_login_form"))

    client_form = ClientSiteForm()
    if client_form.validate_on_submit():
        client_site = client_form.client_site.data
        user = found_user(mongo, session['email'])
        mongo.db.client_sites.insert_one(
            {'user': user['_id'], 'url': client_site})
        return redirect(url_for('routes.display_dashboard'))

    email = session['email']
    my_user = found_user(mongo, session['email'])
    my_client_sites = mongo.db.client_sites.find({'user': my_user['_id']})
    return render_template('dashboard.html', email=email, user=my_user, form=client_form, sites=my_client_sites)
