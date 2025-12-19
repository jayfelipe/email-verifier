from fastapi import APIRouter, Depends
from fastapi import HTTPException, status

admin_router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)

@admin_router.get("/health")
def admin_health_check():
    return {"status": "ok", "message": "Admin router running"}
