from auth0.v3 import Auth0Error
from auth0.v3.management import Auth0
from auth0.v3.authentication import GetToken
from fastapi import APIRouter, Depends, HTTPException

from .auth import require_moderator
from .config import DefaultConfig


user_mgmt = APIRouter()
config = DefaultConfig()


def get_token():
    gt = GetToken(config.AUTH0_DOMAIN)
    token = gt.client_credentials(config.AUTH0_CLIENT_ID,
                                  config.AUTH0_CLIENT_SECRET,
                                  'https://{}/api/v2/'.format(config.AUTH0_DOMAIN))
    mgmt_api_token = token['access_token']
    return mgmt_api_token


@user_mgmt.post('/ban_user/{ban_user_id}', dependencies=[Depends(require_moderator)])
def ban_user(ban_user_id: str):
    ban_user_id = ban_user_id
    mgmt_api_token = get_token()
    auth0 = Auth0(config.AUTH0_DOMAIN, mgmt_api_token)
    body = {"blocked": True}
    try:
        auth0.users.update(ban_user_id, body)
    except Auth0Error:
        raise HTTPException(status_code=403)
    return {"status": "success"}
