from pydantic import BaseModel, ConfigDict

from models.escritura import Escribano, EstadoEscritura
from schemas.common import MoneyStr


class LiquidacionEscrituraItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    escritura_id: str
    nombre: str
    estado: EstadoEscritura
    honorario_principal: MoneyStr
    certificacion: MoneyStr
    subtotal: MoneyStr


class LiquidacionEscribano(BaseModel):
    escribano: Escribano
    total: MoneyStr
    escrituras: list[LiquidacionEscrituraItem]


class LiquidacionResumen(BaseModel):
    anio: int
    mes: int
    total_costanza: MoneyStr
    total_gabriel: MoneyStr
    total_victoria: MoneyStr
    total_global: MoneyStr
    por_escribano: list[LiquidacionEscribano]
