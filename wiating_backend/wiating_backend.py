# -*- coding: utf-8 -*-

"""Python Flask Wiating API backend
"""
from auth0.v3 import Auth0Error
from auth0.v3.authentication import Users
import boto3
from botocore.exceptions import ClientError
import datetime
from dotenv import load_dotenv, find_dotenv
import flask_monitoringdashboard as dashboard
from functools import wraps
import hashlib
import os
from os import environ as env
from werkzeug.utils import secure_filename
from werkzeug.exceptions import HTTPException

from flask import Flask, jsonify, redirect, render_template, request
from flask_cors import CORS

import constants

from elastic import Elasticsearch
from rabbit_queue import RabbitQueue


ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

AUTH0_CALLBACK_URL = env.get(constants.AUTH0_CALLBACK_URL)
AUTH0_CLIENT_ID = env.get(constants.AUTH0_CLIENT_ID)
AUTH0_CLIENT_SECRET = env.get(constants.AUTH0_CLIENT_SECRET)
AUTH0_DOMAIN = env.get(constants.AUTH0_DOMAIN)
AUTH0_BASE_URL = 'https://' + AUTH0_DOMAIN
AUTH0_AUDIENCE = env.get(constants.AUTH0_AUDIENCE)
if AUTH0_AUDIENCE is '':
    AUTH0_AUDIENCE = AUTH0_BASE_URL + '/userinfo'

S3_BUCKET = env.get(constants.S3_BUCKET)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


app = Flask(__name__, static_url_path='/public', static_folder='./public')
app.secret_key = env.get(constants.SECRET_KEY)
app.debug = True

app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024


def group_by_user_sub():
    return hash(request.headers.get("Authorization", None))


dashboard.config.group_by = group_by_user_sub
dashboard.config.init_from(file=env.get(constants.DASHBOARD_CONFIG_FILE_PATH))
dashboard.bind(app)
CORS(app)

es_connection_string = env.get(constatns.ES_CONNECTION_STRING)

QUEUE_NAME = env.get(constants.IMAGE_RESIZER_QUEUE)

# Error handler
class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


@app.errorhandler(Exception)
def handle_auth_error(ex):
    response = jsonify(message=str(ex))
    response.status_code = (ex.code if isinstance(ex, HTTPException) else 500)
    return response


def get_token_auth_header():
    """Obtains the Access Token from the Authorization Header
    """
    auth = request.headers.get("Authorization", None)
    if not auth:
        raise AuthError({"code": "authorization_header_missing",
                        "description":
                            "Authorization header is expected"}, 401)

    parts = auth.split()

    if parts[0].lower() != "bearer":
        raise AuthError({"code": "invalid_header",
                        "description":
                            "Authorization header must start with"
                            " Bearer"}, 401)
    elif len(parts) == 1:
        raise AuthError({"code": "invalid_header",
                        "description": "Token not found"}, 401)
    elif len(parts) > 2:
        raise AuthError({"code": "invalid_header",
                        "description":
                            "Authorization header must be"
                            " Bearer token"}, 401)

    token = parts[1]
    return token


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            users = Users(AUTH0_DOMAIN)
            user = users.userinfo(get_token_auth_header())
        except Auth0Error:
            return redirect('login')
        return f(*args, **kwargs, sub=user['sub'])

    return decorated


# Controllers API
@app.route('/')
def home():
    return render_template('home.html')


@app.route('/get_points', methods=['POST'])
def get_points():
    boundaries = request.json
    es = Elasticsearch(es_connection_string)
    return es.get_points(boundaries['top_right'], boundaries['bottom_left'])


@app.route('/get_point', methods=['POST'])
def get_point():
    params = request.json
    es = Elasticsearch(es_connection_string)
    return es.get_point(params=['id'])


@app.route('/add_point', methods=['POST'])
@requires_auth
def add_point(sub):
    req_json = request.json
    es = Elasticsearch(es_connection_string)
    return es.add_point(name=req_json['name'], description=req_json['description'], directions=req_json['directions'],
                        lat=req_json['lat'], lon=req_json['lon'], point_type=req_json['type'],
                        water_exists=req_json['water_exists'], water_comment=req_json.get('water_comment'),
                        fire_exists=req_json['fire_exists'], fire_comment=req_json.get('fire_comment'), user_sub=sub)


@app.route('/modify_point', methods=['POST'])
@requires_auth
def modify_point(sub):
    req_json = request.json
    es = Elasticsearch(es_connection_string)
    return es.modify_point(point_id=req_json['id'], name=req_json['name'], description=req_json['description'],
                           directions=req_json['directions'], lat=req_json['lat'], lon=req_json['lon'],
                           point_type=req_json['type'], water_exists=req_json['water_exists'],
                           water_comment=req_json.get('water_comment'), fire_exists=req_json['fire_exists'],
                           fire_comment=req_json.get('fire_comment'), user_sub=sub)


def create_s3_directory(s3_client, path):
    try:
        s3_client.put_object(Bucket=S3_BUCKET, Key=(path + '/'))
    except ClientError as e:
        raise


def upload_file(s3_client, file_object, filename):
    try:
        s3_client.upload_fileobj(file_object, S3_BUCKET, filename, ExtraArgs={'ACL': 'public-read',
                                                                              'ContentType': file_object.mimetype})
    except ClientError as e:
        raise


def get_new_file_name(image_file):
    timestamp = datetime.datetime.utcnow().strftime("%s")
    timestamped_filename = hashlib.md5(os.path.join(timestamp + '_' + image_file.filename).encode()).hexdigest() + '.'\
                           + image_file.filename.rsplit('.', 1)[1].lower()
    return secure_filename(timestamped_filename)


@app.route('/add_image/<point_id>', methods=['POST'])
@requires_auth
def add_image(point_id, sub):
    # check if the post request has the file part
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    # if user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        return redirect(request.url)
    if file and allowed_file(file.filename):
        s3_client = boto3.client('s3')
        filename = get_new_file_name(file)
        create_s3_directory(s3_client, point_id)
        upload_file(s3_client, file, os.path.join(point_id, filename))
        image_queue = RabbitQueue(QUEUE_NAME)
        image_queue.publish(body=os.path.join(point_id, filename))
        es = Elasticsearch(es_connection_string)
        res = es.add_image(point_id, filename, sub)
        return res


@app.route('/search_points', methods=['POST'])
def search_points():
    params = request.json
    phrase = params['phrase']
    point_type = params.get('point_type', None)
    top_right = params.get('top_right', None)
    bottom_left = params.get('bottom_left', None)
    water = params.get('water', None)
    fire = params.get('fire', None)

    es = Elasticsearch(es_connection_string)
    return es.search_points(phrase, point_type, top_right, bottom_left, water, fire)
