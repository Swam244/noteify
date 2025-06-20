from app.core.groqClient import categorize_note,enrich_note,handleCode
from app.core.notion_sdk import createNotionPage,createCategoryPageNotion,createNotionBlock,createImageBlockNotion
from app.core.qdrantClient import saveHighlightData,similarityDataSearch,similaritySearchCategory
from app.core.s3_handler import uploadImage
from app.db.models import UserAuth,UserCategories,NotionID,NotionPage,Preferences
from app.db.database import get_db
from app.db.schemas import *
from app.utils import Autherize,getNotionToken,validateCodeLanguage
from fastapi import APIRouter,Depends,UploadFile, File,BackgroundTasks, Form
from fastapi.responses import JSONResponse
from fastapi import status, HTTPException
from redis import Redis
from sqlalchemy.orm import Session
from pathlib import Path
import uuid
import logging
import json
import secrets
import os


logger = logging.getLogger(__name__)

redisClient = Redis(host="localhost", port=6379, decode_responses=True)

router = APIRouter(prefix="/notes",tags=['Notes'])


@router.get("/categories")
def getUserCategories(user: UserAuth = Depends(Autherize), db: Session = Depends(get_db)):
    logger.info(f"Fetching categories for user: {user.user_id}")
    categories = db.query(UserCategories).filter(UserCategories.user_id == user.user_id).all()
    logger.info(f"Found {len(categories)} categories for user: {user.user_id}")
    return JSONResponse({
        "categories": [cat.category_name for cat in categories]
    }, status_code=status.HTTP_200_OK)





@router.post("/category")
def categoryPredict(data : Notes,user : UserAuth = Depends(Autherize),db : Session = Depends(get_db)):
    logger.info(f"Predicting category for user: {user.user_id}, text length: {len(data.text)}")
    
    if len(data.text) < 30:
        logger.warning("Highlighted text too short to be noteworthy.")
        return JSONResponse({
            "detail":"Highlighted text too short to be noteworthy."
        },status_code=status.HTTP_400_BAD_REQUEST)
    
    if len(data.text) > 2000:
        logger.warning("Text too long (NOTION DOESNT SUPPORT ADDING TOO LONG SENTENCES)")
        return JSONResponse({
            "detail":"Text too long (NOTION DOESNT SUPPORT ADDING TOO LONG SENTENCES)"
        },status_code=status.HTTP_400_BAD_REQUEST)

    initialCat = similaritySearchCategory(data.text,user.user_id)
    token = secrets.token_urlsafe(24)

    if initialCat:
        logger.info(f"Initial category found for user: {user.user_id}")
        result = {
            "text": data.text,
            "categories": {
                initialCat[0].payload['category']: 1.0  # score is artificial here
            }
        }
        
        try:
            category_json = initialCat[0].payload['llm_predictions']
            cache_key_category = f"category_{user.user_id}_{token}"
            print(category_json)
            print(type(category_json))
            redisClient.setex(cache_key_category, 60, json.dumps(category_json))
        
        except Exception as e:
            print(e)
            return e
        
        return JSONResponse({
            "category":initialCat[0].payload['category'],
            "token":token
        })
    
    category_found = None
    
    try:
        category_preds = categorize_note(user,db,data.text)
        category_json = json.loads(category_preds)
        print(type(category_preds))
        cache_key_category = f"category_{user.user_id}_{token}"
        redisClient.setex(cache_key_category,60,category_preds)

    except Exception as e:
        print(e)
        return e

    try:
        mx_score = 0
        for category in category_json:
            if category_json[category] > mx_score:
                mx_score = category_json[category]
                category_found = category
                
        logger.info(f"Predicted category: {category_found} for user: {user.user_id}")
        return JSONResponse(
            {
                "category":category_found,
                "token":token
            }
        ,status_code=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error predicting category: {str(e)}")
        return JSONResponse({"detail": f"Error predicting category: {str(e)}"}, status_code=500)






@router.post("/create/category")
def createCategory(data : Category, user : UserAuth = Depends(Autherize), db : Session = Depends(get_db)):
    logger.info(f"Attempting to create category: {data.category} for user: {user.user_id}")
    category = data.category.upper()
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

    if len(data.text) < 30:
        return JSONResponse({
            "detail":"Highlighted text too short to be noteworthy."
        },status_code=status.HTTP_400_BAD_REQUEST)

    if len(data.text) > 2000:
        return JSONResponse({
            "detail":"Text too long (NOTION DOESNT SUPPORT ADDING TOO LONG SENTENCES)"
        },status_code=status.HTTP_400_BAD_REQUEST)

    
    token = getNotionToken(user,db)

    page_id = None

    if preference == Preferences.RAW.value:
        email = user.email.split('@')[0]
        title = "Noteify_RAW_"+"{}".format(email)
        print(title)
        exists = db.query(NotionPage).filter(NotionPage.user_id == user.user_id).filter(NotionPage.title == title).first()
        if not exists:

            try:
                resp = createNotionPage(token,user,db,title=title)
                page_id = resp.notion_page_id
            except Exception as e:
                return e
        
        if not page_id:
            page_id = exists.notion_page_id

        try:
            resp = createNotionBlock(token,page_id,data.text,str(data.destination),False)
        except Exception as e:
            print(e)
            raise HTTPException(500,detail=e)

        return JSONResponse(
            {
                "message":"Added to Notion",
            },
            status_code=status.HTTP_201_CREATED
        )    
        

    
@router.post("/create/image")
def create_image(category: str = Form(...), file: UploadFile = File(...),db: Session = Depends(get_db),user : UserAuth = Depends(Autherize)):
    
    logger.info(f"Received image upload request for user {user.user_id} and {file.filename}")
    images_dir = Path("static/images")
    images_dir.mkdir(parents=True, exist_ok=True)
    temp_filename = str(uuid.uuid4()).replace("-", "")[:24]
    file_path = images_dir / temp_filename
    token = getNotionToken(user,db)

    try:
        content = file.file.read()
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        logger.info(f"Image saved temporarily at: {file_path}")
        upload_result = uploadImage(str(file_path), temp_filename, db, user)
        
        try:
            os.remove(file_path)
        except Exception as cleanup_err:
            logger.warning(f"Could not remove temp file {file_path}: {cleanup_err}")
        
        if not upload_result["success"]:
            logger.error(f"Upload to Appwrite failed: {upload_result.get('error')}")
            raise HTTPException(status_code=500, detail=f"Failed to upload image: {upload_result.get('error')}")
        
        print(upload_result["urls"]["view_url"])
        page_id = None
        database_id = db.query(NotionID).filter(NotionID.user_id == user.user_id).first().database_id
        category = category.upper
        exist = db.query(NotionPage).filter(NotionPage.user_id == user.user_id).filter(NotionPage.title == category).first()
        
        if not exist:
            try:
                logger.info(f"Page Not found , Creating new page with title {category}")
                response = createCategoryPageNotion(token,database_id,category,db,user)
                page_id = response.notion_page_id
                cat = UserCategories(user_id = user.user_id, category_name=category)
                db.add(cat)
                db.commit()
        
            except Exception as e:
                return e
        
        if not page_id:
            logger.info(f"Page found of category {category} for user {user.user_id}, extracting page_id")
            page_id = exist.notion_page_id
        
        try:
            resp = createImageBlockNotion(token,page_id,upload_result["urls"]["view_url"])
            print(resp)
            logger.info("Successfully created code block in Notion")
        
        except Exception as e:
            logger.error(f"Failed to create code block in Notion: {str(e)}")
            raise HTTPException(500,detail=e)



        return JSONResponse({
            "detail": "Image uploaded successfully!",
            "filename": file.filename,
            "saved_as": temp_filename,
            "image_link": upload_result["urls"]["view_url"]
        }, status_code=status.HTTP_201_CREATED)
    
    
    except Exception as e:
        logger.error(f"Error saving/uploading image: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to save/upload image: {str(e)}")
    

    finally:
        file.file.close()



@router.post("/create")
def createNotesCategorize(data : CategoryNotes,background_tasks : BackgroundTasks ,user : UserAuth = Depends(Autherize),db : Session = Depends(get_db)):

    exists = similarityDataSearch(data.text,user.user_id)
    
    if exists:
        return JSONResponse(
                {
                    "message":"Note Already found in page: {0} with {1} % Similarity".format(exists['payload']['category'],float(exists['score'])*100),
                    "category":data.category
                },status_code=status.HTTP_200_OK
            )

    
    token = getNotionToken(user,db)
    database_id = db.query(NotionID).filter(NotionID.user_id == user.user_id).first().database_id
    
    category = data.category.upper()
    
    exist = db.query(NotionPage).filter(NotionPage.user_id == user.user_id).filter(NotionPage.title == category).first()
    page_id = None
    
    code = data.checked

    # REDIS STUFF
    try:
        redis_token = data.token    
        logger.info(f"Token found in request for user {user.user_id} with value {redis_token}")
        key = f"category_{user.user_id}_{redis_token}"
        raw_preds = redisClient.get(key) # String
        logger.info(f"Raw preds from cache :- {raw_preds} {type(raw_preds)}")
        llm_predictions = json.loads(raw_preds) # Dictionary
        logger.info(f"json converted preds :- {llm_predictions}  {type(llm_predictions)}")    
        llm_top1 = None
        print(type(llm_predictions))
        redisClient.delete(key)
        mx_score = 0
        for cat in llm_predictions:
            score = float(llm_predictions[cat])
            if score > mx_score:
                mx_score = score
                llm_top1 = cat

        llm_top1 = llm_top1.upper()
        
    except Exception as e:
        logger.info(f"Error :- {e}")
        return e
    
    if not exist:
        try:
            logger.info(f"Page Not found , Creating new page with title {category}")
            response = createCategoryPageNotion(token,database_id,category,db,user)

            page_id = response.notion_page_id
            cat = UserCategories(user_id = user.user_id, category_name=category)
            
            db.add(cat)
            db.commit()
        except Exception as e:
            return e
    

    if not page_id:
        logger.info(f"Page found of category {category} for user {user.user_id}, extracting page_id")
        page_id = exist.notion_page_id


    logger.info(f"Page ID found : {page_id}")
    text = data.text

    if code:
    
        logger.info("Code detection requested, calling handleCode")
        code_res = handleCode(data.text)
        is_real_code = code_res['code']
        logger.info(f"Code detection result: is_real_code={is_real_code}")

        if is_real_code:
    
            logger.info("Real code detected, processing code block")
            code_text = code_res['code_content']
            code_language = code_res['code_language']
            logger.info(f"Code language detected: {code_language}")

            code_language = validateCodeLanguage(code_language)

            try:
                resp = createNotionBlock(token,page_id,code_text,str(data.destination),True,code_language)
                logger.info("Successfully created code block in Notion")
            except Exception as e:
                logger.error(f"Failed to create code block in Notion: {str(e)}")
                raise HTTPException(500,detail=e)

            background_tasks.add_task(saveHighlightData,data.text, user.user_id,category,resp,page_id,str(data.destination),True,db,llm_predictions,llm_top1)
    
            return JSONResponse(
                {
                    "message":"Noted to Notion",
                    "category":data.category
                },status_code=status.HTTP_200_OK
            )
        
        logger.info("No real code detected, using enriched text")
        text = code_res['enriched_text']

    logger.info("Creating text block in Notion")
    
    try:
        resp = createNotionBlock(token,page_id,text,str(data.destination),False)
        logger.info("Successfully created text block in Notion")
    except Exception as e:
        logger.error(f"Failed to create text block in Notion: {str(e)}")
        raise HTTPException(500,detail=e)
        
    background_tasks.add_task(saveHighlightData,data.text, user.user_id,category, resp,page_id,str(data.destination),False,db,llm_predictions,llm_top1)
    
    return JSONResponse(
            {
                "message":"Noted to Notion",
                "category":data.category
            },status_code=status.HTTP_200_OK
        )






@router.post("/create/enriched")
def createNotesEnrich(data : CategoryEnrich,background_tasks : BackgroundTasks ,user : UserAuth = Depends(Autherize),db : Session = Depends(get_db),):

    logger.info("Trying to get user preference")
    preference = user.preference.value
    logger.info(f"Found preference for user {user.user_id} to be {preference}")
    
    token = getNotionToken(user,db)
    database_id = db.query(NotionID).filter(NotionID.user_id == user.user_id).first().database_id
    
    category = data.category.upper()
    
    exist = db.query(NotionPage).filter(NotionPage.user_id == user.user_id).filter(NotionPage.title == category).first()
    page_id = None

    code = data.checked

    # REDIS STUFF
    try:
        redis_token = data.token    
        key = f"category_{user.user_id}_{redis_token}"
        raw_preds = redisClient.get(key)
        print(redis_token)
        print(raw_preds)
        llm_predictions = json.loads(raw_preds)
        llm_top1 = None
        print(llm_predictions)
        print(type(llm_predictions))
        redisClient.delete(key)
        mx_score = 0
        for cat in llm_predictions:
            score = float(llm_predictions[cat])
            if score > mx_score:
                mx_score = score
                llm_top1 = cat

    except Exception as e:
            logger.info(f"Error :- {e}")
            return e


    if not exist:
        try:
            logger.info(f"Page Not found , Creating new page with title {category}")
            response = createCategoryPageNotion(token,database_id,category,db,user)

            page_id = response.notion_page_id

            cat = UserCategories(user_id = user.user_id, category_name=category)
            
            db.add(cat)
            db.commit()
        except Exception as e:
            return e
    

    if not page_id:
        logger.info(f"Page found of category {category} for user {user.user_id}, extracting page_id")
        page_id = exist.notion_page_id


    logger.info(f"Page ID found : {page_id}")

    text = data.text

    if code:
    
        logger.info("Code detection requested, calling handleCode")
        code_res = handleCode(data.text)
        is_real_code = code_res['code']
        logger.info(f"Code detection result: is_real_code={is_real_code}")

        if is_real_code:
    
            logger.info("Real code detected, processing code block")
            code_text = code_res['code_content']
            code_language = code_res['code_language']
            logger.info(f"Code language detected: {code_language}")

            code_language = validateCodeLanguage(code_language)

            try:
                resp = createNotionBlock(token,page_id,code_text,str(data.destination),True,code_language)
                logger.info("Successfully created code block in Notion")
            except Exception as e:
                logger.error(f"Failed to create code block in Notion: {str(e)}")
                raise HTTPException(500,detail=e)
    
            background_tasks.add_task(saveHighlightData,data.text, user.user_id,category,resp,page_id,str(data.destination),True,db, llm_predictions,llm_top1)
    
            return JSONResponse(
                {
                    "message":"Noted to Notion",
                    "category":data.category
                },status_code=status.HTTP_200_OK
            )
        
        else:
            logger.info("No code detected, using enriched text")
            return JSONResponse(
                {
                    "message":"No code detected in the Text"
                },status_code=status.HTTP_400_BAD_REQUEST
            )


        
    enrichment_option = data.enrichment
    enriched_text = enrich_note(data.text,enrichment_option)
    
    exists = similarityDataSearch(enriched_text,user.user_id)

    if exists:
        return JSONResponse(
                {
                    "message":"Note Already found in page: {0} with {1} % Similarity".format(exists['payload']['category'],float(exists['score'])*100),
                    "category":data.category
                },status_code=status.HTTP_200_OK
            )


    try:
        resp = createNotionBlock(token,page_id,enriched_text,str(data.destination),False)
        print(resp)
    except Exception as e:
        raise HTTPException(500,detail=e)
    
    background_tasks.add_task(saveHighlightData,enriched_text, user.user_id,category,resp,page_id,str(data.destination),False,db,llm_predictions,llm_top1)

    return JSONResponse(
        {
            "message":"Noted to Notion",
            "category":data.category
        },status_code=status.HTTP_200_OK
    )

