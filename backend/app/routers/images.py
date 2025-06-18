from fastapi import APIRouter, HTTPException, Response,Depends,status
from fastapi.responses import JSONResponse
from app.db.database import get_db
from app.utils import Autherize
from app.core.s3_handler import getImageInfo
from sqlalchemy.orm import Session
from app.db.models import UserAuth,UserImages
import requests


router = APIRouter()

@router.get("/images/{image_id}.{ext}")
def serveImage(image_id: str, ext: str, db: Session = Depends(get_db)):
    urls = db.query(UserImages).filter(UserImages.image_id == image_id).first()

    if not urls:
        return JSONResponse({
            "message": "Image not found"
        }, status_code=status.HTTP_400_BAD_REQUEST)

    view_url = urls.appwrite_link
    resp = requests.get(view_url)

    if resp.status_code != 200:
        raise HTTPException(status_code=404, detail="Image not found in storage")

    content_type = resp.headers.get("Content-Type", "image/png")
    print(content_type)
    return Response(
        content=resp.content,
        media_type=content_type,
        headers={"Cache-Control": "public, max-age=31536000"}
    )