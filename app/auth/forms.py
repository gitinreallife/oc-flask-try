from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo
from app.models import User
# from flask_login import current_user
# from sqlalchemy import or_

# kindof like viewmodel in c


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password',
                              validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')
    # users = User.query.where('''username = '' or email = '' ''')
    # print(username)
    # print(email)

    # def validate_username(self, username):
    #     users = User.query.filter(or_(User.username == self.username.data,
    #                                   User.email == self.email.data
    #                                   )).all()
    #     error_mssgs = ''
    #     for user in users:
    #         if user.username == self.username.data:
    #             error_mssgs += '''Username is taken.'''
    #         if user.email == self.email.data:
    #             error_mssgs += '''Email is used.'''
    #     if error_mssgs != '':
    #         print(error_mssgs)

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('''Username is taken.
                                    Please use different username''')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('''Email is taken.
                                    Please use different Email''')


class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Request Password Reset')


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')
