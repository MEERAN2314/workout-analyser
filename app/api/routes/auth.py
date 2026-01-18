from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    return templates.TemplateResponse(
        "auth/login.html",
        {"request": request, "title": "Login"}
    )

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Registration page"""
    return templates.TemplateResponse(
        "auth/register.html",
        {"request": request, "title": "Register"}
    )

@router.post("/login")
async def login():
    """Login endpoint - placeholder"""
    return {"message": "Login endpoint - to be implemented"}

@router.post("/register")
async def register():
    """Register endpoint - placeholder"""
    return {"message": "Register endpoint - to be implemented"}