from datetime import datetime
from typing import List, Optional

from elasticsearch import Elasticsearch as ES
from pydantic import BaseModel

from .config import DefaultConfig


class Location(BaseModel):
    lat: str
    lon: str


class Image(BaseModel):
    name: str
    created_timestamp: str
    created_by: str


class BasePoint(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    directions: Optional[str] = None
    location: Optional[Location] = None
    type: Optional[str] = None
    water_exists: Optional[bool] = None
    fire_exists: Optional[bool] = None
    water_comment: Optional[str] = None
    fire_comment: Optional[str] = None
    created_timestamp: Optional[str] = None
    created_by: Optional[str] = None
    doc_id: Optional[str] = None
    last_modified_timestamp: Optional[str] = None
    last_modified_by: Optional[str] = None
    images: List[Image] = None
    is_disabled: Optional[bool] = None
    report_reason: Optional[str]
    unpublished: Optional[bool] = None

    @classmethod
    def from_dict(cls, body):
        source = body['_source']
        return cls(name=source['name'], description=source['description'], directions=source['directions'],
                   location=Location(lat=source['location']['lat'], lon=source['location']['lon']), type=source['type'],
                   water_exists=source['water_exists'], water_comment=source['water_comment'],
                   fire_exists=source['fire_exists'], fire_comment=source['fire_comment'],
                   created_timestamp=source['created_timestamp'], created_by=source['created_by'],
                   last_modified_timestamp=source['last_modified_timestamp'],
                   last_modified_by=source['last_modified_by'], images=source.get('images'),
                   is_disabled=source.get('is_disabled', False), report_reason=source.get('report_reason'),
                   unpublished=source.get('unpublished'), doc_id=body['_id'])

    def to_dict(self, with_id=False, moderator=False):
        body = {
            "name": self.name,
            "description": self.description,
            "directions": self.directions,
            "location": {
                "lat": self.location.lat,
                "lon": self.location.lon
            },
            "type": self.type,
            "water_exists": self.water_exists,
            "water_comment": self.water_comment,
            "fire_exists": self.fire_exists,
            "fire_comment": self.fire_comment,
            "is_disabled": self.is_disabled,
            "report_reason": self.report_reason,
            "created_timestamp": self.created_timestamp,
            "last_modified_timestamp": self.last_modified_timestamp,
        }
        if with_id is True:
            body["id"] = self.doc_id
        if moderator is True:
            body["unpublished"] = self.unpublished
        if self.images is not None:
            body['images'] = list()
            for image in self.images:
                body["images"].append({"name": image.name, "created_timestamp": image.created_timestamp})
        return body


class NotDefined:
    pass


class Point:
    def __init__(self, name, description, directions, lat, lon, point_type, created_by, last_modified_by,
                 water_exists=None, fire_exists=None, water_comment=None, fire_comment=None, doc_id=None,
                 created_timestamp=None, last_modified_timestamp=None, images=None, is_disabled=False,
                 report_reason=None, unpublished=None):
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
        self.report_reason = report_reason
        self.unpublished = unpublished

    @classmethod
    def new_point(cls, name, description, directions, lat, lon, point_type, user_sub, water_exists=None,
                  fire_exists=None, water_comment=None, fire_comment=None, is_disabled=False):
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
                   last_modified_by=source['last_modified_by'], images=source.get('images'),
                   is_disabled=source.get('is_disabled', False), report_reason=source.get('report_reason'),
                   unpublished=source.get('unpublished'), doc_id=body['_id'])

    def to_dict(self, with_id=False, moderator=False):
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
            "report_reason": self.report_reason,
            "created_timestamp": self.created_timestamp,
            "last_modified_timestamp": self.last_modified_timestamp,
        }
        if with_id is True:
            body["id"] = self.doc_id
        if moderator is True:
            body["unpublished"] = self.unpublished
        if self.images is not None:
            body['images'] = list()
            for image in self.images:
                body["images"].append({"name": image['name'], "created_timestamp": image["created_timestamp"]})
        return body

    def to_index(self):
        body = self.to_dict()
        body["created_by"] = self.created_by
        body["last_modified_by"] = self.last_modified_by
        body["unpublished"] = self.unpublished
        if self.images is not None:
            body['images'] = list()
            for image in self.images:
                body["images"].append({"name": image['name'], "created_timestamp": image["created_timestamp"],
                                       "created_by": image['created_by']})
        return body

    def modify(self, name, description, directions, lat, lon, point_type, water_exists, fire_exists, water_comment,
               fire_comment, is_disabled, unpublished, user_sub):
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

    def report_reason_append(self, report_reason):
        try:
            self.report_reason.append(report_reason)
        except AttributeError:
            self.report_reason = [report_reason]

    def report_reason_replace(self, report_reason):
        if report_reason is None:
            self.report_reason = None
        else:
            self.report_reason = [report_reason]


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

    @classmethod
    def connection(cls):
        config = DefaultConfig()
        return cls(config.ES_CONNECTION_STRING, index=config.INDEX_NAME)

    def search_points(self, phrase=None, point_type=None, top_right=None, bottom_left=None, water=None, fire=None,
                      is_disabled=None, report_reason=None):
        body = {
            "query": {
                "bool": {
                    "must_not": [{
                        "term": {
                            "unpublished": True
                        }
                    }],
                }
            }
        }
        if phrase is not None:
            add_to_or_create_list(location=body['query']['bool'], name='must',
                                  query={
                                      "multi_match": {
                                          "query": phrase,
                                          "fields": [
                                              "name^3",
                                              "description",
                                              "directions"
                                          ]
                                      }
                                  })
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
                            "lat": str(top_right.lat),
                            "lon": str(bottom_left.lon)
                        },
                        "bottom_right": {
                            "lat": str(bottom_left.lat),
                            "lon": str(top_right.lon)
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
        if report_reason is not None:
            if report_reason:
                add_to_or_create_list(location=body['query']['bool'], name='filter',
                                      query={"exists": {"field": "report_reason"}})
            else:
                add_to_or_create_list(location=body['query']['bool'], name='must_not',
                                      query={"exists": {"field": "report_reason"}})
        response = self.es.search(index=self.index, body=body)
        read_points = list(map(Point.from_dict, response['hits']['hits']))
        out_points = [point.to_dict(with_id=True) for point in read_points]
        return {'points': out_points}

    def get_points(self, top_right: Location, bottom_left: Location, point_type: str=None, is_moderator: bool=False):
        body = {
            "query": {
                "bool": {
                    "filter": [{
                        "geo_bounding_box": {
                            "validation_method": "COERCE",
                            "location": {
                                "top_left": {
                                    "lat": str(top_right.lat),
                                    "lon": str(bottom_left.lon)
                                },
                                "bottom_right": {
                                    "lat": str(bottom_left.lat),
                                    "lon": str(top_right.lon)
                                }
                            }
                        }
                    }]
                }
            },
            "size": 9000
        }
        if not is_moderator:
            add_to_or_create_list(location=body['query']['bool'], name='must_not',
                                  query={"term": {"unpublished": True}})
        if point_type not in [None, []]:
            body['query']['bool']['minimum_should_match'] = 1
            for ptype in point_type:
                add_to_or_create_list(location=body['query']['bool'], name='should',
                                      query={"term": {"type": {"value": ptype}}})
        response = self.es.search(index=self.index, body=body)
        read_points = list(map(Point.from_dict, response['hits']['hits']))
        out_points = [point.to_dict(with_id=True, moderator=is_moderator) for point in read_points]
        return {'points': out_points}

    def get_point(self, point_id, is_moderator=False):
        response = self.es.get(index=self.index, id=point_id)
        point = Point.from_dict(body=response)
        return point.to_dict(with_id=True, moderator=is_moderator)

    def get_unpublished(self, size=25, offset=0):
        body = {
            "query": {
                "term": {
                    "unpublished": True
                }
            },
            "sort":
                [{"last_modified_timestamp": {"order": "desc"}}],
            "from": offset,
            "size": size
        }
        response = self.es.search(index=self.index, body=body)
        read_points = list(map(Point.from_dict, response['hits']['hits']))
        out_points = [point.to_dict(with_id=True) for point in read_points]
        return {'points': out_points}

    def get_user_logs(self, user, size=25, offset=0):
        body = {
            "query": {
                'term': {
                    'modified_by.keyword':
                        {'value': user}
                }
            },
            "sort":
                [{"timestamp": {"order": "desc"}}],
            "from": offset,
            "size": size
        }
        response = self.es.search(index=self.index + '_*', body=body)
        return {"logs": response['hits']['hits'], "total": response['hits']['total']['value']}

    def get_logs(self, point_id=None, size=25, offset=0, reviewed_at=None):
        body = {"query": {"bool": {}}, "sort": [{"timestamp": {"order": "desc"}}], "from": offset, "size": size}
        if point_id is not None:
            add_to_or_create_list(location=body['query']['bool'], name='filter',
                                  query={'term': {'doc_id.keyword': {'value': point_id}}})
        if reviewed_at is not None:
            if reviewed_at:
                add_to_or_create_list(location=body['query']['bool'], name='filter',
                                      query={"exists": {"field": "reviewed_at"}})
            else:
                add_to_or_create_list(location=body['query']['bool'], name='must_not',
                                      query={"exists": {"field": "reviewed_at"}})
        response = self.es.search(index=self.index + '_*', body=body)
        return {"logs": response['hits']['hits'], "total": response['hits']['total']['value']}
    
    def get_user_wrapped(self, user):
        year = str(datetime.today().year-1)
        index = self.index + '_*_' + year
        body = {
            "aggs":{
                "all_modifications":{
                    "terms":{
                        "field":"modified_by.keyword",
                        "size": 1000
                    }
                },
                "user":{
                    "filter": {
                        "term": {
                            "modified_by.keyword": "google-oauth2|115007072642438483707"
                        }
                    },
                    "aggs":{
                        "created":{
                            "filter": {
                                "term":{
                                    "changes.action": "created"
                                },
                            },
                            "aggs": {
                                "created_agg":{
                                    "terms": {
                                        "field": "changes"
                                    }
                                }
                            }
                        },
                        "image":{
                            "filter": {
                                "exists":{
                                    "field": "changes.images.new_value"
                                },
                            },
                            "aggs": {
                                "edit_agg":{
                                    "terms": {
                                        "field": "changes"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "size": 0
        }
        response = self.es.search(index=index, body=body)
        try:
            user_total = response["aggregations"]["user"]["doc_count"]
            user_created = response["aggregations"]["user"]["created"]["doc_count"]
            user_images = response["aggregations"]["user"]["image"]["doc_count"]
            user_edits = user_total - user_created - user_images
            all_modifications = response["aggregations"]["all_modifications"]["buckets"]
            for user_stats in zip(range(0, len(all_modifications)), all_modifications):
                if user_stats[1]["key"] == user:
                    activity_percentage = 100.0 - user_stats[0]/len(all_modifications)
                    break
            return {
                "user_total": user_total,
                "user_created": user_created,
                "user_images": user_images,
                "user_edits": user_edits,
                "activity_percentage": activity_percentage,
                "year": year
            }
        except KeyError:
            return None

    def _get_raw_log(self, log_id):
        body = {"query": {"term": {"_id": log_id}}}
        response = self.es.search(index=self.index + '_*', body=body)
        return response

    def get_log(self, log_id):
        response = self._get_raw_log(log_id)
        return response['hits']['hits'][0]['_source']

    def log_reviewed(self, log_id, user):
        raw_log = self._get_raw_log(log_id=log_id)
        log_index = raw_log['hits']['hits'][0]['_index']
        body = {"doc": {"reviewed_at": datetime.utcnow().strftime("%Y/%m/%d %H:%M:%S"),
                        "reviewed_by": user}}
        response = self.es.update(index=log_index, id=log_id, body=body, _source=True)
        if response['result'] == 'updated':
            return response['get']['_source']
        return False

    def modify_point(self, point_id, user_sub, name, description, directions, lat, lon,
                     point_type, water_exists, fire_exists, water_comment, fire_comment, is_disabled, unpublished,
                     is_moderator=False):
        body = self.es.get(index=self.index, id=point_id)
        point = Point.from_dict(body=body)
        changes = point.modify(name=name, description=description, directions=directions, lat=lat, lon=lon,
                               point_type=point_type, water_exists=water_exists, water_comment=water_comment,
                               fire_exists=fire_exists, fire_comment=fire_comment, is_disabled=is_disabled,
                               unpublished=unpublished, user_sub=user_sub)
        res = self.es.index(index=self.index, id=point_id, body=point.to_index())
        if res['result'] == 'updated':
            if changes != {}:
                self.save_log(user_sub=user_sub, doc_id=point_id, name=point.name, changed=changes)
            return self.get_point(point_id=point_id, is_moderator=is_moderator)
        return res

    def report_moderator(self, point_id, report_reason):
        body = self.es.get(index=self.index, id=point_id)
        point = Point.from_dict(body=body)
        point.report_reason_replace(report_reason=report_reason)
        res = self.es.index(index=self.index, id=point_id, body=point.to_index())
        if res['result'] == 'updated':
            return True

    def report_regular(self, point_id, report_reason):
        body = self.es.get(index=self.index, id=point_id)
        point = Point.from_dict(body=body)
        point.report_reason_append(report_reason=report_reason)
        res = self.es.index(index=self.index, id=point_id, body=point.to_index())
        if res['result'] == 'updated':
            return True

    def add_point(self, name, description, directions, lat, lon, type, user_sub, water_exists=None,
                  fire_exists=None, water_comment=None, fire_comment=None, is_disabled=False, is_moderator=False):
        point = Point.new_point(name=name, description=description, directions=directions, lat=lat,
                                lon=lon, point_type=type, water_exists=water_exists, water_comment=water_comment,
                                fire_exists=fire_exists, fire_comment=fire_comment, is_disabled=is_disabled,
                                user_sub=user_sub)
        res = self.es.index(index=self.index, body=point.to_index())
        if res['result'] == 'created':
            self.save_log(user_sub=user_sub, doc_id=res['_id'], name=point.name, changed={"action": "created"})
            return self.get_point(point_id=res['_id'], is_moderator=is_moderator)
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
