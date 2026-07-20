from __future__ import annotations

from datetime import date
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from schemas.common import MoneyStr


class CasaCotizacion(str, Enum):
    BOLSA = "bolsa"
    OFICIAL = "oficial"


class CotizacionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    casa: CasaCotizacion
    fecha: date
    compra: MoneyStr
    venta: MoneyStr
    source: str = Field(description="api | cache | fallback")


class CotizacionAPIError(Exception):
    """Raised when the external exchange-rate API is unavailable."""


class CotizacionNoDisponibleError(Exception):
    """Raised when no rate exists for the requested date."""
