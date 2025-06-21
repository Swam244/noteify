from fastapi import APIRouter
from fastapi.responses import FileResponse
import logging
import os

router = APIRouter()

logger = logging.getLogger(__name__)

@router.get("/help")
async def help_page():
    """
    Serve the help/guide page for users
    """
    try:
        guide_path = "static/pdfjs/guide.html"
        
        if not os.path.exists(guide_path):
            logger.error(f"Guide file not found at {guide_path}")
            return {"error": "Help page not found"}, 404
        
        logger.info("Help page accessed")
        
        return FileResponse(
            path=guide_path,
            media_type="text/html",
            headers={"Cache-Control": "no-cache"}
        )
        
    except Exception as e:
        logger.error(f"Error serving help page: {str(e)}")
        return {"error": "Internal server error"}, 500 