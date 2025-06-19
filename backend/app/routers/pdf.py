from fastapi import Request,APIRouter
from fastapi.responses import StreamingResponse, Response
import requests
import logging

router = APIRouter()

logger = logging.getLogger(__name__)

@router.get("/pdfproxy")
def proxy_pdf(url: str, request: Request):
    try:
        logger.info(f"Proxying request for: {url}")
        if "viewer.html" in url or "pdfproxy" in url:
            return Response(content="Invalid URL", status_code=400)

        r = requests.get(url, stream=True, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()

        filename = None
        content_disp = r.headers.get("Content-Disposition")
        if content_disp:
            import re
            match = re.search(r'filename="?([^";]+)"?', content_disp)
            if match:
                filename = match.group(1)
        if not filename:
            import os
            from urllib.parse import urlparse
            path = urlparse(url).path
            basename = os.path.basename(path)
            if basename and "." in basename:
                filename = basename

        if not filename:
            filename = "document.pdf"

        return StreamingResponse(r.raw, media_type="application/pdf", headers={
            "Access-Control-Allow-Origin": "*",
            "Content-Disposition": f"inline; filename={filename}"
        })
    except Exception as e:
        logger.error(f"Failed to fetch PDF: {str(e)}")
        return Response(content=f"Failed to fetch PDF: {str(e)}", status_code=500)
