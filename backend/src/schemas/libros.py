from datetime import date

from pydantic import BaseModel, ConfigDict

from schemas.common import MoneyStr


class LibroLineaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    escritura_id: str
    escritura_nombre: str
    concepto: str
    monto: MoneyStr
    fecha_escritura: date


class LibroResponse(BaseModel):
    anio: int
    mes: int
    lineas: list[LibroLineaResponse]
    total: MoneyStr
