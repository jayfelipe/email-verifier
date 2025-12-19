# backend/app/models.py
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, nullable=False, unique=True)
    hashed_password: str
    is_active: bool = True
    is_admin: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class EmailJob(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: str = Field(index=True, nullable=False, unique=True)
    owner_id: Optional[int] = Field(default=None, foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="pending")
    total: Optional[int] = 0
    processed: Optional[int] = 0

class EmailResult(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: str = Field(index=True)
    email: str = Field(index=True)
    domain: str = Field(index=True)
    scoring: Optional[str] = None  # store JSON as str or JSONB (need custom)
    heuristics: Optional[str] = None
    smtp: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
