import { apiFetch } from "@/api/client";
import type { PagoColegioInput, PagoColegioResponse } from "@/types/api";

export function createPagoColegio(
  escrituraId: string,
  payload: PagoColegioInput,
): Promise<PagoColegioResponse> {
  return apiFetch(`/escrituras/${escrituraId}/pagos-colegio`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
