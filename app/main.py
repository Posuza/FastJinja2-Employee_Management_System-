from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.exceptions import HTTPException
from starlette.status import HTTP_404_NOT_FOUND
from fastapi.templating import Jinja2Templates
import app.db as db
from app.routes import router

# Create FastAPI app
app = FastAPI(
    title="Employee Management System",
    description="A comprehensive employee management system with authentication",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/statics", StaticFiles(directory="app/statics"), name="statics")

# Include routes
app.include_router(router)

# Database events
@app.on_event("startup")
async def startup_event():
    await db.connect_db()

@app.on_event("shutdown")
async def shutdown_event():
    await db.disconnect_db()

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Employee Management System is running"}

templates = Jinja2Templates(directory="app/templates")

@app.exception_handler(HTTPException)
async def custom_auth_exception_handler(request: Request, exc: HTTPException):
    # If the error is due to authentication, show 404 page
    if exc.detail == "Could not validate credentials":
        return templates.TemplateResponse(
            "error.html",  # Make sure you have this template
            {"request": request},
            status_code=HTTP_404_NOT_FOUND
        )
    # Otherwise, use the default handler
    return await app.default_exception_handler(request, exc)