# backend/app/persistence_email_history.py

from datetime import datetime
from sqlmodel import SQLModel, Field
from app.db import async_session
from sqlalchemy import Column, DateTime


class EmailVerificationHistory(SQLModel, table=True):
    __tablename__ = "email_verification_history"

    id: int | None = Field(default=None, primary_key=True)
    email: str
    domain: str
    status: str
    score: int
    reason: str
    checked_at: datetime = Field(
        sa_column=Column(DateTime(timezone=False))
    )


async def save_email_verification(
    email: str,
    domain: str,
    status: str,
    score: int,
    reason: str
):
    async with async_session() as session:
        record = EmailVerificationHistory(
            email=email,
            domain=domain,
            status=status,
            score=score,
            reason=reason,
            checked_at=datetime.utcnow()
        )

        session.add(record)
        await session.commit()
