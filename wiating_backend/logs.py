from flask import Blueprint, current_app, request, Response
from .auth import requires_auth, moderator
from .elastic import Elasticsearch


logs = Blueprint('logs', __name__, )


@logs.route('/get_logs', methods=['POST'])
@requires_auth
@moderator
def get_logs(user):
    params = request.json
    es = Elasticsearch(current_app.config['ES_CONNECTION_STRING'], index=current_app.config['INDEX_NAME'])
    try:
        size = params.get('size', 25)
        offset = params.get('offset', 0)
        return es.get_logs(point_id=params.get('id'), size=size, offset=offset)
    except AttributeError:
        return es.get_logs()


@logs.route('/get_log', methods=['POST'])
@requires_auth
@moderator
def get_log(user):
    params = request.json
    es = Elasticsearch(current_app.config['ES_CONNECTION_STRING'], index=current_app.config['INDEX_NAME'])
    try:
        return es.get_log(log_id=params['log_id'])
    except IndexError:
        return Response("Log not found", 404)
