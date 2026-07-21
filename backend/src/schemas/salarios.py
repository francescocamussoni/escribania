from pydantic import BaseModel

from schemas.common import MoneyStr
from schemas.liquidacion import LiquidacionEscrituraItem


class PagoEscribano(BaseModel):
    nombre: str
    monto_total: MoneyStr
    deduccion_gastos_extraordinarios: MoneyStr
    monto_neto: MoneyStr
    escrituras: list[LiquidacionEscrituraItem]


class PagoSecretaria(BaseModel):
    nombre: str
    monto: MoneyStr
    base_total: MoneyStr


class PagoSalariosResumen(BaseModel):
    anio: int
    mes: int
    escribanos: list[PagoEscribano]
    secretarias: list[PagoSecretaria]
    total_gastos_extraordinarios: MoneyStr
    advertencia_reparto: str | None = None
