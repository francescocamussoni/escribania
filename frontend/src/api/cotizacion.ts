import { apiFetch } from "@/api/client";
import type { CasaCotizacion, CotizacionResponse } from "@/types/api";

export function getCotizacion(casa: CasaCotizacion, fecha: string): Promise<CotizacionResponse> {
  const params = new URLSearchParams({ casa, fecha });
  return apiFetch(`/cotizacion?${params.toString()}`);
}
