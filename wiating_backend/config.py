from dotenv import load_dotenv, find_dotenv
from os import environ as env
from . import constants



ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

class BaseConfig:
    DEBUG = False
    TESTING = False

    AUTH0_CALLBACK_URL = env.get(constants.AUTH0_CALLBACK_URL)
    AUTH0_CLIENT_ID = env.get(constants.AUTH0_CLIENT_ID)
    AUTH0_CLIENT_SECRET = env.get(constants.AUTH0_CLIENT_SECRET)
    AUTH0_DOMAIN = env.get(constants.AUTH0_DOMAIN)
    AUTH0_BASE_URL = 'https://' + AUTH0_DOMAIN
    AUTH0_AUDIENCE = env.get(constants.AUTH0_AUDIENCE)
    if AUTH0_AUDIENCE is '':
        AUTH0_AUDIENCE = AUTH0_BASE_URL + '/userinfo'

    STORE_PROPERTY = env.get(constants.S3_BUCKET)
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024

    SECRET_KEY = env.get(constants.SECRET_KEY)
    ES_CONNECTION_STRING = env.get(constants.ES_CONNECTION_STRING)
    INDEX_NAME = env.get(constants.INDEX_NAME)
    QUEUE_NAME = env.get(constants.IMAGE_RESIZER_QUEUE)


class DefaultConfig(BaseConfig):
    DEBUG = True
