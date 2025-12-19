from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

from .. import crud, schemas, auth
from ..auth import create_access_token, get_password_hash, verify_password

# Definir router
auth_router = APIRouter(prefix="/auth", tags=["auth"])

# Registro de usuario
@auth_router.post("/register", response_model=schemas.UserRead)
async def register(user: schemas.UserCreate):
    hashed = get_password_hash(user.password)
    dbu = await crud.create_user(user.email, hashed)
    if not dbu:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="User already exists")
    return dbu

# Login / Token
@auth_router.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await crud.get_user_by_email(form_data.username)
    if not user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Incorrect credentials")
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Incorrect credentials")
    access_token_expires = timedelta(minutes=30)
    token = create_access_token(
        {"sub": user.email, "is_admin": user.is_admin},
        expires_delta=access_token_expires
    )
    return {"access_token": token, "token_type": "bearer"}

