from fastapi import APIRouter, Depends, HTTPException

from .auth import require_auth, require_moderator
from .elastic import Elasticsearch


logs = APIRouter()


@logs.get('/get_user_logs')
def get_user_logs(size: int = 25, offset: int = 0, es: dict = Depends(Elasticsearch.connection),
                  user: dict = Depends(require_auth)):
    return es.get_user_logs(user=user['sub'], size=size, offset=offset)


@logs.get('/get_logs', dependencies=[Depends(require_moderator)])
def get_logs(size: int = 25, offset: int = 0, reviewed_at: bool = None, es: dict = Depends(Elasticsearch.connection)):
    return es.get_logs(size=size, offset=offset, reviewed_at=reviewed_at)


@logs.get('/get_logs/{point_id}', dependencies=[Depends(require_moderator)])
def get_logs_point(point_id: str, size: int = 25, offset: int = 0, reviewed_at: bool = None,
             es: dict = Depends(Elasticsearch.connection)):
    return es.get_logs(point_id=point_id, size=size, offset=offset, reviewed_at=reviewed_at)


@logs.get('/get_log/{log_id}')
def get_log(log_id: str, user: dict = Depends(require_auth), es: dict = Depends(Elasticsearch.connection)):
    try:
        if user.get('is_moderator'):
            return es.get_log(log_id=log_id)
        else:
            log = es.get_log(log_id=log_id)
            if log['modified_by'] == user['sub']:
                return log
            else:
                raise HTTPException(status_code=403)
    except IndexError:
        raise HTTPException(detail="Log not found", status_code=404)
    except AttributeError:
        raise HTTPException(status_code=400, detail="Log ID required")


@logs.post('/log_reviewed/{log_id}')
def log_reviewed(log_id: str, user: dict = Depends(require_moderator), es: dict = Depends(Elasticsearch.connection)):
    try:
        result = es.log_reviewed(log_id, user['sub'])
        if result:
            return result
        else:
            raise HTTPException(status_code=500, detail="Database error")
    except (KeyError, IndexError):
        raise HTTPException(status_code=400, detail="Existing log ID required")


@logs.get('/wrapped/')
def wrapped(user: dict = Depends(require_auth), es: dict = Depends(Elasticsearch.connection)):
    if user is None:
        raise HTTPException(status_code=401)
    return es.get_user_wrapped(user=user['sub'])