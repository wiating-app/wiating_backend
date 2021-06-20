import datetime
import hashlib
import os
import shutil

import boto3
from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from image_resizer import resize_image
from werkzeug.utils import secure_filename

from .auth import require_auth, require_moderator
from .config import DefaultConfig
from .elastic import Elasticsearch


images = APIRouter()
config = DefaultConfig()


@images.post('/add_image/{point_id}')
def add_image(point_id: str, file: UploadFile = File(...), es: dict = Depends(Elasticsearch.connection),
              user: dict = Depends(require_auth)):
    sub = user['sub']
    # check if the post request has the file part
    # if user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        raise HTTPException(status_code=400)
    if file and allowed_file(file.filename):
        filename = get_new_file_name(file)
        create_image_directory(point_id)
        upload_file(file, os.path.join(point_id, filename))
        resize_image.delay(os.path.join(point_id, filename))
        try:
            res = es.add_image(point_id, filename, sub)
            return res
        except KeyError:
            raise HTTPException(status_code=400)


@images.delete('/delete_image/{point_id}/{image_name}')
def delete_image(point_id: str, image_name: str, es: dict = Depends(Elasticsearch.connection),
                 user: dict = Depends(require_moderator)):
    sub = user['sub']
    es.delete_image(point_id=point_id, image_name=image_name, sub=sub)
    delete_image_file(point_id=point_id, image_name=image_name)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in config.ALLOWED_EXTENSIONS


def delete_image_directory(path):
    store_property = config.STORE_PROPERTY.split('//', 1)[1]

    if config.STORE_PROPERTY.startswith('file://'):
        try:
            shutil.rmtree(os.path.join(store_property, path))
        except FileNotFoundError:
            pass
    elif config.STORE_PROPERTY.startswith('s3://'):
        # TODO delete S3 directory
        pass


def delete_image_file(point_id, image_name):
    store_property = config.STORE_PROPERTY.split('//', 1)[1]
    file_name, file_extension = image_name.rsplit('.', 1)

    if config.STORE_PROPERTY.startswith('file://'):
        os.remove(os.path.join(store_property, point_id, image_name))
        os.remove(os.path.join(store_property, point_id, file_name + '_m.' + file_extension))
    elif config.STORE_PROPERTY.startswith('s3://'):
        # TODO delete S3 images
        pass


def create_image_directory(path):
    store_property = config.STORE_PROPERTY.split('//', 1)[1]

    if config.STORE_PROPERTY.startswith('file://'):
        try:
            os.mkdir(os.path.join(store_property, path))
        except FileExistsError:
            pass
    elif config.STORE_PROPERTY.startswith('s3://'):
        try:
            s3_client = boto3.client('s3')
            s3_client.put_object(Bucket=store_property, Key=(path + '/'))
        except ClientError:
            raise


def upload_file(file_object, filename):
    store_property = config.STORE_PROPERTY.split('//', 1)[1]

    if config.STORE_PROPERTY.startswith('file://'):
        with open(os.path.join(store_property, filename), 'wb') as write_file:
            write_file.write(file_object.file.read())
    elif config.STORE_PROPERTY.startswith('s3://'):
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
