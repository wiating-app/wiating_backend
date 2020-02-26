from flask import Blueprint, current_app, request
from .auth import requires_auth
from .elastic import Elasticsearch



logs = Blueprint('logs', __name__, )


@logs.route('/get_logs', methods=['POST'])
@requires_auth
def get_logs(user):
    if user['role'] == 'moderator':
        params = request.json
        es = Elasticsearch(current_app.config['ES_CONNECTION_STRING'], index=current_app.config['INDEX_NAME'])
        return es.get_logs(point_id=params.get('id'))
    raise Exception("Not allowed")
