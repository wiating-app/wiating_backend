from functools import wraps

from auth0.v3 import Auth0Error
from auth0.v3.authentication import Users
from fastapi import Header, HTTPException
from redis import Redis

from wiating_backend.config import DefaultConfig
from wiating_backend.constants import APP_METADATA_KEY, MODERATOR

from keycloak import KeycloakOpenID
from redis import Redis
from wiating_backend.config import DefaultConfig

keycloak_openid = KeycloakOpenID(server_url="http://keycloak:8080/",
                                 client_id="wiating",
                                 realm_name="wiating",
                                 client_secret_key=DefaultConfig().keycloak_secret_key)

# Error handler
class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


def get_token_auth_header(authorization):
    """Obtains the Access Token from the Authorization Header
    """
    if not authorization:
        raise AuthError({"code": "authorization_header_missing",
                        "description":
                            "Authorization header is expected"}, 401)

    parts = authorization.split()

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


def check_permissions(token, config: DefaultConfig = DefaultConfig()):
    sub_key = f'{token}:sub'
    moderator_key = f'{token}:moderator'

    redis = Redis(host=config.REDIS_HOST, port=int(config.REDIS_PORT), db=0)

    sub = redis.get(sub_key)
    is_moderator = redis.get(moderator_key)

    if not sub or not is_moderator:
        userinfo = keycloak_openid.userinfo(token)

        sub = userinfo.get('sub')
        is_moderator = 0

        if 'roles' in userinfo:
            roles = userinfo['roles']
            if 'moderator' in roles:
                is_moderator = 1

        redis.set(sub_key, sub)
        redis.expire(sub_key, 60)
        redis.set(moderator_key, is_moderator)
        redis.expire(moderator_key, 60)

    return {'sub': sub.decode() if isinstance(sub, bytes) else sub,
            'is_moderator': True if int(is_moderator) == 1 else False}


def require_auth(authorization: str = Header(None)):
    try:
        token = get_token_auth_header(authorization=authorization)
        user = check_permissions(token)
        return user
    except Auth0Error:
        raise HTTPException(status_code=403, detail="Forbidden")
    except AuthError:
        raise HTTPException(status_code=400, detail="Malformed token")


def require_moderator(authorization: str = Header(None)):
    user = require_auth(authorization=authorization)
    try:
        if not user['is_moderator']:
            raise HTTPException(status_code=403, detail="Forbidden")
    except KeyError:
        return HTTPException(status_code=403, detail="Forbidden")
    return user


def allow_auth(authorization: str = Header(None)):
    try:
        token = get_token_auth_header(authorization=authorization)
        user = check_permissions(token)
        return user
    except:
        return None
