from flask import Blueprint, current_app
from .auth import requires_auth
from .elastic import Elasticsearch



points = Blueprint('points', __name__, )

es_connection_string = current_app.config['ES_CONNECTION_STRING']


@points.route('/get_points', methods=['POST'])
def get_points():
    boundaries = request.json
    es = Elasticsearch(es_connection_string, index=current_app.config['INDEX_NAME'])
    return es.get_points(boundaries['top_right'], boundaries['bottom_left'])


@points.route('/get_point', methods=['POST'])
def get_point():
    params = request.json
    es = Elasticsearch(es_connection_string, index=current_app.config['INDEX_NAME'])
    return es.get_point(point_id=params['id'])


@points.route('/add_point', methods=['POST'])
@requires_auth
def add_point(sub):
    req_json = request.json
    es = Elasticsearch(es_connection_string, index=current_app.config['INDEX_NAME'])
    return es.add_point(name=req_json['name'], description=req_json['description'], directions=req_json['directions'],
                        lat=req_json['lat'], lon=req_json['lon'], point_type=req_json['type'],
                        water_exists=req_json['water_exists'], water_comment=req_json.get('water_comment'),
                        fire_exists=req_json['fire_exists'], fire_comment=req_json.get('fire_comment'), user_sub=sub)


@points.route('/modify_point', methods=['POST'])
@requires_auth
def modify_point(sub):
    req_json = request.json
    es = Elasticsearch(es_connection_string, index=current_app.config['INDEX_NAME'])
    return es.modify_point(point_id=req_json['id'], name=req_json['name'], description=req_json['description'],
                           directions=req_json['directions'], lat=req_json['lat'], lon=req_json['lon'],
                           point_type=req_json['type'], water_exists=req_json['water_exists'],
                           water_comment=req_json.get('water_comment'), fire_exists=req_json['fire_exists'],
                           fire_comment=req_json.get('fire_comment'), user_sub=sub)


@points.route('/search_points', methods=['POST'])
def search_points():
    params = request.json
    phrase = params['phrase']
    point_type = params.get('point_type', None)
    top_right = params.get('top_right', None)
    bottom_left = params.get('bottom_left', None)
    water = params.get('water', None)
    fire = params.get('fire', None)

    es = Elasticsearch(es_connection_string, index=current_app.config['INDEX_NAME'])
    return es.search_points(phrase, point_type, top_right, bottom_left, water, fire)
