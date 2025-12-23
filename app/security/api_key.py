from fastapi import Request, HTTPException, status
from app.config import settings

API_KEY_HEADER = "X-API-Key"

async def verify_api_key(request: Request):
    api_key = request.headers.get(API_KEY_HEADER)

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key missing",
        )

    if api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )
