from fastapi import FastAPI,Request,Depends
from fastapi.middleware.cors import CORSMiddleware
from app.core.middleware import RateLimiter
from redis.asyncio import Redis
from app.config import settings
from app.routers import auth,notes,notion,oauth2,pdf
from app.db import models
from fastapi.staticfiles import StaticFiles
from app.core.notion_sdk import createNotionDB,createNotionPage
from app.db.database import engine
import logging
from app.password_utils import encryptToken,decryptToken
from app.core.cohereClient import get_embeddings
from app.core.groqClient import categorize_note,enrich_note

from app.db.models import UserAuth,NotionID
from app.utils import Autherize
from app.db.database import get_db
from sqlalchemy.orm import Session
from app.core.qdrantClient import initDataCollection,saveHighlightData,similaritySearchCategory

# models.Base.metadata.create_all(bind=engine,checkfirst=True)  # Tables are created only when they do not exist.


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
    text = "AI is very helpful in today's daily life"
    embedding = get_embeddings(text)
    # category = categorize_note(text)
    # enriched = enrich_note(text)
    # encryptedText = encryptToken(text)
    # decryptedText = decryptToken(encryptedText)
    return {"Message": text, "embeddings": embedding, }#"category": category, "enriched_content": enriched,"texten":encryptedText,"textdec":decryptedText}

@app.get("/createdb")
def create(user : UserAuth = Depends(Autherize), db : Session = Depends(get_db)):
    userid = user.user_id
    notionToken = db.query(NotionID).filter(NotionID.user_id == userid).first()
    print(notionToken.token)
    return createNotionDB(notionToken.token,db,user)
    # return createNotionPage(notionToken.token,user,db,isDefault=True)


@app.get("/add/qdrant")
def dummydata():
    saveHighlightData("The Pomodoro technique helps improve productivity.",1,"productivity","The Pomodoro technique helps improve productivity.")
    saveHighlightData("The Pomodoro technique boosts productivity.",1,"productivity","The Pomodoro technique boosts productivity.")
    saveHighlightData("The Apple ecosystem is well-integrated.",1,"Apple technology","The Apple ecosystem is well-integrated.")
    saveHighlightData("An apple a day keeps the doctor away.",1,"Health","An apple a day keeps the doctor away.")
    saveHighlightData("Creating a morning routine helps productivity.",1,"productivity","Creating a morning routine helps productivity.")

@app.get("/search/qdrant")
def dummydatasrch():
    return similaritySearchCategory("The Pomodoro Technique is a time management method developed by Francesco Cirillo in the late 1980s.",1)