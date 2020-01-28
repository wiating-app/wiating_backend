from copy import deepcopy
from datetime import datetime
from elasticsearch import Elasticsearch as ES



def add_to_or_create_list(location, name, query):
    try:
        location[name]
    except KeyError:
        location[name] = []
    location[name].append(query)


class Elasticsearch:
    def __init__(self, connection_string, index='wiaty'):
        self.es = ES([connection_string])
        self.index = index
        self.fields_to_return = ["name", "description", "directions", "location", "type", "water.exists", "water.comment", "fire.exists", "fire.comment", "created_timestamp", "last_modified_timestamp", "images.name", "images.created_timestamp"]

    def search_points(self, phrase, point_type=None, top_right=None, bottom_left=None, water=None, fire=None):
        body = {
          "query": {
            "bool": {
              "must": [{
                "multi_match": {
                  "query": phrase,
                  "fields": [
                    "name^3",
                    "description",
                    "directions"
                  ]
                }
              }]
            }
          }
        }
        if point_type is not None:
            add_to_or_create_list(location=body['query']['bool'], name='filter', query={"term": {"type": {"value": point_type}}})
        if top_right is not None and bottom_left is not None:
            add_to_or_create_list(location=body['query']['bool'], name='filter', query={
                    "geo_bounding_box" : {
                        "location" : {
                            "top_left" : {
                                "lat" : str(top_right['lat']),
                                "lon" : str(bottom_left['lon'])
                            },
                            "bottom_right" : {
                                "lat" : str(bottom_left['lat']),
                                "lon" : str(top_right['lon'])
                            }
                        }
                    }
                }
            )
        if water is not None:
            add_to_or_create_list(location=body['query']['bool'], name='filter', query={"term": {"water.exists": water}})
        if fire is not None:
            add_to_or_create_list(location=body['query']['bool'], name='filter', query={"term": {"fire.exists": fire}})
        response = self.es.search(index=self.index, body=body, _source_includes=self.fields_to_return)
        return {'points': response['hits']['hits']}


    def get_points(self, top_right, bottom_left):
        body = '''{
        "query": {
            "bool" : {
                "must" : {
                    "match_all" : {}
                },
                "filter" : {
                    "geo_bounding_box" : {
                        "validation_method": "COERCE",
                        "location" : {
                            "top_left" : {
                                "lat" : ''' + str(top_right['lat']) + ''',
                                "lon" : ''' + str(bottom_left['lon']) + '''
                            },
                            "bottom_right" : {
                                "lat" : ''' + str(bottom_left['lat']) + ''',
                                "lon" : ''' + str(top_right['lon']) + '''
                            }
                        }
                    }
                }
            }
        },
      	"size": 9000
    	}'''
        response = self.es.search(index=self.index, body=body, _source_includes=self.fields_to_return)
        return {'points': response['hits']['hits']}

    def get_point(self, point_id):
        return self.es.get(index=self.index, id=point_id, _source_includes=self.fields_to_return)

    def save_backup(self, index_suffix, body, doc_id):
        body['id'] = doc_id
        res = self.es.index(index=self.index + index_suffix, body=body)

    def modify_point(self, point_id, name, description, directions, lat, lon, point_type, user_sub, water_exists, fire_exists, water_comment=None, fire_comment=None):
        body = self.es.get(index=self.index, id=point_id)['_source']
        old_body = deepcopy(body)
        body['name'] = name
        body['description'] = description
        body['directions'] = directions
        body['location']['lat'] = str(lat)
        body['location']['lon'] = str(lon)
        body['type'] = point_type
        body['water']['exists'] = water_exists
        body['fire']['exists'] = fire_exists
        body['last_modified_timestamp'] = datetime.utcnow().strftime("%s")
        body['last_modified_by'] = user_sub
        if water_comment is not None:
            body['water']['comment'] = water_comment
        if fire_comment is not None:
            body['fire']['comment'] = fire_comment
        if water_exists is False:
            body['water']['comment'] = None
        if fire_exists is False:
            body['fire']['comment'] = None
        res = self.es.index(index=self.index, id=point_id, body=body)
        if res['result'] == 'updated':
            save_backup(datetime.today().strftime('%m_%Y'), old_body, point_id)
            return self.es.get(index=self.index, id=point_id, _source_includes=self.fields_to_return)
        return res

    def add_point(self, name, description, directions, lat, lon, point_type, user_sub, water_exists, fire_exists, water_comment=None, fire_comment=None):
        body = {
            "name":  name,
            "description": description,
            "directions": directions,
            "location": {
                "lat": str(lat),
                "lon": str(lon)
            },
            "type": point_type,
            "water": {
                "exists": water_exists
            },
            "fire": {
                "exists": fire_exists
            },
            "created_timestamp": datetime.utcnow().strftime("%s"),
            "created_by": user_sub
        }
        if water_comment is not None:
            body['water']['comment'] = water_comment
        if fire_comment is not None:
            body['fire']['comment'] = fire_comment
        res = self.es.index(index=self.index, body=body)
        if res['result'] == 'created':
            return self.es.get(index=self.index, id=res['_id'], _source_includes=self.fields_to_return)
        return res

    def add_image(self, point_id, path, sub):
        try:
            images = self.es.get(index=self.index, id=point_id, _source=['images'])['_source']['images']
        except KeyError:
            images = []
        if not isinstance(images, list):
            images = [images]
        new_image = {"name": path, "created_timestamp": datetime.utcnow().strftime("%s"), "created_by": sub}
        images.append(new_image)
        res = self.es.update(index=self.index, id=point_id, body={"doc": {"images": images}})
        if res['result'] == 'updated':
            return self.es.get(index=self.index, id=point_id, _source_includes=self.fields_to_return)
        return res
