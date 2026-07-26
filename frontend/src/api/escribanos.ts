import { apiFetch } from "@/api/client";
import type { EscribanoResponse, EscribanoUpdateRequest } from "@/types/api";

export function listEscribanos(includeInactive = false): Promise<EscribanoResponse[]> {
  const params = includeInactive ? "?include_inactive=true" : "";
  return apiFetch(`/configuracion/escribanos${params}`);
}

export function createEscribano(nombre: string): Promise<EscribanoResponse> {
  return apiFetch("/configuracion/escribanos", {
    method: "POST",
    body: JSON.stringify({ nombre }),
  });
}

export function deactivateEscribano(id: string, force = false): Promise<void> {
  const params = force ? "?force=true" : "";
  return apiFetch(`/configuracion/escribanos/${id}${params}`, {
    method: "DELETE",
  });
}

export function updateEscribano(
  id: string,
  payload: EscribanoUpdateRequest,
): Promise<EscribanoResponse> {
  return apiFetch(`/configuracion/escribanos/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}
