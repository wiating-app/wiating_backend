from flask import Blueprint, current_app, request
from .auth import requires_auth
from .elastic import Elasticsearch



logs = Blueprint('logs', __name__, )


@logs.route('/get_logs', methods=['POST'])
@requires_auth
def get_points(user):
    if user['role'] == 'moderator':
        return {"yes": "yes yes"}
    return {"no": "no no"}
