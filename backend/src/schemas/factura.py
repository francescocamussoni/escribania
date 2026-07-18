from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


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
    total_factura: Decimal
    updated_at: datetime | None = None
