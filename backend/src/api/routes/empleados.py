from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from database import get_db
from models.usuario import Usuario
from schemas.empleado import EmpleadoCreateRequest, EmpleadoResponse, EmpleadoUpdateRequest
from services.empleado_service import (
    EmpleadoDuplicateError,
    EmpleadoInvalidSueldoError,
    EmpleadoNotFoundError,
    create,
    list_active,
    soft_delete,
    update_sueldo,
)

router = APIRouter(prefix="/configuracion/empleados", tags=["empleados"])


@router.get("", response_model=list[EmpleadoResponse])
async def list_empleados_route(
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> list[EmpleadoResponse]:
    rows = await list_active(db)
    return [EmpleadoResponse.from_orm_row(row) for row in rows]


@router.post("", response_model=EmpleadoResponse, status_code=status.HTTP_201_CREATED)
async def create_empleado_route(
    payload: EmpleadoCreateRequest,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> EmpleadoResponse:
    try:
        row = await create(db, payload.nombre, payload.sueldo)
    except EmpleadoDuplicateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except EmpleadoInvalidSueldoError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return EmpleadoResponse.from_orm_row(row)


@router.patch("/{empleado_id}", response_model=EmpleadoResponse)
async def update_empleado_sueldo_route(
    empleado_id: UUID,
    payload: EmpleadoUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> EmpleadoResponse:
    try:
        row = await update_sueldo(db, empleado_id, payload.sueldo)
    except EmpleadoNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except EmpleadoInvalidSueldoError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return EmpleadoResponse.from_orm_row(row)


@router.delete("/{empleado_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_empleado_route(
    empleado_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> Response:
    try:
        await soft_delete(db, empleado_id)
    except EmpleadoNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
