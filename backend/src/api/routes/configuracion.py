from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from database import get_db
from models.usuario import Usuario
from schemas.configuracion import ConfiguracionInput, ConfiguracionResponse
from services.config_service import create_config_version, get_active_config, list_config_history

router = APIRouter(prefix="/configuracion", tags=["configuracion"])


@router.get("", response_model=ConfiguracionResponse)
async def get_configuracion_route(
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> ConfiguracionResponse:
    config = await get_active_config(db)
    return ConfiguracionResponse.model_validate(config)


@router.post("", response_model=ConfiguracionResponse, status_code=status.HTTP_201_CREATED)
async def create_configuracion_route(
    payload: ConfiguracionInput,
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> ConfiguracionResponse:
    config = await create_config_version(db, payload, created_by=user.id)
    return ConfiguracionResponse.model_validate(config)


@router.get("/history", response_model=list[ConfiguracionResponse])
async def get_configuracion_history_route(
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> list[ConfiguracionResponse]:
    rows = await list_config_history(db)
    return [ConfiguracionResponse.model_validate(row) for row in rows]
