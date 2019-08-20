from wtforms import Form, StringField, PasswordField, validators, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length, Optional, InputRequired

class LoginForm(Form):
    username = StringField("Username", validators=[DataRequired(message=("Please enter your username"))])
    password = PasswordField("Password", validators=[DataRequired(message=("Please enter your password"))])
    login = SubmitField("Log In")

class SignupForm(Form):
    username = StringField("Username", validators=[InputRequired(message=("Please enter a username")),
                                                Length(min=6, message=("Your username must be at least 6 characters"))])
    password = PasswordField("Password", validators=[DataRequired(message=("Please enter your password")),
                                                Length(min=6, message=("Your password must be at least 6 characters"))])
    confirm = PasswordField("Confirm Your Password", validators=[DataRequired(), EqualTo("password", message=("Passwords do not match"))])
    signup = SubmitField("Sign Up")
