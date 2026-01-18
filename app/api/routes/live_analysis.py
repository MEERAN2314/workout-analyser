from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def live_analysis_page(request: Request):
    """Live analysis page"""
    return templates.TemplateResponse(
        "live_analysis.html",
        {"request": request, "title": "Live Analysis"}
    )

@router.post("/start-session")
async def start_live_session():
    """Start live analysis session - placeholder"""
    return {"message": "Live session endpoint - to be implemented"}