from pydantic import BaseModel, ConfigDict

from models.escritura import EstadoEscritura
from schemas.common import MoneyStr


class LiquidacionEscrituraItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    escritura_id: str
    nombre: str
    estado: EstadoEscritura
    monto_cobrado: MoneyStr
    neto_impuestos: MoneyStr


class LiquidacionEscribano(BaseModel):
    escribano_id: str
    escribano_nombre: str
    total: MoneyStr
    escrituras: list[LiquidacionEscrituraItem]


class LiquidacionResumen(BaseModel):
    anio: int
    mes: int
    total_costanza: MoneyStr
    total_gabriel: MoneyStr
    total_monica: MoneyStr
    total_global: MoneyStr
    por_escribano: list[LiquidacionEscribano]
