from flask import Blueprint, current_app, request
from .auth import requires_auth, moderator
from .elastic import Elasticsearch, NotDefined
from .image import delete_image_directory



points = Blueprint('points', __name__, )


@points.route('/get_points', methods=['POST'])
def get_points():
    boundaries = request.json
    es = Elasticsearch(current_app.config['ES_CONNECTION_STRING'], index=current_app.config['INDEX_NAME'])
    return es.get_points(boundaries['top_right'], boundaries['bottom_left'])


@points.route('/get_point', methods=['POST'])
def get_point():
    params = request.json
    es = Elasticsearch(current_app.config['ES_CONNECTION_STRING'], index=current_app.config['INDEX_NAME'])
    return es.get_point(point_id=params['id'])


@points.route('/add_point', methods=['POST'])
@requires_auth
def add_point(user):
    req_json = request.json
    sub = user['sub']
    es = Elasticsearch(current_app.config['ES_CONNECTION_STRING'], index=current_app.config['INDEX_NAME'])
    return es.add_point(name=req_json['name'], description=req_json['description'], directions=req_json['directions'],
                        lat=req_json['lat'], lon=req_json['lon'], point_type=req_json['type'],
                        water_exists=req_json['water_exists'], water_comment=req_json.get('water_comment'),
                        fire_exists=req_json['fire_exists'], fire_comment=req_json.get('fire_comment'), user_sub=sub)


@points.route('/modify_point', methods=['POST'])
@requires_auth
def modify_point(user):
    req_json = request.json
    sub = user['sub']
    es = Elasticsearch(current_app.config['ES_CONNECTION_STRING'], index=current_app.config['INDEX_NAME'])
    return es.modify_point(point_id=req_json['id'], name=req_json.get('name', NotDefined()),
                           description=req_json.get('description', NotDefined()),
                           directions=req_json.get('directions', NotDefined()),
                           lat=str(req_json['lat']) if type(req_json.get('lat', NotDefined())) is not NotDefined \
                               else NotDefined(),
                           lon=str(req_json['lon']) if type(req_json.get('lon', NotDefined())) is not NotDefined \
                               else NotDefined(),
                           point_type=req_json.get('type', NotDefined()),
                           water_exists=req_json.get('water_exists', NotDefined()),
                           water_comment=req_json.get('water_comment', NotDefined()),
                           fire_exists=req_json.get('fire_exists', NotDefined()),
                           fire_comment=req_json.get('fire_comment', NotDefined()), user_sub=sub)


@points.route('/search_points', methods=['POST'])
def search_points():
    params = request.json
    phrase = params['phrase']
    point_type = params.get('point_type', None)
    top_right = params.get('top_right', None)
    bottom_left = params.get('bottom_left', None)
    water = params.get('water', None)
    fire = params.get('fire', None)

    es = Elasticsearch(current_app.config['ES_CONNECTION_STRING'], index=current_app.config['INDEX_NAME'])
    return es.search_points(phrase, point_type, top_right, bottom_left, water, fire)


@points.route('/delete_point', methods=['POST'])
@requires_auth
@moderator
def delete_point():
    params = request.json
    es = Elasticsearch(current_app.config['ES_CONNECTION_STRING'], index=current_app.config['INDEX_NAME'])
    es.delete_point(point_id=params['id'])
    delete_image_directory(params['id'])
