from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from database import get_db
from models.usuario import Usuario
from schemas.pago_cliente import PagoClienteInput, PagoClienteResponse
from services.escritura_errors import EscrituraClosedError, EscrituraNotFoundError
from services.pago_cliente_service import PagoClienteExcesoSaldoError, create_pago

router = APIRouter(prefix="/escrituras", tags=["pagos-cliente"])


@router.post(
    "/{escritura_id}/pagos-cliente",
    response_model=PagoClienteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_pago_cliente_route(
    escritura_id: UUID,
    payload: PagoClienteInput,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> PagoClienteResponse:
    try:
        pago = await create_pago(db, escritura_id, payload)
    except EscrituraNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except EscrituraClosedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except PagoClienteExcesoSaldoError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "detail": str(exc),
                "saldo_pendiente": format(exc.saldo_pendiente, "f"),
            },
        ) from exc
    return PagoClienteResponse.model_validate(pago)
