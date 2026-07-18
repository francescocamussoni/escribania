import { apiFetch } from "@/api/client";
import type { PagoSalariosResumen } from "@/types/api";
import type { PeriodParams } from "@/api/liquidacion";

export function getSalarios({ anio, mes }: PeriodParams): Promise<PagoSalariosResumen> {
  return apiFetch(`/salarios?anio=${anio}&mes=${mes}`);
}
