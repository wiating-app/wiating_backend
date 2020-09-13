from auth0.v3 import Auth0Error
from auth0.v3.authentication import Users
from wiating_backend.constants import APP_METADATA_KEY
from flask import current_app, redirect, request
from functools import wraps


# Error handler
class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


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
            a0_users = Users(current_app.config['AUTH0_DOMAIN'])
            a0_user = a0_users.userinfo(get_token_auth_header())
            user = {'sub': a0_user.get('sub')}
            if a0_user.get(APP_METADATA_KEY):
                user['role'] = a0_user.get(APP_METADATA_KEY).get('role')
        except (Auth0Error, AuthError):
            return redirect('login')
        return f(*args, **kwargs, user=user)

    return decorated


def moderator(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            if kwargs['user']['role'] == 'moderator':
                return f(*args, **kwargs)
        except KeyError:
            raise AuthError("Not allowed", 403)
        raise AuthError("Not allowed", 403)

    return decorated
