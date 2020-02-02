from dotenv import load_dotenv, find_dotenv
from os import environ as env
from . import constants



ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

class BaseConfig:
    def __init__(self):
        self.DEBUG = False
        self.TESTING = False

        self.AUTH0_CALLBACK_URL = env.get(constants.AUTH0_CALLBACK_URL)
        self.AUTH0_CLIENT_ID = env.get(constants.AUTH0_CLIENT_ID)
        self.AUTH0_CLIENT_SECRET = env.get(constants.AUTH0_CLIENT_SECRET)
        self.AUTH0_DOMAIN = env.get(constants.AUTH0_DOMAIN)
        self.AUTH0_BASE_URL = 'https://' + self.AUTH0_DOMAIN
        self.AUTH0_AUDIENCE = env.get(constants.AUTH0_AUDIENCE)
        if self.AUTH0_AUDIENCE == '':
            self.AUTH0_AUDIENCE = self.AUTH0_BASE_URL + '/userinfo'

        self.STORE_PROPERTY = env.get(constants.S3_BUCKET)
        self.ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
        self.MAX_CONTENT_LENGTH = 10 * 1024 * 1024

        self.SECRET_KEY = env.get(constants.SECRET_KEY)
        self.ES_CONNECTION_STRING = env.get(constants.ES_CONNECTION_STRING)
        self.INDEX_NAME = env.get(constants.INDEX_NAME)
        self.QUEUE_NAME = env.get(constants.IMAGE_RESIZER_QUEUE)


class DefaultConfig(BaseConfig):
    pass
