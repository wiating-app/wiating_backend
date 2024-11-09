from wiating_backend.config import DefaultConfig
from .image import images
from .logs import logs
from .points import points
from .user_management import user_mgmt

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from keycloak import KeycloakOpenID


keycloak_openid = KeycloakOpenID(server_url="http://keycloak:8080/",
                                 client_id="wiating",
                                 realm_name="wiating",
                                 client_secret_key=DefaultConfig().keycloak_secret_key)

config_well_known = keycloak_openid.well_known()


app = FastAPI()


app.include_router(images)
app.include_router(logs)
app.include_router(points)
app.include_router(user_mgmt)
app.mount("/images", StaticFiles(directory="/images"), name="images")

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


@app.post('/login')
def login(username: str, password: str):
    try:
        token = keycloak_openid.token(username, password)
        return token
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get('/choose_identity_provider')
def choose_identity_provider():
    redirect_url = keycloak_openid.auth_url(redirect_uri="http://localhost:3000/")
    return RedirectResponse(url=redirect_url)


@app.post('/token')
def token(code: str = Form(...)):
    try:
        token = keycloak_openid.token(grant_type='authorization_code', code=code, redirect_uri="http://localhost:3000/")
        return token
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))