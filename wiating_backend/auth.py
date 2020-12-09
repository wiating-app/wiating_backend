from auth0.v3 import Auth0Error
from auth0.v3.authentication import Users
from wiating_backend.constants import APP_METADATA_KEY, MODERATOR
from flask import current_app, request, Response
from functools import wraps
from redis import Redis


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
            sub_key = f'{get_token_auth_header()}:sub'
            moderator_key = f'{get_token_auth_header()}:moderator'

            redis = Redis(host=current_app.config['REDIS_HOST'], port=int(current_app.config['REDIS_PORT']), db=0)

            sub = redis.get(sub_key)
            is_moderator = redis.get(moderator_key)

            if not sub or not is_moderator:
                a0_users = Users(current_app.config['AUTH0_DOMAIN'])
                a0_user = a0_users.userinfo(get_token_auth_header())

                sub = a0_user.get('sub')
                is_moderator = 0

                if a0_user.get(APP_METADATA_KEY):
                    role = a0_user.get(APP_METADATA_KEY).get('role')
                    if role == MODERATOR and \
                        current_app.config.get('INDEX_NAME') in a0_user.get(APP_METADATA_KEY).get('services'):
                        is_moderator = 1

                redis.set(sub_key, sub)
                redis.expire(sub_key, 60)
                redis.set(moderator_key, is_moderator)
                redis.expire(moderator_key, 60)

            user = {'sub': sub.decode() if isinstance(sub, bytes) else sub,
                    'is_moderator': True if int(is_moderator) == 1 else False}
        except Auth0Error:
            return Response("Forbidden", 403)
        except AuthError:
            return Response("Malformed token", 400)

        return f(*args, **kwargs, user=user)

    return decorated


def moderator(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            if kwargs['user']['is_moderator']:
                return f(*args, **kwargs)
        except KeyError:
            return Response("Forbidden", 403)
        return Response("Forbidden", 403)

    return decorated
