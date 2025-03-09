# Description: This file contains the form classes for the login, registration, flashcard, list, and user management forms.

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField, HiddenField, FieldList, FormField
from wtforms.validators import DataRequired, Length, Email, Regexp

# Define the login form 
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=1, max=255)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=1, max=255)])
    submit = SubmitField('Login')

# Define the registration form
class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=1, max=255)])
    password = PasswordField('Password', 
                            validators=[
                                DataRequired(),
                                Length(min=8, message='Password must be at least 8 characters long'),
                                Regexp(r'^(?=.*[A-Z])', message="Password must contain at least one uppercase letter."),
                                Regexp(r'^(?=.*[a-z])', message="Password must contain at least one lowercase letter."),
                                Regexp(r'^(?=.*\d)', message="Password must contain at least one number."),
                                Regexp(r'^(?=.*[@$%*?&])', message="Password must contain at least one special character."),
                                ]
                            )
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=1, max=255)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=1, max=255)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(min=1, max=255)])
    submit = SubmitField('Register')

# Defining the Adding List form (Two Parts)
# Defining the Dynamically-Added Flashcard Forms
class FlashcardForm(FlaskForm):
    question=StringField('Question', validators=[DataRequired(), Length(min=1, max=255)])
    answer=StringField('Answer', validators=[DataRequired(), Length(min=1, max=500)])

# Defining the List Form (the list name)
class ListForm(FlaskForm):
    list_name = StringField('List Name', validators=[DataRequired()])
    flashcards = FieldList(FormField(FlashcardForm), min_entries=1)

# Define the user edit form 
class UserEditForm(FlaskForm):
    edit_index = HiddenField('Edit Index', validators=[DataRequired()])
    new_username = StringField('Username', validators=[DataRequired(), Length(min=1, max=255)])
    new_first_name = StringField('First Name', validators=[DataRequired(), Length(min=1, max=255)])
    new_last_name = StringField('Last Name', validators=[DataRequired(), Length(min=1, max=255)])
    new_email = StringField('Email', validators=[DataRequired(), Email(), Length(min=1, max=255)])
    new_role = SelectField('Role', choices=[('student', 'Student'), ('admin', 'Admin')], validators=[DataRequired()])
    submit = SubmitField('Save')

# Define the list edit form 
class ListEditForm(FlaskForm):
    edit_index = HiddenField('Edit Index', validators=[DataRequired()])
    new_listname = StringField('List Name', validators=[DataRequired(), Length(min=1, max=255)])
    submit = SubmitField('Save')

# Define the delete item form 
class DeleteItemForm(FlaskForm):
    delete_index = HiddenField('Delete Index')
    delete_type = HiddenField('Delete Type')
    submit = SubmitField('Delete')

# Define the assign list form
class AssignListForm(FlaskForm):
    username = StringField('Student Username', validators=[DataRequired(), Length(min=1, max=255)])
    listname = StringField('List Name', validators=[DataRequired(), Length(min=1, max=255)])
    submit = SubmitField('Assign List')

# Define the MFA verification form 
class MFAVerificationForm(FlaskForm):
    verification_code = StringField('Verification Code', validators=[DataRequired(), Length(min=6, max=6)])
    submit = SubmitField('Verify')

# Define the Logout form 
class LogoutForm(FlaskForm):
    submit = SubmitField('Logout')