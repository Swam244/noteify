from fastapi import APIRouter,Depends,Response
from fastapi.responses import JSONResponse
from fastapi import status, HTTPException
from app.db.models import UserAuth,UserCategories,NotionBlock,NotionID,NotionPage
from app.db.database import get_db
from sqlalchemy.orm import Session
from app.utils import Autherize,normalizeCategoryName
from app.db.schemas import *
from app.config import settings
import logging
from app.core.groqClient import categorize_note
import json

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notes",tags=['Notes'])

categories = ['AI',"Machine Learning","Technology"]

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



@router.post("/create")
def createNotes(data : Notes): # REMEMBER TO ADD USER AUTH HERE currently not added for testing.
    logger.info("Starting note categorization process")
    try:
        categorization_response = categorize_note(data.text, categories)
        logger.debug(f"Received categorization response: {categorization_response}")
        scores = json.loads(categorization_response)

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse categorization response: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse categorization response from AI model.\n {e}"
        )
    except Exception as e:
        logger.error(f"Unexpected error during note categorization: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during note categorization: {str(e)}"
        )

    best_category = None
    max_score = -1.0

    for category, score in scores.items():
        if isinstance(score, (int, float)):
            if score > max_score:
                max_score = score
                best_category = category

    if best_category is not None and max_score >= 0.5:
        logger.info(f"Successfully categorized note with category: {best_category} (score: {max_score})")
        return {
            "success": "200",
            "category": best_category
        }
    else:
        logger.warning(f"No suitable category found. Best category: {best_category}, score: {max_score}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found with sufficient confidence (score < 0.5)."
        )
    
