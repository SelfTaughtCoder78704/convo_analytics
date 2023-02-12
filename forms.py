from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectMultipleField
from wtforms.validators import DataRequired, Email

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')
    csrfToken = StringField('csrfToken')


class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Register')
    csrfToken = StringField('csrfToken')

class ClientSiteForm(FlaskForm):
    client_site = StringField('Client Site', validators=[DataRequired()])
    submit = SubmitField('Submit')
    csrfToken = StringField('csrfToken')

class AddElementForm(FlaskForm):
    elements = SelectMultipleField(
        'Elements',
        choices=[
            ('button', 'Buttons'),
            ('a', 'Links'),
            ('img', 'Images'),
            ('form', 'Forms')
        ]
    )
    submit = SubmitField('Submit')
    csrfToken = StringField('csrfToken')

class EditSiteForm(FlaskForm):
    client_site = StringField('Client Site', validators=[DataRequired()])
    submit = SubmitField('Submit')
    csrfToken = StringField('csrfToken')