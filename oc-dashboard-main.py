from app import create_app, db
from app.models import User, Post
from app import mail
from flask_mail import Message

# from flask_login import current_user, login_user, logout_user, login_required

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Post': Post,
            'mail': mail, 'Message': Message
            # , 'current_user': current_user,
            # 'login_user': login_user, 'logout_user': logout_user,
            # 'login_required': login_required
            }
