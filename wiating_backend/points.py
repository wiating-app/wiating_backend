from flask import Blueprint, current_app, request, Response
from .auth import allows_auth, moderator, requires_auth
from .elastic import Elasticsearch, NotDefined
from .image import delete_image_directory
from .logging import logger

points = Blueprint('points', __name__, )


@points.route('/get_points', methods=['POST'])
@allows_auth
def get_points(user):
    req_json = request.json
    es = Elasticsearch(current_app.config['ES_CONNECTION_STRING'], index=current_app.config['INDEX_NAME'])
    if user is not None and user.get('is_moderator'):
        return es.get_points(req_json['top_right'], req_json['bottom_left'], req_json.get('point_type'),
                             is_moderator=True)
    return es.get_points(req_json['top_right'], req_json['bottom_left'], req_json.get('point_type'))


@points.route('/get_point', methods=['POST'])
@allows_auth
def get_point(user):
    params = request.json
    es = Elasticsearch(current_app.config['ES_CONNECTION_STRING'], index=current_app.config['INDEX_NAME'])
    if user is not None and user.get('is_moderator'):
        return es.get_point(point_id=params['id'], is_moderator=True)
    return es.get_point(point_id=params['id'])


@points.route('/add_point', methods=['POST'])
@requires_auth
def add_point(user):
    req_json = request.json
    sub = user['sub']
    is_moderator = user['is_moderator']
    es = Elasticsearch(current_app.config['ES_CONNECTION_STRING'], index=current_app.config['INDEX_NAME'])
    return es.add_point(name=req_json['name'], description=req_json['description'], directions=req_json['directions'],
                        lat=req_json['lat'], lon=req_json['lon'], point_type=req_json['type'],
                        water_exists=req_json.get('water_exists'), water_comment=req_json.get('water_comment'),
                        fire_exists=req_json.get('fire_exists'), fire_comment=req_json.get('fire_comment'),
                        is_disabled=req_json.get('is_disabled', False), user_sub=sub, is_moderator=is_moderator)


@points.route('/modify_point', methods=['POST'])
@requires_auth
def modify_point(user):
    req_json = request.json
    logger.info('modify_point')
    sub = user['sub']
    is_moderator = user['is_moderator']
    es = Elasticsearch(current_app.config['ES_CONNECTION_STRING'], index=current_app.config['INDEX_NAME'])
    if user.get('is_moderator'):
        return es.modify_point(point_id=req_json['id'], name=req_json.get('name', NotDefined()),
                               description=req_json.get('description', NotDefined()),
                               directions=req_json.get('directions', NotDefined()),
                               lat=str(req_json['lat']) if type(req_json.get('lat', NotDefined())) is not NotDefined
                               else NotDefined(),
                               lon=str(req_json['lon']) if type(req_json.get('lon', NotDefined())) is not NotDefined
                               else NotDefined(),
                               point_type=req_json.get('type', NotDefined()),
                               water_exists=req_json.get('water_exists', NotDefined()),
                               water_comment=req_json.get('water_comment', NotDefined()),
                               fire_exists=req_json.get('fire_exists', NotDefined()),
                               fire_comment=req_json.get('fire_comment', NotDefined()),
                               is_disabled=req_json.get('is_disabled', NotDefined()),
                               unpublished=req_json.get('unpublished', NotDefined()), user_sub=sub,
                               is_moderator=is_moderator)
    else:
        return es.modify_point(point_id=req_json['id'], name=req_json.get('name', NotDefined()),
                               description=req_json.get('description', NotDefined()),
                               directions=req_json.get('directions', NotDefined()),
                               lat=str(req_json['lat']) if type(req_json.get('lat', NotDefined())) is not NotDefined
                               else NotDefined(),
                               lon=str(req_json['lon']) if type(req_json.get('lon', NotDefined())) is not NotDefined
                               else NotDefined(),
                               point_type=req_json.get('type', NotDefined()),
                               water_exists=req_json.get('water_exists', NotDefined()),
                               water_comment=req_json.get('water_comment', NotDefined()),
                               fire_exists=req_json.get('fire_exists', NotDefined()),
                               fire_comment=req_json.get('fire_comment', NotDefined()),
                               is_disabled=req_json.get('is_disabled', NotDefined()),
                               unpublished=NotDefined(),
                               user_sub=sub, is_moderator=is_moderator)


@points.route('/search_points', methods=['POST'])
def search_points():
    """
    It takes search parameters from JSON data.
    Result contains items with non-empty `report_reason` only if `report_reason` is set True, if False it returns items
    without `report_reason`, if not set returns both.
    :return:
    """
    params = request.json
    phrase = params.get('phrase')
    point_type = params.get('point_type')
    top_right = params.get('top_right')
    bottom_left = params.get('bottom_left')
    water = params.get('water')
    fire = params.get('fire')
    is_disabled = params.get('is_disabled')
    report_reason = params.get('report_reason')

    es = Elasticsearch(current_app.config['ES_CONNECTION_STRING'], index=current_app.config['INDEX_NAME'])
    return es.search_points(phrase=phrase, point_type=point_type, top_right=top_right, bottom_left=bottom_left,
                            water=water, fire=fire, is_disabled=is_disabled, report_reason=report_reason)


@points.route('/delete_point', methods=['POST'])
@requires_auth
@moderator
def delete_point(user):
    params = request.json
    es = Elasticsearch(current_app.config['ES_CONNECTION_STRING'], index=current_app.config['INDEX_NAME'])
    es.delete_point(point_id=params['id'])
    delete_image_directory(params['id'])
    return Response(status=200)


@points.route('/report', methods=['POST'])
@requires_auth
def report(user):
    params = request.json
    es = Elasticsearch(current_app.config['ES_CONNECTION_STRING'], index=current_app.config['INDEX_NAME'])
    try:
        if user.get('is_moderator'):
            if es.report_moderator(params['id'], params['report_reason']):
                return Response(status=200)
        else:
            if es.report_regular(params['id'], params['report_reason']):
                return Response(status=200)
        return Response(status=503)
    except AttributeError:
        return Response(status=400, response="Report reason and location ID required")


@points.route('/get_unpublished', methods=['POST'])
@requires_auth
@moderator
def get_unpublished(user):
    params = request.json if request.json else dict()
    es = Elasticsearch(current_app.config['ES_CONNECTION_STRING'], index=current_app.config['INDEX_NAME'])
    return es.get_unpublished(size=params.get('size', 25), offset=params.get('offset', 25))
