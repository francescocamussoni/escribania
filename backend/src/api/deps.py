from fastapi import Depends, HTTPException, Request, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import Settings, get_settings
from database import get_db
from models.usuario import Usuario
from services.auth import ACCESS_TOKEN_COOKIE, decode_access_token


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> Usuario:
    token = request.cookies.get(ACCESS_TOKEN_COOKIE)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        user_id = decode_access_token(token, settings)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from None

    user = await db.scalar(select(Usuario).where(Usuario.id == user_id))
    if user is None or not user.activo:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    request.state.user_id = str(user.id)
    return user


async def get_optional_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> Usuario | None:
    token = request.cookies.get(ACCESS_TOKEN_COOKIE)
    if not token:
        return None

    try:
        user_id = decode_access_token(token, settings)
    except JWTError:
        return None

    user = await db.scalar(select(Usuario).where(Usuario.id == user_id))
    if user is None or not user.activo:
        return None

    request.state.user_id = str(user.id)
    return user
