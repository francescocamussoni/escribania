from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ConfiguracionInput(BaseModel):
    descripcion: str | None = None
    honorario_pct: Decimal = Field(default=Decimal("0.024"))
    honorario_min: Decimal
    certificacion_pct: Decimal = Field(default=Decimal("0.003"))
    aporte_pct: Decimal = Field(default=Decimal("0.12"))
    cinco_pct_hon_pct: Decimal = Field(default=Decimal("0.05"))
    cinco_pct_hon_min: Decimal
    firma_honorarios: Decimal
    art2_a_pct: Decimal = Field(default=Decimal("0.0048"))
    art12_a_pct: Decimal = Field(default=Decimal("0.004"))
    art12_a_min: Decimal
    art12_c_pct: Decimal = Field(default=Decimal("0.0012"))
    art12_f: Decimal
    tasa_3pm_pct: Decimal = Field(default=Decimal("0.003"))
    sellos_pct: Decimal = Field(default=Decimal("0.025"))
    sellos_ajuste_fijo: Decimal = Field(default=Decimal("250.00"))
    tasa_75pm_pct: Decimal = Field(default=Decimal("0.0075"))
    firma_impuestos: Decimal
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
    salario_secretarias_total: Decimal


class ConfiguracionResponse(ConfiguracionInput):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    version: int
    created_at: datetime
    created_by: UUID | None = None
