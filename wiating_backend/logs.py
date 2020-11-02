from flask import Blueprint, current_app, request, Response
from .auth import requires_auth, moderator
from .constants import MODERATOR
from .elastic import Elasticsearch


logs = Blueprint('logs', __name__, )


@logs.route('/get_user_logs', methods=['POST'])
@requires_auth
def get_user_logs(user):
    params = request.json
    es = Elasticsearch(current_app.config['ES_CONNECTION_STRING'], index=current_app.config['INDEX_NAME'])
    try:
        size = params.get('size', 25)
        offset = params.get('offset', 0)
        return es.get_user_logs(user=user['sub'], size=size, offset=offset)
    except AttributeError:
        return es.get_user_logs(user=user['sub'])


@logs.route('/get_logs', methods=['POST'])
@requires_auth
@moderator
def get_logs(user):
    params = request.json
    es = Elasticsearch(current_app.config['ES_CONNECTION_STRING'], index=current_app.config['INDEX_NAME'])
    try:
        size = params.get('size', 25)
        offset = params.get('offset', 0)
        reviewed_at = params.get('reviewed_at')
        return es.get_logs(point_id=params.get('id'), size=size, offset=offset, reviewed_at=reviewed_at)
    except AttributeError:
        return es.get_logs()


@logs.route('/get_log', methods=['POST'])
@requires_auth
def get_log(user):
    params = request.json
    es = Elasticsearch(current_app.config['ES_CONNECTION_STRING'], index=current_app.config['INDEX_NAME'])
    try:
        if user.get('role') == MODERATOR:
            return es.get_log(log_id=params['log_id'])
        else:
            log = es.get_log(log_id=params['log_id'])
            if log['_source']['modified_by'] == user['sub']:
                return log
            else:
                return Response(status=403)
    except IndexError:
        return Response("Log not found", 404)
    except AttributeError:
        return Response(status=400, response="Log ID required")


@logs.route('/log_reviewed', methods=['POST'])
@requires_auth
@moderator
def log_reviewed(user):
    params = request.json
    es = Elasticsearch(current_app.config['ES_CONNECTION_STRING'], index=current_app.config['INDEX_NAME'])
    try:
        result = es.log_reviewed(params['log_id'], user['sub'])
        if result:
            return Response(status=200)
        else:
            return Response(status=500, response="Database error")
    except (KeyError, IndexError):
        return Response(status=400, response="Existing log ID required")
