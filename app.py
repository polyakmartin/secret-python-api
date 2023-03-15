#!/usr/bin/python

#One server file with config and app etc.
# app.py
import os, json, hashlib
from datetime import datetime, timedelta
from flask import Flask, render_template, request, abort, jsonify
from flask import send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# SECRET KEY for CSRF PROTECTION
SECRET_KEY = os.urandom(32)

# Page views
global views

# Basic flask app config
app = Flask(__name__, static_folder='static', template_folder='templates')

# CSRF Protection
app.config['SECRET_KEY'] = SECRET_KEY

# DB Mysql
db = SQLAlchemy()
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://b9c5bda1af9632:406f00eb@eu-cdbr-west-03.cleardb.net/heroku_f578aa3af4082ba"
app.config['SQLALCHEMY_POOL_RECYCLE'] = 499  # For 500 error when heroku's clearDB not response
app.config['SQLALCHEMY_POOL_TIMEOUT'] = 20

# Flask mysql module
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# MyModel
# Flask db migrate execute this block
class Secret(db.Model):
    id_secret = db.Column(db.Integer, primary_key=True, autoincrement=True)
    hash = db.Column(db.String(100))
    secretText = db.Column(db.String(80))
    createdAt = db.Column(db.String(45))
    expiresAt = db.Column(db.String(45))
    remainingViews = db.Column(db.Integer)

    def __init__(self, hash, secretText, createdAt, expiresAt, remainingViews):
        self.hash = hash
        self.secretText = secretText
        self.createdAt = createdAt
        self.expiresAt = expiresAt
        self.remainingViews = remainingViews


# MyForm
# Flask minimal form 
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField
from wtforms.validators import DataRequired, NumberRange

class SecretForm(FlaskForm):
    secret = StringField(validators=[DataRequired()], name=('sec'))
    expV = IntegerField(validators=[DataRequired(), NumberRange(min=0)], name=('expV'))
    expG = IntegerField(validators=[DataRequired(), NumberRange(min=0)], name=('expT'))


# API 
# Routes
@app.route("/", methods=['GET'])
def index():
    form = SecretForm()
    return render_template('index.html', form=form)

# Lazy favicon for fun
@app.route("/favicon.ico")
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

# Post request
@app.route("/secret", methods=['POST'])
def secret():
    if request.method == 'GET':
        abort(404)
    else:
        now = datetime.now()
        token = now + timedelta(minutes=int(request.form['expT']))
        users_hash = request.form['sec']
        hasher = hashlib.md5(users_hash.encode()) # md5 hashing
        secret = Secret(str(hasher.hexdigest()), str(users_hash), str(now), str(token), int(request.form['expV']))
        secret_form = {
            "hash": str(hasher.hexdigest()),
            "secret": request.form['sec'],
            "expireAfterViews": request.form['expV'],
            "expireAfter": request.form['expT']
        }
        db.session.add(secret)
        db.session.commit()
        return json.dumps(secret_form)


# Get request
@app.route("/secret/<string:hash>", methods=['GET'])
def secret_hash(hash):
    query = Secret.query.filter_by(hash=hash).first_or_404()
    views = int(query.remainingViews) - 1
    if str(query.expiresAt) > str(datetime.now()):
        if (views >= 1):
            query.remainingViews = views
            db.session.commit()
        else:
            abort(404)
    else:
        abort(404)
    return render_template('secret.html', query=query)



# Running flask app
if __name__=="__main__":
    app.run()


# Create Procfile for running gunicorn which run flask app on heroku