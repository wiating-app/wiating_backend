from typing import List, Optional, Union

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from .auth import allow_auth, require_auth, require_moderator
from .elastic import BasePoint, Elasticsearch, Location
from .image import delete_image_directory
from .logging import logger


points = APIRouter()


@points.post('/get_points')
def get_points(top_right: Location, bottom_left: Location, point_type: Optional[List[str]] = None,
               es: dict = Depends(Elasticsearch.connection), user: dict = Depends(allow_auth)):
    if user is not None and user.get('is_moderator'):
        return es.get_points(top_right, bottom_left, point_type, is_moderator=True)
    return es.get_points(top_right, bottom_left, point_type)


@points.get('/get_point/{point_id}')
def get_point(point_id: str, es: dict = Depends(Elasticsearch.connection), user: dict = Depends(allow_auth)):
    if user is not None and user.get('is_moderator'):
        return es.get_point(point_id=point_id, is_moderator=True)
    return es.get_point(point_id=point_id)


@points.post('/add_point')
def add_point(point: BasePoint, es: dict = Depends(Elasticsearch.connection), user: dict = Depends(require_auth)):
    return es.add_point(name=point.name, description=point.description, directions=point.directions,
                        lat=point.location.lat, lon=point.location.lon, type=point.type,
                        water_exists=point.water_exists, water_comment=point.water_comment,
                        fire_exists=point.fire_exists, fire_comment=point.fire_comment,
                        is_disabled=point.is_disabled, user_sub=user['sub'], is_moderator=user['is_moderator'])


@points.put('/modify_point/{point_id}')
def modify_point(point_id: str, point: BasePoint, es: dict = Depends(Elasticsearch.connection),
                 user: dict = Depends(require_auth)):
    logger.info('modify_point')
    sub = user['sub']
    is_moderator = user['is_moderator']
    if is_moderator:
        return es.modify_point(point_id=point_id, name=point.name, description=point.description,
                               directions=point.directions, lat=str(point.location.lat), lon=str(point.location.lon),
                               point_type=point.type, water_exists=point.water_exists,
                               water_comment=point.water_comment, fire_exists=point.fire_exists,
                               fire_comment=point.fire_comment, is_disabled=point.is_disabled,
                               unpublished=point.unpublished, user_sub=sub, is_moderator=is_moderator)
    else:
        return es.modify_point(point_id=point_id, name=point.name, description=point.description,
                               directions=point.directions, lat=str(point.location.lat), lon=str(point.location.lon),
                               point_type=point.type, water_exists=point.water_exists,
                               water_comment=point.water_comment, fire_exists=point.fire_exists,
                               fire_comment=point.fire_comment, is_disabled=point.is_disabled, unpublished=None,
                               user_sub=sub, is_moderator=is_moderator)


class SearchQuery(BaseModel):
    phrase: Optional[str] = None
    point_type: Optional[List[str]] = None
    top_right: Optional[Location]
    bottom_left: Optional[Location]
    water: Optional[bool]
    fire: Optional[bool]
    is_disabled: Optional[bool]
    report_reason: Optional[bool]


@points.post('/search_points')
def search_points(search_query: SearchQuery, es: dict = Depends(Elasticsearch.connection)):
    """
    It takes search parameters from JSON data.
    Result contains items with non-empty `report_reason` only if `report_reason` is set True, if False it returns items
    without `report_reason`, if not set returns both.
    :return:
    """
    return es.search_points(phrase=search_query.phrase, point_type=search_query.point_type,
                            top_right=search_query.top_right, bottom_left=search_query.bottom_left,
                            water=search_query.water, fire=search_query.fire, is_disabled=search_query.is_disabled,
                            report_reason=search_query.report_reason)


@points.delete('/delete_point/{point_id}')
def delete_point(point_id: str, es: dict = Depends(Elasticsearch.connection), user: dict = Depends(require_moderator)):
    es.delete_point(point_id=point_id)
    delete_image_directory(point_id)
    return {"status": "deleted"}


class Report(BaseModel):
    report_reason: Union[None, str]


@points.post('/report/{point_id}')
def report(point_id: str, report: Report, es: dict = Depends(Elasticsearch.connection), user: dict = Depends(require_auth)):
    try:
        if user.get('is_moderator'):
            if es.report_moderator(point_id, report.report_reason):
                return
        else:
            if es.report_regular(point_id, report.report_reason):
                return
        raise HTTPException(status_code=503)
    except AttributeError:
        raise HTTPException(status_code=400, detail="Report reason and location ID required")


@points.get('/get_unpublished', dependencies=[Depends(require_moderator)])
def get_unpublished(size: int = 25, offset: int = 0, es: dict = Depends(Elasticsearch.connection)):
    return es.get_unpublished(size=size, offset=offset)
