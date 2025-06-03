from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
import app.db as db
from app.auth import  get_current_user, get_password_hash, is_strong_password, verify_password
from datetime import datetime


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Profile routes
@router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request, current_user: dict = Depends(get_current_user)):
    """Display user profile page"""
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "user": current_user,
        "current_user": current_user  # <-- add this line
    })

@router.post("/profile/update")
async def update_profile(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    """Handle profile update"""
    try:
        await db.database.execute(
            query="UPDATE User SET username = :username, email = :email, updated_at = :updated_at WHERE user_id = :user_id",
            values={
                "username": username,
                "email": email,
                "updated_at": datetime.utcnow(),
                "user_id": current_user["user_id"]
            }
        )
        updated_user = await db.database.fetch_one(
            query="SELECT * FROM User WHERE user_id = :user_id",
            values={"user_id": current_user["user_id"]}
        )
        return templates.TemplateResponse("profile.html", {
            "request": request,
            "user": dict(updated_user),
            "message": "Profile updated successfully"
        })
    except Exception as e:
        return templates.TemplateResponse("profile.html", {
            "request": request,
            "user": current_user,
            "error": "Failed to update profile. Please try again."
        })

# POST: Change password
@router.post("/profile/change-password")
async def change_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    # Check password strength
    if not is_strong_password(new_password):
        return templates.TemplateResponse("profile.html", {
            "request": request,
            "user": current_user,
            "error": "New password is not strong enough. It must be at least 8 characters, contain uppercase, lowercase, a digit, and a special character."
        })

    # Fetch user from DB
    user = await db.database.fetch_one(
        query="SELECT * FROM User WHERE user_id = :user_id",
        values={"user_id": current_user["user_id"]}
    )
    if not user or not verify_password(current_password, user["password_hash"]):
        return templates.TemplateResponse("profile.html", {
            "request": request,
            "user": current_user,
            "error": "Current password is incorrect"
        })

    # Update password
    hashed_password = get_password_hash(new_password)
    await db.database.execute(
        query="UPDATE User SET password_hash = :password_hash, updated_at = :updated_at WHERE user_id = :user_id",
        values={
            "password_hash": hashed_password,
            "updated_at": datetime.utcnow(),
            "user_id": current_user["user_id"]
        }
    )
    updated_user = await db.database.fetch_one(
        query="SELECT * FROM User WHERE user_id = :user_id",
        values={"user_id": current_user["user_id"]}
    )
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "user": dict(updated_user),
        "message": "Password changed successfully"
    })