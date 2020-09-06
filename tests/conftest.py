import pytest
from wiating_backend import create_app
from wiating_backend.config import BaseConfig


@pytest.fixture
def env_mock(mocker):
    mocker.patch('wiating_backend.config.find_dotenv', autospec=True, return_value=None)

    env_mock = dict()
    env_mock['DEBUG'] = False
    env_mock['TESTING'] = False

    env_mock['AUTH0_CLIENT_ID'] = "some_secret"
    env_mock['AUTH0_DOMAIN'] = "some_domain"
    env_mock['AUTH0_CLIENT_SECRET'] = "another_secret"
    env_mock['AUTH0_CALLBACK_URL'] = "some_callback"
    env_mock['AUTH0_AUDIENCE'] = "some_audience"
    env_mock['SECRET_KEY'] = "some_key"
    env_mock['S3_BUCKET'] = "some_bucket"
    env_mock['ES_CONNECTION_STRING'] = "some_connection_string"
    env_mock['IMAGE_RESIZER_QUEUE'] = "some_queue"
    env_mock['DASHBOARD_CONFIG_FILE_PATH'] = "some_dashboard"
    env_mock['AUTH0_BASE_URL'] = 'some_protocol_prefix' + env_mock['AUTH0_DOMAIN']
    env_mock['STORE_PROPERTY'] = "some_property"
    env_mock['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}
    env_mock['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024
    env_mock['INDEX_NAME'] = "some_name"
    env_mock['QUEUE_NAME'] = "another_name"

    mocker.patch('wiating_backend.config.env', spec=env_mock)


@pytest.fixture
def app(env_mock):
    test_config = BaseConfig()
    app = create_app(test_config)
    return app
