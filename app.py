#!/usr/bin/python

# app.py
import os, json, hashlib
from datetime import datetime, timedelta
from flask import Flask, render_template, request, abort, jsonify
from flask import send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

# SECRET KEY for CSRF PROTECTION
SECRET_KEY = os.urandom(32)

# Page views
appViews = 0
global views

app = Flask(__name__, static_folder='static', template_folder='templates')

# CSRF Protection
csrf = CSRFProtect(app)
app.config['SECRET_KEY'] = SECRET_KEY

#DB HEROKU
db = SQLAlchemy()
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://b9c5bda1af9632:406f00eb@eu-cdbr-west-03.cleardb.net/heroku_f578aa3af4082ba"
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# MyModel
# Flask db migrate execute this block
class Secret(db.Model):
    hash = db.Column(db.String(100), primary_key=True)
    secretText = db.Column(db.String(80))
    createdAt = db.Column(db.String(80))
    expiresAt = db.Column(db.String(80))
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
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

class SecretForm(FlaskForm):
    secret = StringField(validators=[DataRequired()], name=('sec'))
    expV = StringField(validators=[DataRequired()], name=('expV'))
    expG = StringField(validators=[DataRequired()], name=('expT'))


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

@app.route("/secret", methods=['POST'])
def secret():
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