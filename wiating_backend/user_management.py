from auth0.v3.management import Auth0
from auth0.v3.authentication import GetToken
from flask import Blueprint, current_app, request

from .auth import requires_auth, moderator



user_mgmt = Blueprint('user_mgmt', __name__, )


def get_token():
    gt = GetToken(current_app.config['AUTH0_DOMAIN'])
    token = gt.client_credentials(current_app.config['AUTH0_CLIENT_ID'],
                                  current_app.config['AUTH0_CLIENT_SECRET'],
                                  'https://{}/api/v2/'.format(current_app.config['AUTH0_DOMAIN']))
    mgmt_api_token = token['access_token']
    return mgmt_api_token


@user_mgmt.route('/ban_user', methods=['POST'])
@requires_auth
@moderator
def ban_user(user):
    params = request.json
    ban_user_id = params['ban_user_id']
    mgmt_api_token = get_token()
    auth0 = Auth0(current_app.config['AUTH0_DOMAIN'], mgmt_api_token)
    body = {"blocked": True}
    auth0.users.update(ban_user_id, body)
    return {"status": "success"}
