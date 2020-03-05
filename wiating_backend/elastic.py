from copy import deepcopy
from datetime import datetime
from deepdiff import DeepDiff
from elasticsearch import Elasticsearch as ES
import re

from .points import NotDefined



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
        self.fields_to_return = ["name", "description", "directions", "location", "type", "water.exists",
                                 "water.comment", "fire.exists", "fire.comment", "created_timestamp",
                                 "last_modified_timestamp", "images.name", "images.created_timestamp"]

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
            add_to_or_create_list(location=body['query']['bool'], name='filter',
                                  query={"term": {"type": {"value": point_type}}})
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
            add_to_or_create_list(location=body['query']['bool'], name='filter',
                                  query={"term": {"water.exists": water}})
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

    def save_backup(self, index_suffix, old_body, new_body, doc_id, user_sub):
        def extract_key(key):
            return re.search(r"(?<=(root\['))\w*(?='\])", key)[0]

        def iterate_over_diff_output(output):
            result = dict()
            for item in output.keys():
                result[extract_key(item)] = output[item]
            return result

        document = {"modified_by": user_sub, "doc_id": doc_id,
                    "timestamp": datetime.utcnow().strftime("%Y/%m/%d %H:%M:%S"), "name": old_body['name']}
        diff = DeepDiff(old_body, new_body, verbose_level=2,
                        exclude_paths=["root['last_modified_timestamp']","root['last_modified_by']"])
        if diff.get('dictionary_item_added') is not None:
            document["added"] = iterate_over_diff_output(diff['dictionary_item_added'])
        if diff.get('dictionary_item_removed') is not None:
            document["removed"] = iterate_over_diff_output(diff['dictionary_item_removed'])
        if diff.get('values_changed') is not None:
            document["changed"] = iterate_over_diff_output(diff['values_changed'])
        self.es.index(index=''.join((self.index, index_suffix)), body=document)

    def get_logs(self, point_id=None, size=25, offset=0):
        body = {"sort":[{"timestamp": {"order": "desc"}}], "from": offset, "size": size}
        if point_id is not None:
            body['query'] = {'term': {'doc_id.keyword': {'value': point_id}}}
        response = self.es.search(index=self.index + '_*', body=body)
        return {"logs": response['hits']['hits'], "total": response['hits']['total']['value']}


    def modify_point(self, point_id, user_sub, name, description, directions, lat, lon,
                     point_type, water_exists, fire_exists, water_comment, fire_comment):
        body = self.es.get(index=self.index, id=point_id)['_source']
        old_body = deepcopy(body)
        body['name'] = name if type(name) != NotDefined else body['name']
        body['description'] = description if type(description) != NotDefined else body['description']
        body['directions'] = directions if type(directions) != NotDefined else body['directions']
        body['location']['lat'] = str(lat) if type(lat) != NotDefined else body['location']['lat']
        body['location']['lon'] = str(lon) if type(lon) != NotDefined else body['location']['lon']
        body['type'] = point_type if type(point_type) != NotDefined else body['type']
        body['water']['exists'] = water_exists if type(water_exists) != NotDefined else body['water']['exists']
        body['water']['comment'] = water_comment if type(water_comment) != NotDefined else body['water'].get('comment')
        body['fire']['exists'] = fire_exists if type(fire_exists) != NotDefined else body['fire']['exists']
        body['fire']['comment'] = fire_comment if type(fire_comment) != NotDefined else body['fire'].get('comment')
        body['last_modified_timestamp'] = datetime.utcnow().strftime("%s")
        body['last_modified_by'] = user_sub
        res = self.es.index(index=self.index, id=point_id, body=body)
        if res['result'] == 'updated':
            self.save_backup(datetime.today().strftime('_%m_%Y'), old_body, body, point_id, user_sub)
            return self.es.get(index=self.index, id=point_id, _source_includes=self.fields_to_return)
        return res

    def add_point(self, name, description, directions, lat, lon, point_type, user_sub, water_exists, fire_exists,
                  water_comment=None, fire_comment=None):
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
