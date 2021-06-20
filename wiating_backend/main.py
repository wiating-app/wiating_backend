from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from .image import images
from .logs import logs
from .points import points
from .user_management import user_mgmt

app = FastAPI()
app.include_router(images)
app.include_router(logs)
app.include_router(points)
app.include_router(user_mgmt)

origins = [
    "http://localhost",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware)


@app.get('/healthz')
def healthz():
    return {}
