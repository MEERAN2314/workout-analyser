from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def recording_analysis_page(request: Request):
    """Recording analysis page"""
    return templates.TemplateResponse(
        "recording_analysis.html",
        {"request": request, "title": "Recording Analysis"}
    )

@router.post("/upload")
async def upload_video():
    """Upload video endpoint - placeholder"""
    return {"message": "Video upload endpoint - to be implemented"}