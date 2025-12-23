# backend/app/routers/jobs_router.py
from fastapi import APIRouter, BackgroundTasks, Depends
from typing import List
import uuid

from app.security.api_key import verify_api_key
from ..schemas import JobCreate, JobRead
from ..crud import create_job
from ..tasks import enqueue_job

jobs_router = APIRouter(
    prefix="/jobs",
    tags=["jobs"],
    dependencies=[Depends(verify_api_key)]
)

@jobs_router.post("/", response_model=JobRead)
async def create_job_endpoint(
    job: JobCreate,
    background_tasks: BackgroundTasks,
):
    current_user = type("User", (), {"id": 1})()

    job_id = str(uuid.uuid4())

    j = await create_job(
        job_id=job_id,
        owner_id=current_user.id,
        total=len(job.emails)
    )

    enqueue_job(job_id, current_user.id, job.emails)

    return JobRead(
        job_id=job_id,
        status="queued",
        total=len(job.emails),
        processed=0
    )






