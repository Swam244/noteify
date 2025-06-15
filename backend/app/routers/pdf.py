from fastapi import Request,APIRouter
from fastapi.responses import StreamingResponse, Response
import requests

router = APIRouter()

@router.get("/pdfproxy")
def proxy_pdf(url: str, request: Request):
    try:
        print(f"Proxying request for: {url}")
        if "viewer.html" in url or "pdfproxy" in url:
            return Response(content="Invalid URL", status_code=400)

        # Fetch and stream the PDF
        r = requests.get(url, stream=True, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()

        return StreamingResponse(r.raw, media_type="application/pdf", headers={
            "Access-Control-Allow-Origin": "*",
            "Content-Disposition": "inline; filename=document.pdf"
        })
    except Exception as e:
        return Response(content=f"Failed to fetch PDF: {str(e)}", status_code=500)
