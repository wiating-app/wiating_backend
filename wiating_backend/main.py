from typing import Optional

from fastapi import FastAPI

from .points import points

app = FastAPI()
app.include_router(points)

@app.get('/healthz')
def healthz():
    return {}


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Optional[str] = None):
    return {"item_id": item_id, "q": q}

