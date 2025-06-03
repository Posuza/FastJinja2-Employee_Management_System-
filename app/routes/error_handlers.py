from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Not found handler for API routes
@router.get("/api/{path:path}", include_in_schema=False)
async def api_not_found(path: str):
    """Catch-all route for API 404 errors"""
    raise HTTPException(status_code=404, detail="API endpoint not found")

# Not found handler for page routes
@router.get("/{path:path}", include_in_schema=False)
async def catch_all(request: Request, path: str):
    """Catch-all route to handle 404 errors"""
    return templates.TemplateResponse(
        "error.html", 
        {
            "request": request, 
            "error_code": 404,
            "error_message": "Page Not Found"
        },
        status_code=404
    )