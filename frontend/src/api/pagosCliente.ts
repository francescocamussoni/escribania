import { apiFetch } from "@/api/client";
import type { PagoClienteInput, PagoClienteResponse } from "@/types/api";

export function createPagoCliente(
  escrituraId: string,
  payload: PagoClienteInput,
): Promise<PagoClienteResponse> {
  return apiFetch(`/escrituras/${escrituraId}/pagos-cliente`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
