""" This module is the main flask application """
from logging.config import dictConfig
import json

from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

from in_memory_user_store import InMemoryUserStore
from in_memory_account_store import InMemoryAccountStore
from user_collection import UserCollection
from account_collection import AccountCollection
from errors import APIError

# Confgure our two loggers
# Root: For general logging to the error stream
# Audit: For logging to the audit.log file for when auditers need to audit our system
dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }, 'auditFormatter': {
        'format': '[AUDIT - %(asctime)s]: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }, 'auditHandler': {
        'formatter': 'auditFormatter',
        'class': 'logging.handlers.RotatingFileHandler',
        'filename': "audit.log",
        'maxBytes': 5000000,
        'backupCount': 10
    } },
     'loggers': {
           'audit': {
        'level': 'INFO',
        'handlers': ['auditHandler'],
        "propagate": False
,    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi'],
    },
})

app = Flask(__name__)
app.config.from_file("config.json", load=json.load)

jwt = JWTManager(app)
store = UserCollection(user_store=InMemoryUserStore())
accountCollection = AccountCollection(account_store=InMemoryAccountStore())

@app.errorhandler(APIError)
def api_error(e):
    """ Handles all our custom errors meant for the api level. Non-custom errors will return a status-code 500 and be logged as ERROR"""
    app.logger.warning("An error occurred while handling a request. e='%s'", e)
    return jsonify(e.to_dict()), e.status_code

# USER ROUTES
@app.route("/users", methods = ["POST"])
def create_user():
    """ Endpoint for creating a new user """
    content = request.get_json()
    if "username" not in content:
        raise APIError("username not submitted in body", 400)
    username = content['username']
    user, pwd = store.create_user(username)
    app.logger.info("Successfully created a new user. username=%s, user_id=%s", user.username, user.id)
    return jsonify({"user": user, "pwd": pwd})


@app.route("/users/<username>", methods = ["GET"])
def get_user(username: str):
    """ Endpoint for getting a user by username """
    user = store.get_user(username)
    app.logger.info("Successfully fetched user upon request. username=%s, user_id=%s", user.username, user.id)
    return jsonify({"username": user.username})

@app.route("/auth", methods = ["GET"])
def authenticate():
    """ Endpoint for authenticating a user and getting an access token"""
    if "username" not in request.authorization:
        raise APIError("username not submitted with basic auth", 400)
    if "password" not in request.authorization:
        raise APIError("password not submitted with basic auth", 400)

    username = request.authorization["username"]
    pwd = request.authorization["password"]

    user = store.authenticate(username, pwd)
    token = create_access_token(identity=user.id)

    app.logger.info("User successfully authenticated username=%s, user_id=%s", user.username, user.id)
    return jsonify({"token": token})

# ACCOUNT ROUTES
@app.route('/accounts', methods=['POST'])
@jwt_required()
def create_account():
    """ Endpoint for creating a new account for a user """
    user_id = get_jwt_identity()
    content = request.get_json()

    if "balance" not in content:
        raise APIError("balance not submitted in body", 400)
    balance = content['balance']

    account = accountCollection.create_account(user_id, balance)

    app.logger.info("Successfully created a new account. account_id=%s, user_id=%s", account.id, user_id)
    return jsonify(account)


@app.route('/accounts/<account_id>', methods=['GET'])
@jwt_required()
def get_account(account_id: str):
    """ Endpoint for getting a particular account for a user """
    user_id = get_jwt_identity()
    account = accountCollection.get_user_account(user_id, account_id)
    app.logger.info("Successfully fetched account for user upon request. account_id=%s, user_id=%s", account.id, user_id)
    return jsonify(account)

@app.route('/accounts', methods=['GET'])
@jwt_required()
def get_accounts():
    """ Endpoint for getting all accounts for a user """
    user_id = get_jwt_identity()
    accounts = accountCollection.get_user_accounts(user_id)
    app.logger.info("Successfully fetched accounts for user upon request.  user_id=%s", user_id)
    return jsonify(accounts)


@app.route('/accounts/<account_id>', methods=['PATCH'])
@jwt_required()
def transfer(account_id: str):
    """ Endpoint for initializing a transfer """
    user_id = get_jwt_identity()
    content = request.get_json()

    if "to_account_id" not in content:
        raise APIError("to_account_id not submitted in body", 400)
    to_account_id = content['to_account_id']

    if "amount" not in content:
        raise APIError("amount not submitted in body")
    amount = content['amount']
    
    account = accountCollection.transfer(user_id, account_id, to_account_id, amount)
    app.logger.info("Successfully transfered an amount between two accounts. from_account_id=%s, to_account_id=%s", account_id, to_account_id)
    return jsonify(account)