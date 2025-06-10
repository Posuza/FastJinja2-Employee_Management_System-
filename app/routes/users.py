from fastapi import APIRouter, Depends, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Optional, List
from datetime import datetime
import app.db as db
from app.auth import get_current_user, get_password_hash
from app.schemas import User, UserCreate, UserUpdate
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# User Management Routes
@router.get("/users", response_class=HTMLResponse)
async def users_page(request: Request, current_user: dict = Depends(get_current_user)):
    """Display users management page"""
    # Check if user has admin role
    if current_user["role"] != "admin":
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    
    # Get all users
    query = "SELECT * FROM User ORDER BY created_at DESC"
    users = await db.database.fetch_all(query=query)
    
    # Extract message and error from URL parameters (like employees.py does)
    message = request.query_params.get('message')
    error = request.query_params.get('error')
    
    # Convert + to spaces and decode
    if message:
        message = message.replace('+', ' ')
    if error:
        error = error.replace('+', ' ')
    
    # Return the users page with message/error parameters
    return templates.TemplateResponse("home.html", {
        "request": request,
        "current_user": current_user,
        "users": users,
        "message": message,  # ← Add this
        "error": error       # ← Add this
    })


@router.post("/users")
async def create_user(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    redirect_to: Optional[str] = Form("/users"),
    current_user: dict = Depends(get_current_user)
):
    """Create a new user (admin only)"""
    # Check if user has admin role
    if current_user["role"] != "admin":
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    
    try:
        # Check if username exists
        existing_user = await db.database.fetch_one(
            query="SELECT user_id FROM User WHERE username = :username",
            values={"username": username.strip()}
        )
        if existing_user:
            # Get all users for redisplay
            query = "SELECT * FROM User ORDER BY created_at DESC"
            users = await db.database.fetch_all(query=query)
            
            return templates.TemplateResponse("home.html", {
                "request": request,
                "current_user": current_user,
                "users": users,
                "error": f"Username '{username}' is already taken"
            })
        
        # Check if email exists
        existing_email = await db.database.fetch_one(
            query="SELECT user_id FROM User WHERE email = :email",
            values={"email": email.strip()}
        )
        if existing_email:
            # Get all users for redisplay
            query = "SELECT * FROM User ORDER BY created_at DESC"
            users = await db.database.fetch_all(query=query)
            
            return templates.TemplateResponse("home.html", {
                "request": request,
                "current_user": current_user,
                "users": users,
                "error": "Email address is already registered"
            })
        
        # Create user
        hashed_password = get_password_hash(password)
        now = datetime.utcnow()
        
        # Modified query - removed full_name field
        query = """
        INSERT INTO User (username, email, password_hash, role, created_at, updated_at)
        VALUES (:username, :email, :password_hash, :role, :created_at, :updated_at)
        """
        
        await db.database.execute(
            query=query,
            values={
                "username": username.strip(),
                "email": email.strip(),
                "password_hash": hashed_password,
                "role": role.strip(),
                "created_at": now,
                "updated_at": now
            }
        )
        
        # Get the user_id of the newly created user
        new_user = await db.database.fetch_one(
            query="SELECT user_id FROM User WHERE username = :username",
            values={"username": username.strip()}
        )
        
        # Log user creation
        await db.database.execute(
            query="INSERT INTO Log (user_id, action, details) VALUES (:user_id, :action, :details)",
            values={
                "user_id": current_user["user_id"],
                "action": "USER_CREATED",
                "details": f"Admin {current_user['username']} created new user {username}"
            }
        )
        
        # Return redirect with success message
        return RedirectResponse(
            url=f"{redirect_to}?message=User+{username}+created+successfully",
            status_code=status.HTTP_303_SEE_OTHER
        )
        
    except Exception as e:
        print(f"Create user error: {e}")
        # Get all users for redisplay
        query = "SELECT * FROM User ORDER BY created_at DESC"
        users = await db.database.fetch_all(query=query)
        
        return templates.TemplateResponse("home.html", {
            "request": request,
            "current_user": current_user,
            "users": users,
            "error": f"Failed to create user: {str(e)}"
        })


@router.get("/users/{user_id}", response_class=HTMLResponse)
async def get_user(request: Request, user_id: int, current_user: dict = Depends(get_current_user)):
    """Get user details (admin only)"""
    # Check if user has admin role
    if current_user["role"] != "admin":
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    
    # Get user
    user = await db.database.fetch_one(
        query="SELECT * FROM User WHERE user_id = :user_id",
        values={"user_id": user_id}
    )
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Return user details
    return templates.TemplateResponse("home.html", {
        "request": request,
        "current_user": current_user,
        "user": dict(user)
    })

@router.post("/users/{user_id}/update")
async def update_user(
    request: Request,
    user_id: int,
    username: str = Form(...),  # Add username parameter
    email: str = Form(...),
    role: str = Form(...),
    redirect_to: Optional[str] = Form("/users"),
    current_user: dict = Depends(get_current_user)
):
    """Update user details (admin only)"""
    if current_user["role"] != "admin":
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    
    try:
        # Get the user to update
        user_to_update = await db.database.fetch_one(
            query="SELECT * FROM User WHERE user_id = :user_id",
            values={"user_id": user_id}
        )
        
        if not user_to_update:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if username is taken by another user
        if username.strip() != user_to_update['username']:
            existing_username = await db.database.fetch_one(
                query="SELECT user_id FROM User WHERE username = :username AND user_id != :user_id",
                values={"username": username.strip(), "user_id": user_id}
            )
            if existing_username:
                return RedirectResponse(
                    url=f"{redirect_to}?error=Username+'{username}'+is+already+taken",
                    status_code=status.HTTP_303_SEE_OTHER
                )
        
        # Check if email is taken by another user
        if email.strip() != user_to_update['email']:
            existing_email = await db.database.fetch_one(
                query="SELECT user_id FROM User WHERE email = :email AND user_id != :user_id",
                values={"email": email.strip(), "user_id": user_id}
            )
            if existing_email:
                return RedirectResponse(
                    url=f"{redirect_to}?error=Email+address+is+already+registered",
                    status_code=status.HTTP_303_SEE_OTHER
                )
        
        # Update user - now includes username
        query = """
        UPDATE User 
        SET username = :username, email = :email, role = :role, updated_at = :updated_at
        WHERE user_id = :user_id
        """
        
        await db.database.execute(
            query=query,
            values={
                "username": username.strip(),
                "email": email.strip(),
                "role": role.strip(),
                "updated_at": datetime.utcnow(),
                "user_id": user_id
            }
        )
        
        # Return with success message
        return RedirectResponse(
            url=f"{redirect_to}?message=User+{username}+updated+successfully",
            status_code=status.HTTP_303_SEE_OTHER
        )
        
    except Exception as e:
        print(f"Update user error: {e}")
        return RedirectResponse(
            url=f"{redirect_to}?error=Failed+to+update+user:+{str(e)}",
            status_code=status.HTTP_303_SEE_OTHER
        )

@router.post("/users/{user_id}/reset-password")
async def reset_user_password(
    request: Request,
    user_id: int,
    new_password: str = Form(...),
    redirect_to: Optional[str] = Form("/users"),
    current_user: dict = Depends(get_current_user)
):
    """Reset user password (admin only)"""
    if current_user["role"] != "admin":
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    
    try:
        # Get the user to update
        user_to_update = await db.database.fetch_one(
            query="SELECT * FROM User WHERE user_id = :user_id",
            values={"user_id": user_id}
        )
        
        if not user_to_update:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update password
        hashed_password = get_password_hash(new_password)
        
        await db.database.execute(
            query="UPDATE User SET password_hash = :password_hash, updated_at = :updated_at WHERE user_id = :user_id",
            values={
                "password_hash": hashed_password,
                "updated_at": datetime.utcnow(),
                "user_id": user_id
            }
        )
        
        # Get updated user
        updated_user = await db.database.fetch_one(
            query="SELECT * FROM User WHERE user_id = :user_id",
            values={"user_id": user_id}
        )
        
        # Return user details with success message
        return RedirectResponse(
            url=f"{redirect_to}?message=Password+for+user+{user_to_update['username']}+reset+successfully",
            status_code=status.HTTP_303_SEE_OTHER
        )
        
    except Exception as e:
        print(f"Reset password error: {e}")
        user = await db.database.fetch_one(
            query="SELECT * FROM User WHERE user_id = :user_id",
            values={"user_id": user_id}
        )
        
        return templates.TemplateResponse("user_detail.html", {
            "request": request,
            "current_user": current_user,
            "user": dict(user),
            "error": "Failed to reset password. Please try again."
        })

@router.post("/users/{user_id}/delete")
async def delete_user(
    request: Request,
    user_id: int,
    redirect_to: Optional[str] = Form("/home"),  # ← Change default to /home
    current_user: dict = Depends(get_current_user)
):
    """Delete user (admin only)"""
    print(f"DELETE USER REQUEST: user_id={user_id}, admin={current_user['role']}")
    
    if current_user["role"] != "admin":
        print("ERROR: Not admin")
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    
    try:
        # Cannot delete yourself
        if user_id == current_user["user_id"]:
            return RedirectResponse(
                url=f"{redirect_to}?error=You+cannot+delete+your+own+account",
                status_code=status.HTTP_303_SEE_OTHER
            )
        
        # Get the user to delete
        user_to_delete = await db.database.fetch_one(
            query="SELECT * FROM User WHERE user_id = :user_id",
            values={"user_id": user_id}
        )
        
        if not user_to_delete:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Delete user
        await db.database.execute(
            query="DELETE FROM User WHERE user_id = :user_id",
            values={"user_id": user_id}
        )
        
        # Get all users
        query = "SELECT * FROM User ORDER BY created_at DESC"
        users = await db.database.fetch_all(query=query)
        
        # Return the users page with success message
        return RedirectResponse(
            url=f"/home?message=User+{user_to_delete['username']}+deleted+successfully",  # ← Always redirect to /home
            status_code=status.HTTP_303_SEE_OTHER
        )
        
    except Exception as e:
        print(f"Delete user error: {e}")
        query = "SELECT * FROM User ORDER BY created_at DESC"
        users = await db.database.fetch_all(query=query)
        
        return templates.TemplateResponse("home.html", {
            "request": request,
            "current_user": current_user,
            "users": users,
            "error": "Failed to delete user. Please try again."
        })