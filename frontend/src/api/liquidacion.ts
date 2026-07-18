import { apiFetch } from "@/api/client";
import type { LiquidacionResumen } from "@/types/api";

export interface PeriodParams {
  anio: number;
  mes: number;
}

export function getLiquidacion({ anio, mes }: PeriodParams): Promise<LiquidacionResumen> {
  return apiFetch(`/liquidacion?anio=${anio}&mes=${mes}`);
}
