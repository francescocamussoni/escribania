from pydantic import BaseModel

from schemas.common import MoneyStr
from schemas.liquidacion import LiquidacionEscrituraItem


class PagoEscribano(BaseModel):
    nombre: str
    monto_total: MoneyStr
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
