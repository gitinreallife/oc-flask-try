# from flask import request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import ValidationError, DataRequired, Length
from app.models import User


class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    about_me = TextAreaField('About me', validators=[Length(min=0, max=140)])
    submit = SubmitField('Submit')

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError('Username is taken.')

    # comment below to produce internal server error
    # def validate_username(self, username):
    #     user = User.query.filter_by(username=username.data).first()
    #     # print('--------------')
    #     # print(user.id is not current_user.id)
    #     # print(user is not None)
    #     # print(user is not None and user.id is not current_user.id)
    #     if user is not None and user.id is not current_user.id:
    #         raise ValidationError('''Username is taken bruh.
    #                                 Please use different username''')


class PostForm(FlaskForm):
    post = TextAreaField('Say something', validators=[DataRequired()])
    submit = SubmitField('Submit')