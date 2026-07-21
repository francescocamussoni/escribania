import { ApiRequestError } from "@/api/client";
import { formatMoney } from "@/utils/format";

const KNOWN_API_MESSAGES: Record<string, string> = {
  "An active escribano with this name already exists":
    "Ya existe un escribano activo con ese nombre.",
  "An active employee with this name already exists":
    "Ya existe una empleada activa con ese nombre.",
  "sueldo must be greater than 0": "El sueldo debe ser mayor a cero.",
  "Cannot modify a closed escritura": "No se puede modificar una escritura cerrada.",
  "Escritura is already closed": "La escritura ya está cerrada.",
  "No se puede cerrar la escritura: saldo pendiente de cobro":
    "No se puede cerrar la escritura: hay saldo pendiente de cobro.",
  "No se puede cerrar la escritura: balance de impuestos pendiente":
    "No se puede cerrar la escritura: el balance de impuestos no está en cero.",
  "No se puede cerrar la escritura: impuestos con pagos incompletos":
    "No se puede cerrar la escritura: hay impuestos con pagos incompletos.",
  "Cannot delete impuesto with registered payments":
    "No se puede eliminar un impuesto que tiene pagos registrados.",
  "No se pudo consultar la cotización oficial":
    "No se pudo consultar la cotización oficial. Podés ingresar los valores manualmente.",
};

function extractDetailMessage(detail: string | Record<string, unknown> | undefined): string | null {
  if (typeof detail === "string") {
    return detail;
  }
  if (detail && typeof detail === "object" && typeof detail.detail === "string") {
    return detail.detail;
  }
  return null;
}

function extractSaldoPendiente(detail: string | Record<string, unknown> | undefined): string | null {
  if (detail && typeof detail === "object" && typeof detail.saldo_pendiente === "string") {
    return detail.saldo_pendiente;
  }
  return null;
}

function extractBalanceImpuestos(
  detail: string | Record<string, unknown> | undefined,
): string | null {
  if (detail && typeof detail === "object" && typeof detail.balance === "string") {
    return detail.balance;
  }
  return null;
}

function extractImpuestosPendientesCount(
  detail: string | Record<string, unknown> | undefined,
): number | null {
  if (detail && typeof detail === "object" && Array.isArray(detail.impuestos_pendientes)) {
    return detail.impuestos_pendientes.length;
  }
  return null;
}

export function closeEscrituraSaldoMessage(error: unknown): string | null {
  if (!(error instanceof ApiRequestError) || error.status !== 409) {
    return null;
  }
  const saldo = extractSaldoPendiente(error.body?.detail);
  if (!saldo) {
    return null;
  }
  return `No se puede cerrar la escritura. Saldo pendiente: ${formatMoney(saldo)}.`;
}

export function closeEscrituraImpuestosMessage(error: unknown): string | null {
  if (!(error instanceof ApiRequestError) || error.status !== 409) {
    return null;
  }
  const detail = error.body?.detail;
  const balance = extractBalanceImpuestos(detail);
  if (balance) {
    return `No se puede cerrar la escritura. Balance de impuestos: ${formatMoney(balance)}.`;
  }
  const pendientes = extractImpuestosPendientesCount(detail);
  if (pendientes !== null && pendientes > 0) {
    return `No se puede cerrar la escritura. ${pendientes} impuesto(s) con pagos incompletos.`;
  }
  return null;
}

function translateApiMessage(message: string): string {
  return KNOWN_API_MESSAGES[message] ?? message;
}

export function friendlyApiError(error: unknown, fallback: string): string {
  if (error instanceof ApiRequestError) {
    const detailMessage = extractDetailMessage(error.body?.detail) ?? error.message;

    if (error.status === 401) {
      if (detailMessage === "Invalid credentials") {
        return "Usuario o contraseña incorrectos.";
      }
      return "Tu sesión expiró. Volvé a iniciar sesión.";
    }
    if (error.status === 403) {
      return "No tenés permiso para realizar esta acción.";
    }
    if (error.status === 409) {
      return translateApiMessage(detailMessage);
    }
    if (error.status === 413) {
      return "Los datos enviados son demasiado grandes.";
    }
    if (error.status === 422) {
      const translated = translateApiMessage(detailMessage);
      if (translated !== detailMessage) {
        return translated;
      }
      return "Revisá los valores ingresados e intentá de nuevo.";
    }
    if (error.status === 429) {
      return "Demasiados intentos. Esperá un momento e intentá de nuevo.";
    }
    if (error.status === 503) {
      return translateApiMessage(detailMessage);
    }
    if (error.status >= 500) {
      return "El servidor no está disponible en este momento. Intentá más tarde.";
    }
    return translateApiMessage(detailMessage);
  }
  return fallback;
}
