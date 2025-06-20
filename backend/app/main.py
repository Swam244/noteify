from app.core.middleware import RateLimiter
from app.core.qdrantClient import initDataCollection
from app.routers import auth,notes,oauth2,pdf,images
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from redis.asyncio import Redis
import logging

# Base.metadata.create_all(bind=engine,checkfirst=True)  # Tables are created only when they do not exist.

app = FastAPI()
app.mount("/pdfjs", StaticFiles(directory="static/pdfjs"), name="pdfjs")    
initDataCollection()
redisClient = Redis(host="localhost", port=6379, decode_responses=True)


app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"]
)
app.add_middleware(RateLimiter,redisClient,max_requests=1000, window_seconds=30)



app.include_router(auth.router)
app.include_router(oauth2.router)
app.include_router(notes.router)
app.include_router(pdf.router)
app.include_router(images.router)



logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    handlers=[
        logging.FileHandler('noteify.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)



@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": str(exc.detail)},
    )
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc)},
    )
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )



@app.get("/")
def root():
    logger.info("Root endpoint accessed")
    text = "Hello from noteify !!"

    return {"Message": text}
