from fastapi import APIRouter,Depends,Response
from fastapi.responses import JSONResponse
from fastapi import status, HTTPException
from app.db.models import UserAuth,UserCategories,NotionBlock,NotionID,NotionPage,Preferences
from app.db.database import get_db
from sqlalchemy.orm import Session
from app.utils import Autherize,normalizeCategoryName, getNotionToken
from app.db.schemas import *
from app.config import settings
import logging
from app.core.groqClient import categorize_note
from app.core.notion_sdk import createNotionPage,createCategoryPageNotion,createNotionBlock
import json
from app.core.qdrantClient import saveHighlightData,similarityDataSearch,qdrant_client,similaritySearchCategory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notes",tags=['Notes'])
# redisClient = Redis(host="localhost", port=6379, decode_responses=True)
db_id = None


categories = ['AI',"Machine Learning","Technology"]


@router.get("/categories")
def getUserCategories(user: UserAuth = Depends(Autherize), db: Session = Depends(get_db)):

    categories = db.query(UserCategories).filter(UserCategories.user_id == user.user_id).all()
    
    return JSONResponse({
        "categories": [cat.category_name for cat in categories]
    }, status_code=status.HTTP_200_OK)





@router.post("/category")
def categoryPredict(data : Notes,user : UserAuth = Depends(Autherize)):

    print(len(data.text))

    if len(data.text) < 30:
        return JSONResponse({
            "detail":"Highlighted text too short to be noteworthy."
        },status_code=status.HTTP_400_BAD_REQUEST)

    if len(data.text) > 2000:
        return JSONResponse({
            "detail":"Text too long (NOTION DOESNT SUPPORT ADDING TOO LONG SENTENCES)"
        },status_code=status.HTTP_400_BAD_REQUEST)

    initialCat = similaritySearchCategory(data.text,user.user_id)

    if initialCat:
        result = {
            "text": data.text,
            "categories": {
                initialCat[0].payload['category']: 1.0  # score is artificial here
            }
        }
    
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
    info = db.query(NotionID).filter(NotionID.user_id == user.user_id).first()
    notion_db_id = info.database_id
    token = getNotionToken(user,db)

    try:
        response = createCategoryPageNotion(token,notion_db_id,category,db,user)
        new_category = UserCategories(user_id = user_id, category_name=category)
        db.add(new_category)
        db.commit()

    except Exception as e:
        return e
    
    logger.info(f"Successfully created category {category} for user {user_id}")
    
    return JSONResponse(
        {
            "detail":f"Category {category} created successfully"
        },
        status_code=status.HTTP_201_CREATED
    )






@router.post("/create/raw")
def createNotesRaw(data : Notes, user : UserAuth = Depends(Autherize),db : Session = Depends(get_db)):
    
    logger.info("Trying to get user preference")
    preference = user.preference.value
    logger.info(f"Found preference for user {user.user_id} to be {preference}")
    
    token = getNotionToken(user,db)

    page_id = None

    if preference == Preferences.RAW.value:
        
        exists = db.query(NotionPage).filter(NotionPage.user_id == user.user_id).filter(NotionPage.title == "Noteify_Miscellaneous").first()
        if not exists:
            try:
                resp = createNotionPage(token,user,db,title="Noteify_Miscellaneous")
                page_id = resp.notion_page_id
            except Exception as e:
                return e
        
        if not page_id:
            page_id = exists.notion_page_id

        try:
            resp = createNotionBlock(token,page_id,data.text,str(data.destination))
        except Exception as e:
            raise HTTPException(500,detail=e)

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
    database_id = db.query(NotionID).filter(NotionID.user_id == user.user_id).first().database_id
    
    category = normalizeCategoryName(data.category)
    
    exist = db.query(NotionPage).filter(NotionPage.user_id == user.user_id).filter(NotionPage.title == category).first()
    page_id = None
    
    if not exist:
        try:
            logger.info(f"Page Not found , Creating new page with title {category}")
            response = createCategoryPageNotion(token,database_id,category,db,user)

            page_id = response.notion_page_id
            ref_id = response.references_block_id
            note_block_id = response.notes_block_id

            

            cat = UserCategories(user_id = user.user_id, category_name=category)
            
            db.add(cat)
            db.commit()
        except Exception as e:
            return e
    

    if not page_id:
        logger.info(f"Page found of category {category} for user {user.user_id}, extracting page_id")
        info = db.query(NotionPage).filter(NotionPage.user_id == user.user_id).filter(NotionPage.title == category).first()
        page_id = info.notion_page_id
        ref_id = info.references_block_id
        note_block_id = info.notes_block_id


    logger.info(f"ID's found : {page_id} {ref_id} {note_block_id}")

    if preference == Preferences.CATEGORIZED_AND_RAW.value:
        try:
            # print(token)
            # print(note_block_id)
            # print(ref_id)
            # print(data.text)
            # print(data.destination)
            resp = createNotionBlock(token,page_id,data.text,str(data.destination))
            # print(resp)
        except Exception as e:
            raise HTTPException(500,detail=e)
        
        return JSONResponse(
            {
                "message":"Noted to Notion",
                "category":data.category
            },status_code=status.HTTP_200_OK
        )
    
    if preference == Preferences.CATEGORIZED_AND_ENRICHED.value:
        
        return JSONResponse(
            {
                "message":"Noted to Notion",
                "category":data.category
            },status_code=status.HTTP_200_OK
        )
    



