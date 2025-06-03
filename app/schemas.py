from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, date

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserBase(BaseModel):
    username: str
    email: EmailStr  # ✅ Required field - keep EmailStr
    role: str

class UserCreate(BaseModel):
    username: str
    email: str
    password_hash: str
    role: str = "user"

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None  # ✅ Optional but must be valid if provided
    password: Optional[str] = None
    role: Optional[str] = None

class User(UserBase):
    user_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class EmployeeBase(BaseModel):
    emp_code: str
    prefix: Optional[str] = None
    first_name: str
    last_name: str
    email: Optional[str] = None       
    phone: Optional[str] = None       
    thai_id_or_passport: Optional[str] = None
    employment: Optional[str] = None
    status: Optional[str] = None
    salary: Optional[float] = None
    address: Optional[str] = None

class EmployeeCreate(EmployeeBase):
    start_date: Optional[date] = None
    leave_date: Optional[date] = None

class EmployeeUpdate(BaseModel):
    emp_code: Optional[str] = None
    prefix: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    thai_id_or_passport: Optional[str] = None
    employment: Optional[str] = None
    start_date: Optional[date] = None
    leave_date: Optional[date] = None
    status: Optional[str] = None
    salary: Optional[float] = None
    address: Optional[str] = None

class Employee(EmployeeBase):
    employee_id: int
    start_date: Optional[date] = None
    leave_date: Optional[date] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class LogCreate(BaseModel):
    action: str
    details: Optional[str] = None
    user_id: Optional[int] = None

class Log(LogCreate):
    log_id: int
    timestamp: Optional[datetime] = None  # ✅ Changed from log_time to timestamp
    
    class Config:
        from_attributes = True