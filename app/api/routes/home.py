from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page with navigation options"""
    return templates.TemplateResponse(
        "home.html", 
        {"request": request, "title": "Workout Analyzer"}
    )

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """User dashboard - will add authentication later"""
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "title": "Dashboard"}
    )