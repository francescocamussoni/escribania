import { apiFetch } from "@/api/client";
import type {
  PagoColegioBulkPreviewRequest,
  PagoColegioBulkPreviewResponse,
  PagoColegioBulkRequest,
  PagoColegioBulkResponse,
  PagoColegioInput,
  PagoColegioResponse,
} from "@/types/api";

export function createPagoColegio(
  escrituraId: string,
  payload: PagoColegioInput,
): Promise<PagoColegioResponse> {
  return apiFetch(`/escrituras/${escrituraId}/pagos-colegio`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function previewPagoColegioBulk(
  payload: PagoColegioBulkPreviewRequest,
): Promise<PagoColegioBulkPreviewResponse> {
  return apiFetch("/escrituras/pagos-colegio/bulk/preview", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function confirmPagoColegioBulk(
  payload: PagoColegioBulkRequest,
): Promise<PagoColegioBulkResponse> {
  return apiFetch("/escrituras/pagos-colegio/bulk", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
