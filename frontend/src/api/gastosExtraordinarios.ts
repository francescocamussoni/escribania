import { apiFetch } from "@/api/client";
import type { PeriodParams } from "@/api/liquidacion";
import type {
  GastoExtraordinarioInput,
  GastoExtraordinarioResponse,
  GastoExtraordinarioUpdate,
  GastosExtraordinariosListResponse,
} from "@/types/api";

export function listGastosExtraordinarios({
  anio,
  mes,
}: PeriodParams): Promise<GastosExtraordinariosListResponse> {
  return apiFetch(`/gastos-extraordinarios?anio=${anio}&mes=${mes}`);
}

export function createGastoExtraordinario(
  payload: GastoExtraordinarioInput,
): Promise<GastoExtraordinarioResponse> {
  return apiFetch("/gastos-extraordinarios", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateGastoExtraordinario(
  gastoId: string,
  payload: GastoExtraordinarioUpdate,
): Promise<GastoExtraordinarioResponse> {
  return apiFetch(`/gastos-extraordinarios/${gastoId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteGastoExtraordinario(gastoId: string): Promise<void> {
  return apiFetch(`/gastos-extraordinarios/${gastoId}`, {
    method: "DELETE",
  });
}
