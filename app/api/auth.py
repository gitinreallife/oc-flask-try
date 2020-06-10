from flask import g, jsonify, request, url_for, abort
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth
from app.models import User
from app.api.errors import error_response
from flask_login import login_user, logout_user, current_user
from app.api import api_bp
from app.api.errors import bad_request

basic_auth = HTTPBasicAuth()
token_auth = HTTPTokenAuth()

#  curl -i -H "Content-Type:application/plain" -X POST -d 'nairobi|1234' http://localhost:5000/api/login
@api_bp.route('/login', methods=['GET', 'POST'])
def login():
    username = request.form.get('username', '', str)
    password = request.form.get('password', '', str)

    if username == '' or password == '':
        return bad_request('Username and password can not be empty')

    user = User.query.filter_by(username=username).first()

    if user is None or not user.check_password_bruh(password):
        return bad_request('Invalid username or password')
    # login_user(user, remember=True)
    g.current_user = user
    return jsonify(g.current_user.to_dict())


@api_bp.route('/logout')
def logout():
    User.revoke_token()
    g.current_user = None
    logout_user()
    return {'message': 'User Logged Out'}

# http --auth nairobi:1234 POST http://localhost:5000/api/tokens
@token_auth.verify_token
def verify_token(token):
    g.current_user = User.check_token(token) if token else None
    return g.current_user is not None


@token_auth.error_handler
def token_auth_error():
    return error_response(401)


@basic_auth.verify_password
def verify_password(username, password):
    user = User.query.filter_by(username=username).first()
    if user is None:
        return False
    g.current_user = user
    return user.check_password_bruh(password)


@basic_auth.error_handler
def basic_auth_error():
    return error_response(401)


@basic_auth.get_password
def get_password(username):
    if username == 'nairobi':
        return '1234'
    return None


# @app.errorhandler(404)
# def not_found(error):
#     return make_response(jsonify({'error': 'Not found Bruh'}), 404)
