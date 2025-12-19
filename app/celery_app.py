from celery import Celery
import os

BROKER = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

celery = Celery("email_verifier", broker=BROKER, backend=BACKEND)

# Configuración Celery básica
celery.conf.update(
    task_acks_late=True,       # ack task after execution
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    task_time_limit=300,      # límite por tarea (segundos)
    task_soft_time_limit=240,
)
