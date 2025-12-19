# backend/app/routers/jobs_router.py
from fastapi import APIRouter, BackgroundTasks, Depends
from typing import List
import uuid

from ..schemas import JobCreate, JobRead
# from ..auth import get_current_active_user  # Comentado para pruebas
from ..crud import create_job
from ..tasks import enqueue_job

jobs_router = APIRouter(
    prefix="/jobs",
    tags=["jobs"]
)

@jobs_router.post("/", response_model=JobRead)
async def create_job_endpoint(
    job: JobCreate,
    background_tasks: BackgroundTasks,
    # current_user = Depends(get_current_active_user)  # Comentado para pruebas
):
    # Usuario dummy para pruebas
    current_user = type("User", (), {"id": 1})()

    # Generar un ID único para el trabajo
    job_id = str(uuid.uuid4())

    # Crear el trabajo en la base de datos
    j = await create_job(
        job_id=job_id,
        owner_id=current_user.id,  # CORRECCIÓN: user_id → owner_id
        total=len(job.emails)
    )

    # Encolar el trabajo para procesamiento en segundo plano
    enqueue_job(job_id, current_user.id, job.emails)

    # Retornar información del trabajo
    return JobRead(
        job_id=job_id,
        status="queued",
        total=len(job.emails),
        processed=0
    )






