from auth0.v3 import Auth0Error
from flask import request, url_for
import pytest
from unittest.mock import MagicMock

from wiating_backend.auth import AuthError, get_token_auth_header, requires_auth, moderator
from wiating_backend.constants import APP_METADATA_KEY


def test_get_token_auth_header_success(client):
    client.get(url_for('points.get_point'), headers=[('Authorization', 'Bearer 123abc')])
    assert "123abc" == get_token_auth_header()


def test_get_token_auth_header_missing(client):
    client.get(url_for('points.get_point'), headers=[])
    with pytest.raises(AuthError):
        get_token_auth_header()


def test_get_token_auth_header_invalid_start(client):
    client.get(url_for('points.get_point'), headers=[('Authorization', 'Password 123abc')])
    with pytest.raises(AuthError):
        get_token_auth_header()


def test_get_token_auth_header_one_tag(client):
    client.get(url_for('points.get_point'), headers=[('Authorization', 'Bearer')])
    with pytest.raises(AuthError):
        get_token_auth_header()


def test_get_token_auth_header_to_much_tags(client):
    client.get(url_for('points.get_point'), headers=[('Authorization', 'Bearer 123abc 321cba')])
    with pytest.raises(AuthError):
        get_token_auth_header()


@pytest.fixture
def auth0_users(mocker):
    def user(*_):
        return {'sub': "some sub", APP_METADATA_KEY: {"role": "some role"}}

    auth0_users_mock = MagicMock()
    auth0_users_mock.return_value.userinfo.side_effect = user

    auth0_mock = mocker.patch('wiating_backend.auth.Users', side_effect=auth0_users_mock)

    return auth0_mock


@requires_auth
def requires_auth_decorated(user):
    return user


def test_requires_auth_success(auth0_users, client):
    client.get(url_for('points.get_point'), headers=[('Authorization', 'Bearer 123abc')])
    user = requires_auth_decorated()
    assert user['sub'] == "some sub"
    assert user['role'] == "some role"


@pytest.fixture
def auth0_users_raises(mocker):
    auth0_users_mock = MagicMock()
    auth0_users_mock.return_value.userinfo.side_effect = Auth0Error(status_code=123, error_code=321, message="some")

    auth0_mock = mocker.patch('wiating_backend.auth.Users', side_effect=auth0_users_mock)

    return auth0_mock


def test_requires_auth_unauthorized(auth0_users_raises, client):
    client.get(url_for('points.get_point'), headers=[('Authorization', 'Bearer 123abc')])
    unauthorized = requires_auth_decorated()
    assert unauthorized.status_code == 401


@moderator
def some_function(user):
    return "some text"


def test_moderator_decorator_success():
    assert "some text" == some_function(user={'role': 'moderator'})


def test_moderator_decorator_wrong_role_name():
    with pytest.raises(AuthError):
        some_function(user={'role': 'admin'})


def test_moderator_decorator_wrong_key():
    with pytest.raises(AuthError):
        some_function(user={'abc': 'def'})


def test_moderator_decorator_empty_dict():
    with pytest.raises(AuthError):
        some_function(user={})


def test_moderator_decorator_no_kwargs():
    with pytest.raises(AuthError):
        some_function()

