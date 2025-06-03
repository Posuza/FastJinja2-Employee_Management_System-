from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from databases import Database
from typing import Optional
import app.db as db
from app.schemas import User, TokenData, Token

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "your-secret-key-change-this-in-production"  # Change this in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Simple in-memory rate limiting
login_attempts = {}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def authenticate_user(database: Database, username: str, password: str):
    """Authenticate user with username and password"""
    query = "SELECT * FROM User WHERE username = :username"
    user = await database.fetch_one(query=query, values={"username": username})
    if not user or not verify_password(password, user["password_hash"]):
        return False
    return dict(user)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password for storing"""
    return pwd_context.hash(password)

def get_token_from_cookie(request: Request) -> Optional[str]:
    """Extract token from cookie"""
    token = request.cookies.get("access_token")
    return token

async def get_current_user(request: Request):
    """Get current user from token in cookie"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = get_token_from_cookie(request)
    if not token:
        raise credentials_exception
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    query = "SELECT * FROM User WHERE username = :username"
    user = await db.database.fetch_one(query=query, values={"username": token_data.username})
    
    if user is None:
        raise credentials_exception
    
    return dict(user)

async def get_current_active_user(current_user: dict = Depends(get_current_user)):
    """Check if user is active"""
    if current_user.get("is_active") is False:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def create_token_response(username: str) -> Token:
    """Create a token response object"""
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")

async def get_current_user_optional(request: Request):
    """Get current user - returns None if not authenticated"""
    try:
        return await get_current_user(request)
    except HTTPException:
        return None

def is_valid_email(email: str) -> bool:
    """Validate email format"""
    import re
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, email))

def is_strong_password(password: str) -> bool:
    """Check if password meets minimum security requirements"""
    if len(password) < 8:
        return False
    
    # Check for at least one uppercase letter
    if not any(c.isupper() for c in password):
        return False
    
    # Check for at least one lowercase letter
    if not any(c.islower() for c in password):
        return False
    
    # Check for at least one digit
    if not any(c.isdigit() for c in password):
        return False
    
    # Check for at least one special character
    special_chars = "!@#$%^&*()-_=+[]{}|;:,.<>?/~"
    if not any(c in special_chars for c in password):
        return False
    
    return True

def check_rate_limit(username: str, max_attempts: int = 5, window_seconds: int = 300):
    """Check if user has exceeded login attempt rate limit"""
    now = datetime.utcnow()
    if username in login_attempts:
        attempts = [a for a in login_attempts[username] if now - a < timedelta(seconds=window_seconds)]
        login_attempts[username] = attempts
        if len(attempts) >= max_attempts:
            # Calculate time until oldest attempt expires
            if attempts:
                oldest_attempt = min(attempts)
                time_until_reset = (oldest_attempt + timedelta(seconds=window_seconds) - now).total_seconds()
                return False, int(time_until_reset)
    else:
        login_attempts[username] = []
    
    login_attempts[username].append(now)
    return True, 0