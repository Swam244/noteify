from appwrite.client import Client
from appwrite.services.storage import Storage
from appwrite.permission import Permission
from appwrite.role import Role
from appwrite.input_file import InputFile
from appwrite.exception import AppwriteException
import logging
from app.config import settings
from app.db.models import UserImages,UserAuth
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

BUCKET_ID = settings.BUCKET_ID
PROJECT_ID = settings.PROJECT_ID
ENDPOINT = settings.ENDPOINT
API_KEY = settings.APPWRITE_SECRET
BASE_URL = settings.BASE_URL

client = Client()
client.set_endpoint(ENDPOINT)
client.set_project(PROJECT_ID)
client.set_key(API_KEY)

storage = Storage(client)


def createUrls(file_id: str, db : Session, user : UserAuth, bucket_id: str = BUCKET_ID, project_id: str = PROJECT_ID, endpoint: str = ENDPOINT):
    logger.info(f"[createUrls] Called with file_id={file_id}, user_id={user.user_id}")
    view_url = f"{endpoint}/storage/buckets/{bucket_id}/files/{file_id}/view?project={project_id}"
    download_url = f"{endpoint}/v1/storage/buckets/{bucket_id}/files/{file_id}/download?project={project_id}"
    
    try:
        newObj = UserImages(
            user_id = user.user_id,
            image_id = file_id, 
            appwrite_link = view_url
        )
        db.add(newObj)
        db.commit()
        db.refresh(newObj)
        logger.info(f"[createUrls] UserImages record created for file_id={file_id}")
    
    except Exception as e:
        logger.error(f"[createUrls] Error creating UserImages record: {e}")
        return e
    
    view_link = BASE_URL + f"/images/{file_id}"
    logger.info(f"[createUrls] Returning view_link={view_link}")
    return {
        "view_url": view_link,
    }


def getImageInfo(file_id: str,db : Session, user : UserAuth):
    logger.info(f"[getImageInfo] Called with file_id={file_id}, user_id={user.user_id}")
    
    try:
        urls = db.query(UserImages).filter(UserImages.user_id == user.user_id).filter(UserImages.image_id == file_id).first()
        if urls:
            logger.info(f"[getImageInfo] Found image for file_id={file_id}")
            return {
                "success": True,
                "file_id": urls.image_id,
                "view_url": urls.appwrite_link,
            }
        else:
            logger.warning(f"[getImageInfo] No image found for file_id={file_id}")
            return {
                "success": False,
                "error": "Image not found"
            }
    
    except Exception as e:
        logger.error(f"[getImageInfo] Unexpected error getting file info {file_id}: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def uploadImage(file_path: str, file_id: str,db : Session, user : UserAuth, bucket_id: str = BUCKET_ID,permissions: Optional[list] = None):
    logger.info(f"[uploadImage] Called with file_path={file_path}, file_id={file_id}, user_id={user.user_id}")
    
    try:
        if permissions is None:
            permissions = [Permission.read(Role.any())]
        file = InputFile.from_path(file_path)
        logger.info(f"[uploadImage] Uploading file to Appwrite storage...")
        result = storage.create_file(
            bucket_id=bucket_id,
            file_id=file_id,
            file=file,
            permissions=permissions
        )
        logger.info(f"[uploadImage] File uploaded to Appwrite with file_id={result['$id']}")
        urls = createUrls(result["$id"],db,user)
        logger.info(f"[uploadImage] URLs created for file_id={file_id}")
    
        return {
            "success": True,
            "file_id": result["$id"],
            "file_name": result.get("name", file_id),
            "file_size": result.get("size", 0),
            "mime_type": result.get("mimeType", ""),
            "urls": urls,
            "result": result
        }
    
    except AppwriteException as e:
        logger.error(f"[uploadImage] Appwrite error uploading file {file_id}: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "error_code": e.code if hasattr(e, 'code') else None
        }
    except Exception as e:
        logger.error(f"[uploadImage] Unexpected error uploading file {file_id}: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

# NOT TESTED.
def update_file_in_storage(file_id: str,file_path: str,bucket_id: str = BUCKET_ID,permissions: Optional[list] = None) -> Dict[str, Any]:
    logger.info(f"[update_file_in_storage] Called with file_id={file_id}, file_path={file_path}")
    try:
        if permissions is None:
            permissions = [Permission.read(Role.any())]
        file = InputFile.from_path(file_path)
        logger.info(f"[update_file_in_storage] Updating file in Appwrite storage...")
        result = storage.update_file(
            bucket_id=bucket_id,
            file_id=file_id,
            file=file,
            permissions=permissions
        )
        logger.info(f"[update_file_in_storage] File updated in Appwrite with file_id={result['$id']}")
        urls = create_appwrite_urls(bucket_id, result["$id"], PROJECT_ID)
        logger.info(f"[update_file_in_storage] URLs created for file_id={file_id}")
        return {
            "success": True,
            "file_id": result["$id"],
            "file_name": result.get("name", file_id),
            "file_size": result.get("size", 0),
            "mime_type": result.get("mimeType", ""),
            "urls": urls,
            "result": result
        }
    except AppwriteException as e:
        logger.error(f"[update_file_in_storage] Appwrite error updating file {file_id}: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "error_code": e.code if hasattr(e, 'code') else None
        }
    except Exception as e:
        logger.error(f"[update_file_in_storage] Unexpected error updating file {file_id}: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def delete_file_from_storage(file_id: str,bucket_id: str = BUCKET_ID) -> Dict[str, Any]:
    logger.info(f"[delete_file_from_storage] Called with file_id={file_id}")
    try:
        result = storage.delete_file(
            bucket_id=bucket_id,
            file_id=file_id
        )
        logger.info(f"[delete_file_from_storage] File deleted successfully: {file_id}")
        return {
            "success": True,
            "message": f"File {file_id} deleted successfully",
            "result": result
        }
    except AppwriteException as e:
        logger.error(f"[delete_file_from_storage] Appwrite error deleting file {file_id}: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "error_code": e.code if hasattr(e, 'code') else None
        }
    except Exception as e:
        logger.error(f"[delete_file_from_storage] Unexpected error deleting file {file_id}: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

