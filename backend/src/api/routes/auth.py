from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from config import Settings, get_settings
from database import get_db
from models.usuario import Usuario
from schemas.auth import LoginInput, UserResponse
from services.auth import (
    ACCESS_TOKEN_COOKIE,
    create_access_token,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _cookie_params(settings: Settings) -> dict:
    return {
        "key": ACCESS_TOKEN_COOKIE,
        "httponly": True,
        "secure": settings.environment != "local",
        "samesite": "strict",
        "path": "/",
        "max_age": settings.jwt_expiry_hours * 3600,
    }


def _delete_cookie_params(settings: Settings) -> dict:
    return {
        "key": ACCESS_TOKEN_COOKIE,
        "httponly": True,
        "secure": settings.environment != "local",
        "samesite": "strict",
        "path": "/",
    }


@router.post("/login", status_code=status.HTTP_200_OK)
async def login(
    payload: LoginInput,
    response: Response,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, str]:
    user = await db.scalar(select(Usuario).where(Usuario.username == payload.username))
    if user is None or not user.activo or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    user.last_login_at = datetime.now(UTC)
    await db.commit()

    token = create_access_token(user.id, settings)
    response.set_cookie(value=token, **_cookie_params(settings))
    return {"status": "ok"}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    settings: Settings = Depends(get_settings),
    _: Usuario = Depends(get_current_user),
) -> None:
    response.delete_cookie(**_delete_cookie_params(settings))


@router.get("/me", response_model=UserResponse)
async def me(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    return current_user
