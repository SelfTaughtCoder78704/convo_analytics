# import smtplib
# from email.mime.text import MIMEText
from datetime import timedelta
from flask import Flask, request, render_template, jsonify, redirect, url_for, session
# from langchain.chains.conversation.memory import ConversationBufferMemory
# from langchain import OpenAI, ConversationChain
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email
from flask_wtf.csrf import CSRFProtect

from helpers import (
    register_user,
    hash_password,
    check_password,
    found_user,
    get_password,
    email_already_registered
)


import os
import pymongo
from dotenv import load_dotenv
load_dotenv()

################ APP SETUP ###########################################

app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = 'secret-key'
csrf = CSRFProtect(app)

################ END APP SETUP ###########################################

################ MONGO SETUP ###########################################

conn_str = os.getenv("MONGO_URL")
# set a 5-second connection timeout
client = pymongo.MongoClient(conn_str, serverSelectionTimeoutMS=5000)

try:
    print(client.server_info())
except Exception:
    print("Unable to connect to the server.")

mongo = client.get_database('eventbot')

################ END MONGO SETUP #######################################

################ ROUTES SETUP ###########################################


@app.route("/")
def hello_world():
    return render_template('index.html')


################ LOGIN/LOGOUT ROUTES AND FORM ###########################################

# Define a form to handle the login information


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')
    csrfToken = StringField('csrfToken')


@app.route("/login_form", methods=["GET"])
def display_login_form():
    form = LoginForm()
    return render_template("login.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user_email = form.email.data
        user_password = form.password.data
        if not found_user(mongo, user_email):
            return redirect(url_for('display_register_form', message='Email not registered'))
        if not email_already_registered(mongo, user_email):
            return render_template('login.html', form=form, message='Email not registered')

        if not check_password(user_password, get_password(mongo, user_email)):
            return render_template('login.html', form=form, message='Incorrect password')

        # Create a session for the user
        session.permanent = True
        app.permanent_session_lifetime = timedelta(minutes=30)
        session['email'] = user_email

        return redirect(url_for('display_dashboard'))

    return render_template('login.html', form=form)


@app.route("/logout", methods=["GET"])
def logout():
    session.clear()
    return redirect(url_for("display_login_form"))

################ END LOGIN/LOGOUT  ROUTES AND FORM ###########################################

################ REGISTER ROUTES ###########################################

# Define a form to handle the registration information


class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Register')
    csrfToken = StringField('csrfToken')


@app.route("/register_form", methods=["GET"])
def display_register_form():
    form = RegisterForm()
    message = request.args.get('message') or ''
    return render_template("register_form.html", message=message, form=form)


@app.route("/register", methods=["POST"])
def register():
    # Get the user details from the request
    # user_details = request.get_json()
    # user_name = user_details.get('username')
    # user_email = user_details.get('email')
    # user_password = user_details.get('password')
    # print(user_name, user_email, user_password)

    # # Check if the email is already registered
    # if email_already_registered(mongo, user_email):
    #     return jsonify({'message': 'Email already registered'}), 400
    # # Hash the password
    # hashed_password = hash_password(user_password)
    # # Register the user
    # register_user(mongo, user_name, user_email, hashed_password)
    # return render_template('register_form.html', message='User registered successfully')

    form = RegisterForm()
    if form.validate_on_submit():
        user_name = form.username.data
        user_email = form.email.data
        user_password = form.password.data
        if email_already_registered(mongo, user_email):
            return render_template('register_form.html', form=form, message='Email already registered')
        hashed_password = hash_password(user_password)
        register_user(mongo, user_name, user_email, hashed_password)
        return redirect(url_for('display_login_form'))
    return render_template('register_form.html', form=form)


################ END REGISTER ROUTES ###########################################

################ DASHBOARD ROUTE ###########################################


@app.route("/dashboard", methods=["GET"])
def display_dashboard():
    # Get the email from the session
    email = session.get("email")
    if not email:
        return redirect(url_for("display_login_form"))

    my_user = found_user(mongo, email)
    return render_template('dashboard.html', email=email, user=my_user)

################ END DASHBOARD ROUTE ###########################################


################ END ROUTES SETUP ###########################################

# llm = OpenAI(temperature=0)
# conversation = ConversationChain(
#     llm=llm,
#     verbose=True,
#     memory=ConversationBufferMemory()
# )

# first_input = "Hi there! You are EventBot. Frontend events are sent to you and you will document them in a friendly human readable way."
# convo = conversation.predict(input=first_input)


# @app.route("/summary", methods=["POST"])
# def summary():
#     data = request.get_json()
#     events = data.get("events", [])
#     prompt = "Please summarize the events that occurred in a conversational way. The events were: " + \
#         str(events) + ". Match hovering and clicking events with the corresponding elements. Make the summary in list fashion."
#     summary = conversation.predict(input=prompt)

#     # Send the email with the summary
#     sender = 'bobbynicholson78704@gmail.com'
#     recipient = data.get("email")
#     password = os.getenv("EMAIL_PASSWORD")
#     subject = "Summary of Frontend Events"
#     text = summary

#     msg = MIMEText(text)
#     msg['Subject'] = subject
#     msg['From'] = sender
#     msg['To'] = recipient

#     server = smtplib.SMTP('smtp.gmail.com', 587)
#     server.starttls()
#     server.login(sender, password)
#     server.sendmail(sender, recipient, msg.as_string())
#     server.quit()

#     return jsonify({'summary': summary})

if __name__ == '__main__':
    app.run(debug=True, PORT=os.getenv("PORT", default=5000))
