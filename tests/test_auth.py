from flask import url_for
import pytest

from wiating_backend.auth import AuthError, get_token_auth_header, requires_auth, moderator


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


@moderator
def some_function(user):
    return "some text"


def test_moderator_decorator_wrong_role_name():
    res = some_function(user={'role': 'admin'})
    res.status_code = 403


def test_moderator_decorator_wrong_key():
    res = some_function(user={'abc': 'def'})
    res.status_code = 403


def test_moderator_decorator_empty_dict():
    res = some_function(user={})
    res.status_code = 403


def test_moderator_decorator_no_kwargs():
    res = some_function()
    res.status_code = 403

