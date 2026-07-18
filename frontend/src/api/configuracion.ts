import { apiFetch } from "@/api/client";
import type { ConfiguracionInput, ConfiguracionResponse } from "@/types/api";

export function getConfiguracion(): Promise<ConfiguracionResponse> {
  return apiFetch("/configuracion");
}

export function createConfiguracion(payload: ConfiguracionInput): Promise<ConfiguracionResponse> {
  return apiFetch("/configuracion", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getConfiguracionHistory(): Promise<ConfiguracionResponse[]> {
  return apiFetch("/configuracion/history");
}
