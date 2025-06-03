from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import logging

templates = Jinja2Templates(directory="app/templates")

async def custom_404_handler(request: Request, exc: HTTPException):
    """Custom 404 error handler"""
    return templates.TemplateResponse(
        "error.html", 
        {
            "request": request, 
            "error_code": 404,
            "error_message": "Page not found"
        },
        status_code=404
    )

async def custom_500_handler(request: Request, exc: Exception):
    """Custom 500 error handler"""
    logging.error(f"Internal server error: {exc}")
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "error_code": 500,
            "error_message": "Internal server error"
        },
        status_code=500
    )