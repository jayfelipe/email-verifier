# backend/app/crud.py
from .models import User, EmailJob, EmailResult
from .db import async_session
from sqlmodel import select
from sqlalchemy.exc import IntegrityError

async def create_user(email: str, hashed_password: str, is_admin=False):
    async with async_session() as sess:
        user = User(email=email, hashed_password=hashed_password, is_admin=is_admin)
        sess.add(user)
        try:
            await sess.commit()
            await sess.refresh(user)
            return user
        except IntegrityError:
            await sess.rollback()
            return None

async def get_user_by_email(email: str):
    async with async_session() as sess:
        q = select(User).where(User.email == email)
        res = await sess.execute(q)
        return res.scalar_one_or_none()

async def create_job(job_id: str, owner_id: int, total: int):
    async with async_session() as sess:
        job = EmailJob(job_id=job_id, owner_id=owner_id, total=total, processed=0)
        sess.add(job)
        await sess.commit()
        await sess.refresh(job)
        return job

async def update_job_processed(job_id: str, processed_inc: int = 1, status: str = None):
    async with async_session() as sess:
        q = select(EmailJob).where(EmailJob.job_id == job_id)
        res = await sess.execute(q)
        job = res.scalar_one_or_none()
        if job:
            job.processed = (job.processed or 0) + processed_inc
            if status:
                job.status = status
            sess.add(job)
            await sess.commit()
            await sess.refresh(job)
            return job
        return None

async def insert_result(data: dict):
    async with async_session() as sess:
        r = EmailResult(**data)
        sess.add(r)
        await sess.commit()
        await sess.refresh(r)
        return r
