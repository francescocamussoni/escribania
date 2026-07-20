import { apiFetch } from "@/api/client";
import type {
  EscrituraInput,
  EscrituraListItem,
  EscrituraResponse,
  EscrituraUpdate,
  EstadoEscritura,
  GastoAdicionalInput,
  GastoAdicionalResponse,
} from "@/types/api";

export interface EscrituraListFilters {
  estado?: EstadoEscritura;
  escribano_id?: string;
  anio?: number;
  mes?: number;
}

function buildQuery(filters?: EscrituraListFilters): string {
  if (!filters) {
    return "";
  }
  const params = new URLSearchParams();
  if (filters.estado) {
    params.set("estado", filters.estado);
  }
  if (filters.escribano_id) {
    params.set("escribano_id", filters.escribano_id);
  }
  if (filters.anio !== undefined) {
    params.set("anio", String(filters.anio));
  }
  if (filters.mes !== undefined) {
    params.set("mes", String(filters.mes));
  }
  const query = params.toString();
  return query ? `?${query}` : "";
}

export function listEscrituras(filters?: EscrituraListFilters): Promise<EscrituraListItem[]> {
  return apiFetch(`/escrituras${buildQuery(filters)}`);
}

export function getEscritura(id: string): Promise<EscrituraResponse> {
  return apiFetch(`/escrituras/${id}`);
}

export function createEscritura(payload: EscrituraInput): Promise<EscrituraResponse> {
  return apiFetch("/escrituras", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateEscritura(id: string, payload: EscrituraUpdate): Promise<EscrituraResponse> {
  return apiFetch(`/escrituras/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function closeEscritura(id: string): Promise<EscrituraResponse> {
  return apiFetch(`/escrituras/${id}/close`, { method: "POST" });
}

export function addGasto(
  escrituraId: string,
  payload: GastoAdicionalInput,
): Promise<GastoAdicionalResponse> {
  return apiFetch(`/escrituras/${escrituraId}/gastos`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
