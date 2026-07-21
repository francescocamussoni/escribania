import { apiFetch } from "@/api/client";
import type {
  ImpuestoInput,
  ImpuestoResponse,
  ImpuestosListResponse,
  ImpuestoUpdate,
  PagoImpuestoInput,
  PagoImpuestoClienteResponse,
  PagoImpuestoEscribaniaResponse,
} from "@/types/api";

export function listImpuestos(escrituraId: string): Promise<ImpuestosListResponse> {
  return apiFetch(`/escrituras/${escrituraId}/impuestos`);
}

export function createImpuesto(
  escrituraId: string,
  payload: ImpuestoInput,
): Promise<ImpuestoResponse> {
  return apiFetch(`/escrituras/${escrituraId}/impuestos`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateImpuesto(
  escrituraId: string,
  impuestoId: string,
  payload: ImpuestoUpdate,
): Promise<ImpuestoResponse> {
  return apiFetch(`/escrituras/${escrituraId}/impuestos/${impuestoId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteImpuesto(escrituraId: string, impuestoId: string): Promise<void> {
  return apiFetch(`/escrituras/${escrituraId}/impuestos/${impuestoId}`, {
    method: "DELETE",
  });
}

export function upsertPagoImpuestoCliente(
  escrituraId: string,
  impuestoId: string,
  payload: PagoImpuestoInput,
): Promise<PagoImpuestoClienteResponse> {
  return apiFetch(`/escrituras/${escrituraId}/impuestos/${impuestoId}/pago-cliente`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updatePagoImpuestoCliente(
  escrituraId: string,
  impuestoId: string,
  payload: PagoImpuestoInput,
): Promise<PagoImpuestoClienteResponse> {
  return apiFetch(`/escrituras/${escrituraId}/impuestos/${impuestoId}/pago-cliente`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deletePagoImpuestoCliente(escrituraId: string, impuestoId: string): Promise<void> {
  return apiFetch(`/escrituras/${escrituraId}/impuestos/${impuestoId}/pago-cliente`, {
    method: "DELETE",
  });
}

export function upsertPagoImpuestoEscribania(
  escrituraId: string,
  impuestoId: string,
  payload: PagoImpuestoInput,
): Promise<PagoImpuestoEscribaniaResponse> {
  return apiFetch(`/escrituras/${escrituraId}/impuestos/${impuestoId}/pago-escribania`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updatePagoImpuestoEscribania(
  escrituraId: string,
  impuestoId: string,
  payload: PagoImpuestoInput,
): Promise<PagoImpuestoEscribaniaResponse> {
  return apiFetch(`/escrituras/${escrituraId}/impuestos/${impuestoId}/pago-escribania`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deletePagoImpuestoEscribania(
  escrituraId: string,
  impuestoId: string,
): Promise<void> {
  return apiFetch(`/escrituras/${escrituraId}/impuestos/${impuestoId}/pago-escribania`, {
    method: "DELETE",
  });
}
