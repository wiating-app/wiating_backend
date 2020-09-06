import boto3
from botocore.exceptions import ClientError
import datetime
import hashlib
import os
import shutil
from werkzeug.utils import secure_filename

from flask import Blueprint, current_app, redirect, request, Response

from .auth import moderator, requires_auth
from .elastic import Elasticsearch


from image_resizer import resize_image


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
        resize_image.delay(os.path.join(point_id, filename))
        es = Elasticsearch(current_app.config['ES_CONNECTION_STRING'], index=current_app.config['INDEX_NAME'])
        res = es.add_image(point_id, filename, sub)
        return res


@images.route('/delete_image', methods=['POST'])
@requires_auth
@moderator
def delete_image(user):
    params = request.json
    sub = user['sub']
    es = Elasticsearch(current_app.config['ES_CONNECTION_STRING'], index=current_app.config['INDEX_NAME'])
    es.delete_image(point_id=params['id'], image_name=params['image_name'], sub=sub)
    delete_image_file(point_id=params['id'], image_name=params['image_name'])
    return Response(status=200)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def delete_image_directory(path):
    store_property = current_app.config['STORE_PROPERTY'].split('//', 1)[1]

    if current_app.config['STORE_PROPERTY'].startswith('file://'):
        try:
            shutil.rmtree(os.path.join(store_property, path))
        except FileNotFoundError:
            pass
    elif current_app.config['STORE_PROPERTY'].startswith('s3://'):
        # TODO delete S3 directory
        pass


def delete_image_file(point_id, image_name):
    store_property = current_app.config['STORE_PROPERTY'].split('//', 1)[1]
    file_name, file_extension = image_name.rsplit('.', 1)

    if current_app.config['STORE_PROPERTY'].startswith('file://'):
        os.remove(os.path.join(store_property, point_id, image_name))
        os.remove(os.path.join(store_property, point_id, file_name + '_m.' + file_extension))
    elif current_app.config['STORE_PROPERTY'].startswith('s3://'):
        # TODO delete S3 images
        pass


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
        except ClientError:
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
        except ClientError:
            raise


def get_new_file_name(image_file):
    timestamp = datetime.datetime.utcnow().strftime("%s.%f")
    file_name = os.path.join(timestamp + '_' + image_file.filename).encode()
    file_extension = image_file.filename.rsplit('.', 1)[1].lower()
    timestamped_filename = '.'.join((hashlib.md5(file_name).hexdigest(), file_extension))
    return secure_filename(timestamped_filename)
