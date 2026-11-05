from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from schemas.common import MoneyStr

FacturaLineaSeccion = Literal["honorarios", "honorarios_varios", "impuestos", "gastos_admin"]


class FacturaLineaItem(BaseModel):
    key: str
    label: str
    monto: MoneyStr
    monto_efectivo: MoneyStr
    habilitada: bool
    seccion: FacturaLineaSeccion


class FacturaPrincipalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID | None = None
    escritura_id: UUID | None = None
    monto_base_mep: Decimal
    precio_base_nacion: Decimal
    honorario_principal: Decimal
    certificacion: Decimal
    suma_hon_cert: Decimal
    aporte_12pct: Decimal
    cinco_pct_hon: Decimal
    firma_honorarios: Decimal
    subtotal_honorarios: Decimal
    art2_a: Decimal
    art12_a: Decimal
    art12_c: Decimal
    art12_f: Decimal
    total_leyes_notariales: Decimal
    tasa_3pm: Decimal
    sellos: Decimal
    tasa_75pm: Decimal
    firma_impuestos: Decimal
    total_impuestos: Decimal
    inscripcion: Decimal
    protocolo: Decimal
    ii_certificados: Decimal
    municipio: Decimal
    fotocopias_urgentes: Decimal
    certificaciones_extra: Decimal
    catastro: Decimal
    testimonio: Decimal
    concuerda: Decimal
    informes_notariales: Decimal
    extracto: Decimal
    fotocopias_simples: Decimal
    tasas_minimas: Decimal
    total_gastos_admin: Decimal
    dif_honorarios: Decimal
    total_parcial: Decimal
    total_sin_iva: Decimal
    iva: Decimal
    total_factura: Decimal
    updated_at: datetime | None = None
    lineas_deshabilitadas: list[str] = Field(default_factory=list)
    lineas: list[FacturaLineaItem] = Field(default_factory=list)
    total_impuestos_efectivo: MoneyStr | None = None
