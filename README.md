# Dashboard - Main Service #

Main service for Opencloud dashboard that consist (may change)

1. User management
2. Dashboard collection
3. Historical data store
4. (includes) Multiple tennant

### Stacks
1. Flask Framework (Python)
2. Postgres (Find out what ORM available)

### TODO:

1. List all dependencies (3rd party libs)
2. Provide API reference document.

See requirements.txt for full list
python3 -m venv venv
pip install flask
pip install python-dotenv
pip install flask-wtf
pip install flask-sqlalchemy
pip install flask-migrate
    flask db init
    flask db migrate -m "users table"
    flask db migrate -m "posts table"
    flask db upgrade
pip install flask-login
pip install flask-mail
pip install pyjwt
pip install email_validator
python -m smtpd -n -c DebuggingServer localhost:8025

----for frontend
pip install flask-bootstrap
pip install flask-moment
