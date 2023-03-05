import pytest

from wiating_backend.auth import AuthError, get_token_auth_header


def test_get_token_auth_header_success(client):
    client.get('/get_points', headers={'Authorization': 'Bearer 123abc'})
    assert "123abc" == get_token_auth_header()


def test_get_token_auth_header_missing(client):
    client.get('/get_points')
    with pytest.raises(AuthError):
        get_token_auth_header()


def test_get_token_auth_header_invalid_start(client):
    client.get('/get_points', headers={'Authorization': 'Password 123abc'})
    with pytest.raises(AuthError):
        get_token_auth_header()


def test_get_token_auth_header_one_tag(client):
    client.get('/get_points', headers={'Authorization': 'Bearer'})
    with pytest.raises(AuthError):
        get_token_auth_header()


def test_get_token_auth_header_to_much_tags(client):
    client.get('/get_points', headers={'Authorization': 'Bearer 123abc 321cba'})
    with pytest.raises(AuthError):
        get_token_auth_header()
