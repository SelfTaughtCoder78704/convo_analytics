# import smtplib
# from email.mime.text import MIMEText
from flask import Flask, request, render_template, jsonify, redirect, url_for
# from langchain.chains.conversation.memory import ConversationBufferMemory
# from langchain import OpenAI, ConversationChain
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email


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

################ END APP SETUP ###########################################

################ MONGO SETUP ###########################################

conn_str = os.getenv("MONGO_URI")
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


@app.route("/register_form", methods=["GET"])
def display_register_form():
    return render_template("register_form.html")


@app.route("/register", methods=["POST"])
def register():
    # Get the user details from the request
    user_details = request.get_json()
    user_name = user_details.get('username')
    user_email = user_details.get('email')
    user_password = user_details.get('password')
    print(user_name, user_email, user_password)

    # Check if the email is already registered
    if email_already_registered(mongo, user_email):
        return jsonify({'message': 'Email already registered'}), 400
    # Hash the password
    hashed_password = hash_password(user_password)
    # Register the user
    register_user(mongo, user_name, user_email, hashed_password)
    return jsonify({'message': 'User registered successfully'})


# Define a form to handle the login information
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


@app.route("/login_form", methods=["GET"])
def display_login_form():
    form = LoginForm()
    return render_template("login.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    # Get the user details from the form
    user_email = form.email.data
    user_password = form.password.data
    print(user_email, user_password)

    # Check if the email is already registered
    if not email_already_registered(mongo, user_email):
        return render_template('login.html', form=form, message='Email not registered')

        # Check if the password is correct
    if not check_password(user_password, get_password(mongo, user_email)):
        return render_template('login.html', form=form, message='Incorrect password')

    # Return the result of the redirect
    return redirect(url_for('display_dashboard', email=user_email))


@app.route("/dashboard", methods=["GET"])
def display_dashboard():
    email = request.args.get("email")
    my_user = found_user(mongo, email)
    return render_template("dashboard.html", user=my_user)

################ END ROUTES SETUP ###########################################


if __name__ == '__main__':
    app.run(debug=True, PORT=os.getenv("PORT", default=5000))


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
