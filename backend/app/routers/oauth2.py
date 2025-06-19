from app.config import settings
from app.core.notion_sdk import createNotionDB
from app.db.database import get_db
from app.db.models import UserAuth,NotionID
from app.db.schemas import *
from app.password_utils import encryptToken
from app.utils import Autherize
from fastapi import APIRouter,Depends,Response
from fastapi import HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import logging
import requests


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/oauth2",tags=['OAuth2'])



@router.get("/notion")
def notionOauth2Start(user: UserAuth = Depends(Autherize)):
    url = (
        f"https://api.notion.com/v1/oauth/authorize?owner=user"
        f"&client_id={settings.NOTION_CLIENT_ID}"
        f"&redirect_uri={settings.NOTION_REDIRECT_URI}"
        f"&response_type=code"
    )
    return RedirectResponse(url)




@router.get("/notion/callback")
def notionOauth2Callback(code: str = None, db: Session = Depends(get_db),user: UserAuth = Depends(Autherize)):
    
    if not code:
        logger.error("No code provided in Notion OAuth2 callback.")
        raise HTTPException(status_code=400, detail="No code provided.")
    
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.NOTION_REDIRECT_URI,
    }
    
    auth = (settings.NOTION_CLIENT_ID, settings.NOTION_CLIENT_SECRET)
    headers = {"Content-Type": "application/json"}
    response = requests.post("https://api.notion.com/v1/oauth/token", json=data, auth=auth, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get Notion token: {response.text}")
        raise HTTPException(status_code=400, detail="Failed to get Notion token.")
    
    token_data = response.json()
    access_token = token_data.get("access_token")
    
    if not access_token:
        logger.error("No access token in Notion response.")
        raise HTTPException(status_code=400, detail="No access token in Notion response.")
    
    logger.info(f"Token : {access_token}")
    notion_id = db.query(NotionID).filter(NotionID.user_id == user.user_id).first()

    if notion_id:
        encrpyted_token = encryptToken(access_token)
        notion_id.token = encrpyted_token
    
    else:
        encrpyted_token = encryptToken(access_token)
    
        try:
            resp = createNotionDB(access_token,db,user)
        except Exception as e:
            logger.error(e)
            raise HTTPException(status_code=400, detail="Unable to Create Notion DB (token invalid)")
    
        notion_db_id = resp['id']
        notion_id = NotionID(user_id=user.user_id, token=encrpyted_token,database_id=notion_db_id)
        db.add(notion_id)
    
    user.notionConnected = True
    db.commit()
    logger.info(f"Notion connected for user {user.email}")
    return RedirectResponse(url="/pdfjs/notion_success.html")

