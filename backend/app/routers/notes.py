from fastapi import APIRouter,Depends,Response
from fastapi.responses import JSONResponse
from fastapi import status, HTTPException
from app.db.models import UserAuth,UserCategories,NotionBlock,NotionID,NotionPage,Preferences
from app.db.database import get_db
from sqlalchemy.orm import Session
from app.utils import Autherize,normalizeCategoryName, getNotionToken,getCategoryCacheKey
from app.db.schemas import *
from app.config import settings
import logging
from app.core.groqClient import categorize_note
from app.core.notion_sdk import createNotionPage
import json
from app.core.qdrantClient import saveHighlightData,similarityDataSearch,qdrant_client,similaritySearchCategory
from redis import Redis

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notes",tags=['Notes'])
redisClient = Redis(host="localhost", port=6379, decode_responses=True)



categories = ['AI',"Machine Learning","Technology"]

@router.post("/category")
def categoryPredict(data : Notes,user : UserAuth = Depends(Autherize)):
    initialCat = similaritySearchCategory(data.text,user.user_id)
    # key = getCategoryCacheKey(user.user_id)
    if initialCat:
        result = {
            "text": data.text,
            "categories": {
                initialCat[0].payload['category']: 1.0  # score is artificial here
            }
        }
        # redisClient.setex(key, 3000, result) 
        return JSONResponse({
            "category":initialCat[0].payload['category']
        })
    
    category_json = json.loads(categorize_note(data.text))
    category_found = None

    result = {
        "text": data.text,
        "categories": category_json
    }

    mx_score = 0
    for category in category_json:
        if category_json[category] > mx_score:
            mx_score = category_json[category]
            category_found = category

    # redisClient.setex(key, 3000, json.dumps(result))

    return JSONResponse(
        {
            "category":category_found
        }
    ,status_code=status.HTTP_200_OK)


@router.post("/create/category")
def createCategory(data : Category, user : UserAuth = Depends(Autherize), db : Session = Depends(get_db)):
    logger.info(f"Attempting to create category: {data.category} for user: {user.user_id}")
    category = normalizeCategoryName(data.category)
    print(category)
    user_id = user.user_id
    exist = db.query(UserCategories).filter(UserCategories.user_id == user_id).filter(UserCategories.category_name == category).first()
    
    if exist:
        logger.warning(f"Category {category} already exists for user {user_id}")
        return JSONResponse({
                "detail":"Category already exists"
                }
                ,status_code=status.HTTP_409_CONFLICT
            )

    new_category = UserCategories(user_id = user_id, category_name=category)
    db.add(new_category)
    db.commit()
    logger.info(f"Successfully created category {category} for user {user_id}")
    return JSONResponse(
        {
            "detail":f"Category {category} created successfully"
        },
        status_code=status.HTTP_201_CREATED
    )



@router.post("/create/raw")
def createNotes(data : Notes, user : UserAuth = Depends(Autherize),db : Session = Depends(get_db)):
    
    logger.info("Trying to get user preference")
    preference = user.preference.value
    logger.info(f"Found preference for user {user.user_id} to be {preference}")
    
    token = getNotionToken(user,db)

    if preference == Preferences.RAW.value:
        exists = db.query(NotionPage).filter(NotionPage.user_id == user.user_id).filter(NotionPage.title == "Noteify_Miscellaneous").first()
        if not exists:
            try:
                resp = createNotionPage(token,user,db,title="Noteify_Miscellaneous")
            except Exception as e:
                return e
        return JSONResponse(
            {
                "message":"Added to Notion",
            },
            status_code=status.HTTP_201_CREATED
        )    
        
    
@router.post("/create")
def createNotes(data : CategoryNotes, user : UserAuth = Depends(Autherize),db : Session = Depends(get_db)):
    
    logger.info("Trying to get user preference")
    preference = user.preference.value
    logger.info(f"Found preference for user {user.user_id} to be {preference}")
    
    token = getNotionToken(user,db)

    # print(data.category)
    # print(data.text)

    if preference == Preferences.CATEGORIZED_AND_RAW.value:
        # jsonData = json.loads(cachedData)
        # text = jsonData.text
        return JSONResponse(
            {
                # "message":data.text,
                "message":"Noted to Notion",
                "category":data.category
            },status_code=status.HTTP_200_OK
        )
    
    if preference == Preferences.CATEGORIZED_AND_ENRICHED.value:
        # jsonData = json.loads(cachedData)
        # text = jsonData.text
        return JSONResponse(
            {
                # "message":data.text,
                "message":"Noted to Notion",
                "category":data.category
            },status_code=status.HTTP_200_OK
        )