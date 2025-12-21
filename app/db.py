# backend/app/db.py
import os
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from .config import settings


# 1️⃣ Tomamos la URL
DATABASE_URL = settings.DATABASE_URL

# 2️⃣ Convertimos a asyncpg si viene como postgresql://
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgresql://",
        "postgresql+asyncpg://",
        1
    )

# 3️⃣ Creamos engine con SSL obligatorio (Railway)
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    connect_args={
        "ssl": "require"
    }
)

# 4️⃣ Session async
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# 5️⃣ Init DB
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
