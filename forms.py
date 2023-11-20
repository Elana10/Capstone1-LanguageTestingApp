from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, PasswordField
from wtforms.validators import InputRequired, Email, Length, ValidationError, EqualTo
from sqlalchemy import select
from flask import g
from models import User
import language_tool_python

def unique_username():
    """Ensure username is available."""
    message = "That username is already taken. Please enter a unique username."
    def _unique(form, field):
        username = field.data
        database_entry = User.query.filter_by(username = username).all()
        if database_entry:
            if username != g.user.username:
                raise ValidationError(message)
    return _unique

def unique_email():
    """Checks the database for a unique email."""
    message = "That email is already associated with another user. Please enter a unique email."

    def _unique(form,field):
        email = field.data
        database_entry = User.query.filter_by(email=email).all()
        if database_entry:
            if email != g.user.email:
                raise ValidationError(message)
    return _unique

language_list = [('English','English'),('Spanish','Spanish'),('German','German'),('Arabic','Arabic'),('French','French'),('Italian','Italian'),('Portuguese','Portuguese'), ('Farsi','Farsi'),('Japanese','Japanese'),('Chinese','Chinese')]

class Login(FlaskForm):
    """ Form for a registered user to login. """
    username = StringField('Username', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])

class NewUserForm(FlaskForm):
    """Form for adding user to the database."""
    username = StringField('Username', validators=[InputRequired(), unique_username()])
    email = StringField('E-mail', validators=[InputRequired(), Email(), unique_email()])
    password = PasswordField('Password', validators=[InputRequired(), EqualTo('confirm', message = 'Passwords must match.')])
    confirm = PasswordField('Repeat Password', validators=[InputRequired()])    

class NewStoryForm(FlaskForm):
    """Form for adding a new story to the database with base language and translation."""

    title = StringField('Give your translation a title:', validators=[InputRequired(),Length(1,60)])
    translate_text = TextAreaField('Enter your text to be translated here:', validators=[InputRequired(), Length(1,2000)])
    base_lang = SelectField('Base Language:', 
                            choices=language_list, 
                            validators=[InputRequired()])    
    foreign_lang = SelectField('Translation Language:', 
                               choices=language_list,
                                validators=[InputRequired()])
 