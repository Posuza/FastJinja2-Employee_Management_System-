from fastapi import APIRouter, Depends, HTTPException, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordBearer
from fastapi.templating import Jinja2Templates
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from databases import Database
from typing import Optional
import re
import app.db as db
from app.schemas import User, TokenData, Token, UserCreate
from app.auth import (
    get_current_user_optional, 
    authenticate_user, 
    create_token_response, 
    get_password_hash,
    check_rate_limit,
    login_attempts,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    is_valid_email,
    is_strong_password
)

# Set up router and templates
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


# Routes
@router.get("/", response_class=HTMLResponse)
async def index(request: Request, current_user: Optional[dict] = Depends(get_current_user_optional)):
    """Home page"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "current_user": current_user
    })

@router.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request, 
    message: Optional[str] = None,  # Add this parameter
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Display login page"""
    if current_user:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("login.html", {
        "request": request,
        "message": message  # Pass the message to the template
    })

@router.post("/login", response_class=HTMLResponse)
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    """Handle login form submission"""
    # Check rate limit
    can_login, wait_time = check_rate_limit(username.strip())
    if not can_login:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Too many login attempts. Please try again later.",
            "wait_time": wait_time
        })
    
    user = await authenticate_user(db.database, username.strip(), password)
    if not user:
        # Record failed login attempt
        login_attempts.setdefault(username.strip(), []).append(datetime.utcnow())
        
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Invalid username or password"
        })
    
    # Create access token
    token = create_token_response(user["username"])
    
    # Create response with redirect
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    
    # Set cookie with token
    response.set_cookie(
        key="access_token",
        value=token.access_token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        expires=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    
    return response

@router.get("/logout", response_class=RedirectResponse)
async def logout(request: Request):
    """Logout user by clearing the cookie"""
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    return response

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, current_user: Optional[dict] = Depends(get_current_user_optional)):
    """Display registration page"""
    if current_user:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register", response_class=HTMLResponse)
async def register(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    # Remove full_name parameter
    password: str = Form(...),
    confirm_password: str = Form(...)
):
    """Handle registration form submission"""
    # Validate input
    if password != confirm_password:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Passwords do not match",
            "username": username,
            "email": email
            # Remove full_name
        })
    
    if not is_valid_email(email):
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Please enter a valid email address",
            "username": username
            # Remove full_name
        })
    
    # Check if username exists
    existing_user = await db.database.fetch_one(
        query="SELECT username FROM User WHERE username = :username",
        values={"username": username.strip()}
    )
    
    if existing_user:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Username already exists",
            "email": email
            # Remove full_name
        })
    
    # Check if email exists
    existing_email = await db.database.fetch_one(
        query="SELECT email FROM User WHERE email = :email",
        values={"email": email.strip()}
    )
    
    if existing_email:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Email address is already registered",
            "username": username
            # Remove full_name
        })
    
    if not is_strong_password(password):
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Password must be at least 8 characters long and include uppercase, lowercase, numbers, and special characters",
            "username": username,
            "email": email
        })
    
    # Create user
    hashed_password = get_password_hash(password)
    user_data = UserCreate(
        username=username.strip(),
        email=email.strip(),
        password_hash=hashed_password,
        role="user"
    )
    
    now = datetime.utcnow()
    # Update the query to remove full_name
    query = """
    INSERT INTO User (username, email, password_hash, role, created_at, updated_at)
    VALUES (:username, :email, :password_hash, :role, :created_at, :updated_at)
    """
    
    values = user_data.dict()
    values.update({"created_at": now, "updated_at": now})
    
    await db.database.execute(query=query, values=values)
    
    # Get the user_id of the newly created user
    new_user = await db.database.fetch_one(
        query="SELECT user_id FROM User WHERE username = :username",
        values={"username": username.strip()}
    )
    
# Replace it with this updated version:
    await db.database.execute(
        query="INSERT INTO Log (user_id, action, details, timestamp) VALUES (:user_id, :action, :details, :timestamp)",
        values={
            "user_id": new_user["user_id"],
            "action": "USER_REGISTERED",
            "details": f"New user {username} registered successfully",
            "timestamp": datetime.utcnow()  # Add the current timestamp
        }
    )
    
    return templates.TemplateResponse("login.html", {
        "request": request,
        "message": "Registration successful! Please log in."
    })

# Add this route for /home
@router.get("/home", response_class=HTMLResponse)
async def home_page(
    request: Request,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    # Get employees
    employees = await db.database.fetch_all("SELECT * FROM Employee ORDER BY created_at DESC")
    
    # Process employees for display
    processed_employees = []
    for emp in employees:
        employee_dict = dict(emp)
        
        # Calculate initials for avatar
        first_initial = emp["first_name"][0].upper() if emp["first_name"] else ""
        last_initial = emp["last_name"][0].upper() if emp["last_name"] else ""
        employee_dict["initials"] = f"{first_initial}{last_initial}"
        
        # Full name with prefix
        prefix = f"{emp['prefix']} " if emp["prefix"] else ""
        employee_dict["full_name"] = f"{prefix}{emp['first_name']} {emp['last_name']}"
        
        # Normalize employment type for CSS classes
        if emp["employment"]:
            employee_dict["employment_normalized"] = emp["employment"].lower().replace("-", "_")
        else:
            employee_dict["employment_normalized"] = ""
            
        # Normalize status for CSS classes
        if emp["status"]:
            employee_dict["status_normalized"] = emp["status"].lower().replace(" ", "_")
        else:
            employee_dict["status_normalized"] = ""
        
        processed_employees.append(employee_dict)
    
    # Get users if current user is admin
    users = []
    if current_user and current_user.get("role") == "admin":
        users = await db.database.fetch_all("SELECT * FROM User ORDER BY created_at DESC")
    
    # Generate auto employee code (optional)
    from app.routes.employees import generate_employee_code
    auto_gen_employee_code = await generate_employee_code()
    
    # Current date
    current_date = datetime.now().strftime("%B %d, %Y")
    
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "current_user": current_user,
            "employees": processed_employees,
            "users": users,
            "auto_gen_employee_code": auto_gen_employee_code,
            "current_date": current_date
        }
    )