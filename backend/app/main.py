from fastapi import FastAPI,Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import secrets
from app.core.middleware import RateLimiter
from redis.asyncio import Redis
from app.config import settings
from app.routers import auth,notes,notion
from app.db import models
from app.db.database import engine
import logging

models.Base.metadata.create_all(bind=engine,checkfirst=True)  # Tables are created only when they do not exist.

# SERVER_KEY = settings.SERVER_KEY
# SSL_CERTFILE = settings.SSL_CERTFILE

# app = FastAPI(ssl_keyfile = SERVER_KEY ,ssl_certfile= SSL_CERTFILE)
app = FastAPI()
redis = Redis(host="localhost", port=6379, decode_responses=True)

# app.add_middleware(CSRFMiddleware,secret_key=settings.SECRET_KEY)

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"]
)
app.add_middleware(RateLimiter,redis,max_requests=1000, window_seconds=30)


app.include_router(auth.router)

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    handlers=[
        logging.FileHandler('noteify.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@app.get("/")
def root():
    logger.info("Root endpoint accessed")
    return {"Message": "Hello World"}

