import logging
from notion_client import Client, APIResponseError
from fastapi import HTTPException,status
from app.db.database import get_db
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.db.models import NotionPage, UserAuth


logger = logging.getLogger(__name__)


def createNotionPage(access_token: str,user : UserAuth ,db: Session , isDefault : bool = False, title: str = "NoteifyNotes"):

    try:
        notion = Client(auth=access_token)
        page_exists = db.query(NotionPage).filter(NotionPage.user_id == user.user_id).filter(NotionPage.title == title).first()
        
        if page_exists:
            return JSONResponse(
                {
                    "detail":"Page already Exists"
                }
            ,status_code=status.HTTP_409_CONFLICT)
        

        response = notion.pages.create(
                parent={"type": "workspace", "workspace": True},
                properties={
                    "title": [
                        {
                            "type": "text",
                            "text": {
                                "content": title
                            }
                        }
                    ]
                }
            )

        page_id = response.get("id")
        page_url = response.get("url")
        page_title_content = title 
        try:
            notiondb = response['parent']['database_id']
        except Exception as e:
            notiondb = None

        if not page_id:
            logger.error("Notion API response missing page ID.")
            raise HTTPException(
                status_code=500,
                detail="Failed to retrieve page ID from Notion API response"
            )
        
        new_notion_page = NotionPage(
            user_id=user.user_id,
            notion_page_id=page_id,
            notion_page_url=page_url,
            title=page_title_content,
            notion_database_id=notiondb
        )
            
        db.add(new_notion_page)
        db.commit()
        db.refresh(new_notion_page) 

        return new_notion_page

    except APIResponseError as api_err:
        logger.error(f"Notion API error: {api_err.code}") 
        raise HTTPException(
            status_code=api_err.code if isinstance(api_err.code, int) else 400,
            detail=f"Notion API error: {api_err}"
        )
    except Exception as e:
        logger.error(f"Unexpected error creating Notion page for user {user.user_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error creating Notion page: {str(e)}"
        )




def createNotionDB(access_token: str, db : Session, user : UserAuth):
    parent_root_page_id = db.query(NotionPage).filter(NotionPage.user_id == user.user_id).filter(NotionPage.title == "NoteifyNotes").first()

    if not parent_root_page_id:
        try:
            parent_root_page_id = createNotionPage(access_token,user,db,isDefault=True)
        except Exception as e:
            return e

    data = {
        "parent":{
            "type": "page_id",
            "page_id": parent_root_page_id.notion_page_id
        },
        "title": [
            {
                "type": "text",
                "text": {
                    "content": "NoteifyNotes"
                }
            }
        ],
        "properties": {
            "Name": {
                "title": {} 
            }
        }
    }

    try:
        notion = Client(auth=access_token)
        response = notion.databases.create(**data)

        database_id = response.get("id")
        if not database_id:
            raise HTTPException(
                status_code=500,
                detail="Failed to retrieve database ID from Notion API response"
            )
        
        return response

    except APIResponseError as api_err:
        logger.error(f"Notion API error: {api_err.code}")    
        try:
            status_code = int(api_err.code)
        except (ValueError, TypeError):
            status_code = 400
        raise HTTPException(
            status_code=status_code,
            detail=f"Notion API error: {api_err}"
        )

    except Exception as e:
        logger.error(f"Unexpected error creating Notion database: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error creating Notion database: {str(e)}"
        )



# need to think about category creation (can do a tree like structure)
# need to create endpoints to fetch a particular block and full page
# need to create endpoint to update the content inside a block.
