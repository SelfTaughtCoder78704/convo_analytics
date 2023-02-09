# import smtplib
# from email.mime.text import MIMEText
from flask_cors import CORS, cross_origin
from datetime import timedelta
from bson import ObjectId
from flask import Flask, Response, make_response, request, render_template, jsonify, redirect, url_for, session
# from langchain.chains.conversation.memory import ConversationBufferMemory
# from langchain import OpenAI, ConversationChain
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectMultipleField
from wtforms.validators import DataRequired, Email
from flask_wtf.csrf import CSRFProtect

from helpers import (
    register_user,
    hash_password,
    check_password,
    found_user,
    get_password,
    email_already_registered,
    allow_cors
)


import os
import pymongo
from dotenv import load_dotenv
load_dotenv()


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


################ APP SETUP ###########################################

app = Flask(__name__, template_folder='templates')
################ CORS SETUP #################

approved_sites = [doc['client_site'] for doc in mongo.db.client_sites.find()]

server_site = os.getenv('https://web-staging-staging.up.railway.app')

approved_sites.append(server_site)

cors = CORS(app, resources={r"/*": {"origins": approved_sites}},
            attach_to_all=False, automatic_options=False)


def allow_cors(response):
    origin = request.headers.get('Origin', '')
    if origin in approved_sites:
        response.headers['Access-Control-Allow-Origin'] = origin
    else:
        return make_response("Unauthorized", 401)
    return response


app.after_request(allow_cors)


################ END CORS SETUP #################

app.config['SECRET_KEY'] = 'secret-key'
csrf = CSRFProtect(app)
# allow CORS
cors = CORS(app, resources={r"/*": {"origins": "*"}},
            attach_to_all=False, automatic_options=False)
################ END APP SETUP ###########################################


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

# form for setting client site url
class ClientSiteForm(FlaskForm):
    client_site = StringField('Client Site', validators=[DataRequired()])
    submit = SubmitField('Submit')
    csrfToken = StringField('csrfToken')


@app.route("/dashboard", methods=["GET"])
def display_dashboard():
    # Check if the user is logged in
    if not session.get("email"):
        return redirect(url_for("display_login_form"))

    client_form = ClientSiteForm()

    email = session['email']

    my_user = found_user(mongo, session['email'])
    my_client_sites = mongo.db.client_sites.find({'user': my_user['_id']})
    return render_template('dashboard.html', email=email, user=my_user, form=client_form, sites=my_client_sites)

################ END DASHBOARD ROUTE ###########################################

################ CLIENT ADDS SITE ROUTE ###############


@app.route("/set_site", methods=['POST'])
def set_site():
    client_form = ClientSiteForm()
    my_user = found_user(mongo, session['email'])
    user_sites = mongo.db.client_sites.find({'user': my_user['_id']})
    if client_form.validate_on_submit():
        client_site = client_form.client_site.data

        # check if the user has reached their limit of 1 site on FREE account_type
        if len(my_user['client_sites']) >= 1 and my_user['account_type'] == 'FREE':
            # redirect to dashboard with message

            return render_template('dashboard.html', form=client_form, sites=user_sites, message='You have reached your limit of 1 site on FREE plan', user=my_user)

        # create a mew collection for the client_sites add the client site to the collection and link it to the user
        mongo.db.client_sites.insert_one(
            {'client_site': client_site,
                'user': my_user['_id'], 'elements': []}
        )

        # add the client site to the user and increment the usage
        mongo.db.users.update_one(
            {'_id': my_user['_id']},
            {'$push': {'client_sites': client_site}}
        )

        return redirect(url_for('display_dashboard'))
    return render_template('dashboard.html', form=client_form, sites=user_sites, user=my_user)


################ END CLIENT ADDS SITE ROUTE ############

################ VIEW SINGLE SITE ROUTE ############

# form for adding elements

class AddElementForm(FlaskForm):
    elements = SelectMultipleField('Elements', choices=[(
        'button', 'Buttons'), ('a', 'Links'), ('img', 'Images'), ('form', 'Forms')])
    submit = SubmitField('Submit')
    csrfToken = StringField('csrfToken')

# form for editing site name


class EditSiteForm(FlaskForm):
    client_site = StringField('Client Site', validators=[DataRequired()])
    submit = SubmitField('Submit')
    csrfToken = StringField('csrfToken')


@app.route("/site/<site_id>", methods=['GET'])
def view_site(site_id):
    element_form = AddElementForm()
    edit_site_form = EditSiteForm()
    # Check if the user is logged in
    if not session.get("email"):
        return redirect(url_for("display_login_form"))

    my_user = found_user(mongo, session['email'])
    my_client_site = mongo.db.client_sites.find_one({'_id': ObjectId(site_id)})
    my_page_data = list(mongo.db.page_data.find(
        {'site_id': site_id}))
    if not my_page_data:
        my_page_data = []

    print(my_page_data)

    return render_template('site.html', user=my_user, site=my_client_site, events=my_page_data, form=element_form, edit=edit_site_form)

################ END VIEW SINGLE SITE ROUTE ############

################ EDIT SITE NAME ROUTE ############


@app.route("/site/edit_site/<site_id>", methods=['POST'])
def edit_site(site_id):
    edit_site_form = EditSiteForm()
    my_user = found_user(mongo, session['email'])
    my_client_site = mongo.db.client_sites.find_one({'_id': ObjectId(site_id)})

    if edit_site_form.validate_on_submit():
        client_site = edit_site_form.client_site.data

        # update the client site name
        mongo.db.client_sites.update_one(
            {'_id': ObjectId(site_id)},
            {'$set': {'client_site': client_site}}
        )

        # update the client site name in the user
        # the user looks like this: {
        #   "name": "user_one",
        #   "email": "user@here.com",
        #   "password": "$2b$12$PTNkAR8GPZA/1aSorZXNge/YOg2T./U.OwXMGnO5OeTF9s96fbcue",
        #   "account_type": "FREE",
        #   "client_sites": [
        #       "client_site_one",
        #   ]
        # }
        mongo.db.users.update_one(
            {'_id': my_user['_id']},
            {'$set': {'client_sites.$[elem]': client_site}},
            array_filters=[{'elem': my_client_site['client_site']}]


        )

        return redirect(url_for('view_site', site_id=site_id))
    return render_template('site.html', user=my_user, site=my_client_site, edit=edit_site_form)

################ END EDIT SITE NAME ROUTE ############


################ ADD ELEMENTS TO SITE ROUTE ############


@app.route("/site/set_elements/<site_id>", methods=['POST'])
def set_elements(site_id):
    element_form = AddElementForm()
    my_user = found_user(mongo, session['email'])
    my_client_site = mongo.db.client_sites.find_one({'_id': ObjectId(site_id)})
    my_client_site_events = mongo.db.client_site_events.find(
        {'client_site': my_client_site['client_site']})
    if element_form.validate_on_submit():
        elements = element_form.elements.data

        # add the elements to the client site
        mongo.db.client_sites.update_one(
            {'_id': ObjectId(site_id)},
            # OVERWRITE THE WHOLE ARRAY
            {'$set': {'elements': elements}}
        )

        return redirect(url_for('view_site', site_id=site_id))
    return render_template('site.html', user=my_user, site=my_client_site, events=my_client_site_events, form=element_form)

################ END ADD ELEMENTS TO SITE ROUTE ############

################ GENERATE SCRIPT ROUTE ############


@app.route("/site/generate_script/<site_id>", methods=['GET'])
def generate_script(site_id):

    my_client_site = mongo.db.client_sites.find_one({'_id': ObjectId(site_id)})

    # get the elements from the client site
    elements = my_client_site['elements']
    # generate a javascript script with query selectors for the elements
    script = f"""
    let events = []
    let timeLoaded;
    window.onbeforeunload = function() {{
        let timeLeft = new Date()
        let timeSpent = timeLeft - timeLoaded
        fetch('https://web-staging-staging.up.railway.app/summary', {{
            method: 'POST',
            headers: {{
                'Content-Type': 'application/json',
                'site_id': '{site_id}',
                'client_id': '{my_client_site['user']}'
            }},
            body: JSON.stringify(events)
        }}).then(res => res.json())
        .then(data => console.log(data))
        .catch(err => console.log(err))
    }}
    const elements = {elements}
    elements.forEach(element => {{
        const elementList = document.querySelectorAll(element)
        elementList.forEach(element => {{
            
            element.addEventListener('click', (e) => {{
                const event = {{
                    'element': e.target.nodeName,
                    'event': e.type,
                    'client_site': '{my_client_site['client_site']}',
                    'value': e.target.textContent.trim()
                }}
                console.log(event)
                events.push(event)
            }})
        }})
        elementList.forEach(element => {{
            element.addEventListener('mouseover', (e) => {{
                const event = {{
                    'element': e.target.nodeName,
                    'event': e.type,
                    'client_site': '{my_client_site['client_site']}',
                    'value': e.target.textContent.trim()
                }}
                console.log(event)
                events.push(event)
            }})
        }})
    }})
    """
    # add the script to the client site
    mongo.db.client_sites.update_one(
        {'_id': ObjectId(site_id)},
        {'$set': {'script': script}}
    )
    return Response(script, mimetype='text/javascript')


################ END GENERATE SCRIPT ROUTE ############

# request looks like this: REQUEST DATA  [{'element': 'A', 'event': 'mouseover', 'client_site': 'https://statuesque-dango-bb3731.netlify.app/';, 'value': 'Instagram'}, {'element': 'A', 'event': 'mouseover', 'client_site': 'https://statuesque-dango-bb3731.netlify.app/';, 'value': 'Twitter'}, {'element': 'A', 'event': 'mouseover', 'client_site': 'https://statuesque-dango-bb3731.netlify.app/';, 'value': 'Facebook'}, {'element': 'A', 'event': 'mouseover', 'client_site': 'https://statuesque-dango-bb3731.netlify.app/';, 'value': 'Google'}, {'element': 'A', 'event': 'mouseover', 'client_site': 'https://statuesque-dango-bb3731.netlify.app/';, 'value': 'Facebook'}, {'element': 'A', 'event': 'click', 'client_site': 'https://statuesque-dango-bb3731.netlify.app/';, 'value': 'Facebook'}, {'isTrusted': True}]
# REWRITE TO CREATE A PageData Object
@app.route("/summary", methods=["POST"])
@cross_origin(origins=approved_sites)
# exempt from csrf protection
@csrf.exempt
def summary():
    data = request.get_json()
    print('REQUEST DATA ', data)
    events = data
    # get the site id from the request header
    print(request.headers)
    print('EVENTS: ')
    print(events)
    site_id = request.headers.get('Site-Id')
    client = request.headers.get('Client-Id')

    # create a new page data object
    page_data = mongo.db.page_data.insert_one({
        'client_id': client,
        'site_id': site_id,
    })
    # add the events to the page data object
    for event in events:
        mongo.db.page_data.update_one(
            {'_id': ObjectId(page_data.inserted_id)},
            {'$push': {'events': event}}
        )
    print('PAGE DATA ', page_data)

    return jsonify({"success": True})


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
