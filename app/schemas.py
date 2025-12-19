# backend/app/schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional, List

class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: Optional[str] = None

class TokenData(BaseModel):
    email: Optional[str] = None
    is_admin: bool = False

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserRead(BaseModel):
    id: int
    email: EmailStr
    is_admin: bool

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class JobCreate(BaseModel):
    emails: List[EmailStr]
    job_name: Optional[str] = None

class JobRead(BaseModel):
    job_id: str
    status: str
    total: int
    processed: int
