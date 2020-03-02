import boto3
from botocore.exceptions import ClientError
import datetime
import hashlib
import os
from werkzeug.utils import secure_filename

from flask import Blueprint, current_app, Flask, jsonify, redirect, render_template, request

from .auth import requires_auth
from .elastic import Elasticsearch

from rabbit_queue import RabbitQueue



images = Blueprint('images', __name__)


@images.route('/add_image/<point_id>', methods=['POST'])
@requires_auth
def add_image(point_id, user):
    sub = user['sub']
    point_id = secure_filename(point_id)
    # check if the post request has the file part
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    # if user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = get_new_file_name(file)
        create_image_directory(point_id)
        upload_file(file, os.path.join(point_id, filename))
        image_queue = RabbitQueue(current_app.config['QUEUE_NAME'])
        image_queue.publish(body=os.path.join(point_id, filename))
        es = Elasticsearch(current_app.config['ES_CONNECTION_STRING'], index=current_app.config['INDEX_NAME'])
        res = es.add_image(point_id, filename, sub)
        return res


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def create_image_directory(path):
    store_property = current_app.config['STORE_PROPERTY'].split('//', 1)[1]

    if current_app.config['STORE_PROPERTY'].startswith('file://'):
        try:
            os.mkdir(os.path.join(store_property, path))
        except FileExistsError:
            pass
    elif current_app.config['STORE_PROPERTY'].startswith('s3://'):
        try:
            s3_client = boto3.client('s3')
            s3_client.put_object(Bucket=store_property, Key=(path + '/'))
        except ClientError as e:
            raise


def upload_file(file_object, filename):
    store_property = current_app.config['STORE_PROPERTY'].split('//', 1)[1]

    if current_app.config['STORE_PROPERTY'].startswith('file://'):
        file_object.save(os.path.join(store_property, filename))
    elif current_app.config['STORE_PROPERTY'].startswith('s3://'):
        try:
            s3_client = boto3.client('s3')
            s3_client.upload_fileobj(file_object, store_property, filename,
                                     ExtraArgs={'ACL': 'public-read', 'ContentType': file_object.mimetype})
        except ClientError as e:
            raise


def get_new_file_name(image_file):
    timestamp = datetime.datetime.utcnow().strftime("%s.%f")
    timestamped_filename = hashlib.md5(os.path.join(timestamp + '_' + image_file.filename).encode()).hexdigest() + '.'\
                           + image_file.filename.rsplit('.', 1)[1].lower()
    return secure_filename(timestamped_filename)
