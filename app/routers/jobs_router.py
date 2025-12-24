# backend/app/routers/jobs_router.py
from fastapi import APIRouter, Depends
import uuid

from app.security.api_key import verify_api_key
from ..schemas import JobCreate, JobRead
from ..crud import create_job
from ..tasks import enqueue_job

jobs_router = APIRouter(
    prefix="/jobs",
    tags=["jobs"],
    dependencies=[Depends(verify_api_key)]  # 🔐 API KEY
)

@jobs_router.post("/", response_model=JobRead)
async def create_job_endpoint(job: JobCreate):
    job_id = str(uuid.uuid4())

    # 🔹 SIN usuario hasta que exista auth real
    await create_job(
        job_id=job_id,
        owner_id=None,
        total=len(job.emails)
    )

    # 🔹 Encolar job sin owner
    enqueue_job(
        job_id=job_id,
        owner_id=None,
        emails=job.emails
    )

    return JobRead(
        job_id=job_id,
        status="queued",
        total=len(job.emails),
        processed=0
    )






