from datetime import datetime
from elasticsearch import Elasticsearch as ES


class NotDefined:
    pass


class Point:
    def __init__(self, name, description, directions, lat, lon, point_type, water_exists, fire_exists,
                 created_by, last_modified_by, water_comment=None, fire_comment=None, doc_id=None,
                 created_timestamp=None, last_modified_timestamp=None, images=None, is_disabled=False):
        self.name = name
        self.description = description
        self.directions = directions
        self.lat = str(lat)
        self.lon = str(lon)
        self.point_type = point_type
        self.water_exists = water_exists
        self.fire_exists = fire_exists
        self.water_comment = water_comment
        self.fire_comment = fire_comment
        self.created_timestamp = datetime.utcnow().strftime("%s") if created_timestamp is None else created_timestamp
        self.created_by = created_by
        self.doc_id = doc_id
        self.last_modified_timestamp = datetime.utcnow().strftime("%s") if last_modified_timestamp is None \
            else last_modified_timestamp
        self.last_modified_by = last_modified_by
        self.images = images
        self.is_disabled = is_disabled

    @classmethod
    def new_point(cls, name, description, directions, lat, lon, point_type, water_exists, fire_exists,
                  user_sub, water_comment=None, fire_comment=None, is_disabled=False):
        return cls(name=name, description=description, directions=directions, lat=lat, lon=lon, point_type=point_type,
                   water_exists=water_exists, water_comment=water_comment, fire_exists=fire_exists,
                   fire_comment=fire_comment, is_disabled=is_disabled, created_by=user_sub, last_modified_by=user_sub)

    @classmethod
    def from_dict(cls, body):
        source = body['_source']
        return cls(name=source['name'], description=source['description'], directions=source['directions'],
                   lat=source['location']['lat'], lon=source['location']['lon'], point_type=source['type'],
                   water_exists=source['water_exists'], water_comment=source['water_comment'],
                   fire_exists=source['fire_exists'], fire_comment=source['fire_comment'],
                   created_timestamp=source['created_timestamp'], created_by=source['created_by'],
                   last_modified_timestamp=source['last_modified_timestamp'],
                   last_modified_by=source['last_modified_by'],
                   images=source.get('images'), is_disabled=source.get('is_disabled', False), doc_id=body['_id'])

    def to_dict(self, with_id=False):
        body = {
            "name": self.name,
            "description": self.description,
            "directions": self.directions,
            "location": {
                "lat": self.lat,
                "lon": self.lon
            },
            "type": self.point_type,
            "water_exists": self.water_exists,
            "water_comment": self.water_comment,
            "fire_exists": self.fire_exists,
            "fire_comment": self.fire_comment,
            "is_disabled": self.is_disabled,
            "created_timestamp": self.created_timestamp,
            "last_modified_timestamp": self.last_modified_timestamp,
        }
        if with_id is True:
            body["id"] = self.doc_id
        if self.images is not None:
            body['images'] = list()
            for image in self.images:
                body["images"].append({"name": image['name'], "created_timestamp": image["created_timestamp"]})
        return body

    def to_index(self):
        body = self.to_dict()
        body["created_by"] = self.created_by
        body["last_modified_by"] = self.last_modified_by
        if self.images is not None:
            body['images'] = list()
            for image in self.images:
                body["images"].append({"name": image['name'], "created_timestamp": image["created_timestamp"],
                                       "created_by": image['created_by']})
        return body

    def modify(self, name, description, directions, lat, lon, point_type, water_exists, fire_exists, water_comment,
               fire_comment, is_disabled, user_sub):
        params = locals()
        params.pop('self')
        params.pop('user_sub')
        changed = dict()
        for param in params.keys():
            if type(params[param]) is not NotDefined:
                if getattr(self, param) != params[param]:
                    if param == 'point_type':
                        log_param = 'type'
                    else:
                        log_param = param
                    changed[log_param] = {'old_value': getattr(self, param),
                                          'new_value': params[param]}
                setattr(self, param, params[param])
        self.last_modified_by = user_sub
        self.last_modified_timestamp = datetime.utcnow().strftime("%s")
        return changed


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

    def search_points(self, phrase, point_type=None, top_right=None, bottom_left=None, water=None, fire=None,
                      is_disabled=None):
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
        if point_type not in [None, []]:
            body['query']['bool']['minimum_should_match'] = 1
            for ptype in point_type:
                add_to_or_create_list(location=body['query']['bool'], name='should',
                                      query={"term": {"type": {"value": ptype}}})
        if top_right is not None and bottom_left is not None:
            add_to_or_create_list(location=body['query']['bool'], name='filter', query={
                "geo_bounding_box": {
                    "location": {
                        "top_left": {
                            "lat": str(top_right['lat']),
                            "lon": str(bottom_left['lon'])
                        },
                        "bottom_right": {
                            "lat": str(bottom_left['lat']),
                            "lon": str(top_right['lon'])
                        }
                    }
                }
            }
                                  )
        if water is not None:
            add_to_or_create_list(location=body['query']['bool'], name='filter',
                                  query={"term": {"water_exists": water}})
        if fire is not None:
            add_to_or_create_list(location=body['query']['bool'], name='filter', query={"term": {"fire_exists": fire}})
        if is_disabled is not None:
            add_to_or_create_list(location=body['query']['bool'], name='filter',
                                  query={"term": {"is_disabled": is_disabled}})
        response = self.es.search(index=self.index, body=body)
        read_points = list(map(Point.from_dict, response['hits']['hits']))
        out_points = [point.to_dict(with_id=True) for point in read_points]
        return {'points': out_points}

    def get_points(self, top_right, bottom_left, point_type=None):
        body = {
            "query": {
                "bool": {
                    "must": {
                        "match_all": {}
                    },
                    "filter": [{
                        "geo_bounding_box": {
                            "validation_method": "COERCE",
                            "location": {
                                "top_left": {
                                    "lat": str(top_right['lat']),
                                    "lon": str(bottom_left['lon'])
                                },
                                "bottom_right": {
                                    "lat": str(bottom_left['lat']),
                                    "lon": str(top_right['lon'])
                                }
                            }
                        }
                    }]
                }
            },
            "size": 9000
        }
        if point_type not in [None, []]:
            body['query']['bool']['minimum_should_match'] = 1
            for ptype in point_type:
                add_to_or_create_list(location=body['query']['bool'], name='should',
                                      query={"term": {"type": {"value": ptype}}})
        response = self.es.search(index=self.index, body=body)
        read_points = list(map(Point.from_dict, response['hits']['hits']))
        out_points = [point.to_dict(with_id=True) for point in read_points]
        return {'points': out_points}

    def get_point(self, point_id):
        response = self.es.get(index=self.index, id=point_id)
        point = Point.from_dict(body=response)
        return point.to_dict(with_id=True)

    def get_logs(self, point_id=None, size=25, offset=0):
        body = {"sort": [{"timestamp": {"order": "desc"}}], "from": offset, "size": size}
        if point_id is not None:
            body['query'] = {'term': {'doc_id.keyword': {'value': point_id}}}
        response = self.es.search(index=self.index + '_*', body=body)
        return {"logs": response['hits']['hits'], "total": response['hits']['total']['value']}

    def get_log(self, log_id):
        body = {"query": {"term": {"_id": log_id}}}
        response = self.es.search(index=self.index + '_*', body=body)
        return response['hits']['hits'][0]['_source']

    def modify_point(self, point_id, user_sub, name, description, directions, lat, lon,
                     point_type, water_exists, fire_exists, water_comment, fire_comment, is_disabled):
        body = self.es.get(index=self.index, id=point_id)
        point = Point.from_dict(body=body)
        changes = point.modify(name=name, description=description, directions=directions, lat=lat, lon=lon,
                               point_type=point_type, water_exists=water_exists, water_comment=water_comment,
                               fire_exists=fire_exists, fire_comment=fire_comment, is_disabled=is_disabled,
                               user_sub=user_sub)
        res = self.es.index(index=self.index, id=point_id, body=point.to_index())
        if res['result'] == 'updated':
            self.save_log(user_sub=user_sub, doc_id=point_id, name=point.name, changed=changes)
            return self.get_point(point_id=point_id)
        return res

    def add_point(self, name, description, directions, lat, lon, point_type, user_sub, water_exists, fire_exists,
                  water_comment=None, fire_comment=None, is_disabled=False):
        point = Point.new_point(name=name, description=description, directions=directions, lat=lat,
                                lon=lon, point_type=point_type, water_exists=water_exists, water_comment=water_comment,
                                fire_exists=fire_exists, fire_comment=fire_comment, is_disabled=is_disabled,
                                user_sub=user_sub)
        res = self.es.index(index=self.index, body=point.to_index())
        if res['result'] == 'created':
            self.save_log(user_sub=user_sub, doc_id=res['_id'], name=point.name, changed={"action": "created"})
            return self.get_point(point_id=res['_id'])
        return res

    def delete_point(self, point_id):
        res = self.es.delete(index=self.index, id=point_id)
        if res['result'] == 'deleted':
            return
        raise Exception("Can't delete point")

    def add_image(self, point_id, path, sub):
        body = self.es.get(index=self.index, id=point_id)
        point = Point.from_dict(body=body)
        images = point.images
        if images is None:
            images = []
        new_image = {"name": path, "created_timestamp": datetime.utcnow().strftime("%s"), "created_by": sub}
        images.append(new_image)
        res = self.es.update(index=self.index, id=point_id, body={"doc": {"images": images}})
        if res['result'] == 'updated':
            self.save_log(user_sub=sub, doc_id=point_id, name=point.name, changed={"images": {"old_value": None,
                                                                                   "new_value": path}})
            return self.get_point(point_id=point_id)
        return res

    def delete_image(self, point_id, image_name, sub):
        body = self.es.get(index=self.index, id=point_id)
        point = Point.from_dict(body=body)
        new_images = [image for image in point.images if image['name'] != image_name]
        res = self.es.update(index=self.index, id=point_id, body={"doc": {"images": new_images}})
        if res['result'] == 'updated':
            self.save_log(user_sub=sub, doc_id=point_id, name=point.name, changed={"images": {"old_value": image_name,
                                                                                   "new_value": None}})
            return self.get_point(point_id=point_id)
        return res

    def save_log(self, user_sub, doc_id, name, changed):
        document = {"modified_by": user_sub, "doc_id": doc_id, "changes": changed,
                    "timestamp": datetime.utcnow().strftime("%Y/%m/%d %H:%M:%S"), "name": name}
        self.es.index(index=''.join((self.index, datetime.today().strftime('_%m_%Y'))), body=document)
