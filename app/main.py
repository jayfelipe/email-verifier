from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import init_db

# Routers importados con nombres correctos
from .routers.auth_router import auth_router
from .routers.jobs_router import jobs_router
from .routers.admin_router import admin_router

app = FastAPI(title=settings.APP_NAME)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cambia por tus dominios si quieres seguridad
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(auth_router)
app.include_router(jobs_router)
app.include_router(admin_router)

# Evento de startup
@app.on_event("startup")
async def on_startup():
    await init_db()



