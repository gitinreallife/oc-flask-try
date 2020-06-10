from app import create_app, db
from app.models import User, Post, Resource, ResourceUsage
from app import mail
from flask_mail import Message

# from flask_login import current_user, login_user, logout_user, login_required
if __name__ == '__main__':
    print('wtfffffffff')
app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Post': Post, 'Resource': Resource,
            'mail': mail, 'Message': Message, 'ResourceUsage': ResourceUsage
            # , 'current_user': current_user,
            # 'login_user': login_user, 'logout_user': logout_user,
            # 'login_required': login_required
            }
