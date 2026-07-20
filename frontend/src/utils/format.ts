import type { Escribano, EscribanoResponse, EstadoEscritura } from "@/types/api";

export function formatMoney(value: string): string {
  const amount = Number(value);
  if (Number.isNaN(amount)) {
    return value;
  }
  return new Intl.NumberFormat("es-AR", {
    style: "currency",
    currency: "ARS",
    minimumFractionDigits: 2,
  }).format(amount);
}

/** Integer percent of costo_total collected; null when costo_total is zero or invalid. */
export function formatCobroPercent(totalPagado: string, costoTotal: string): number | null {
  const pagado = Number(totalPagado);
  const costo = Number(costoTotal);
  if (Number.isNaN(pagado) || Number.isNaN(costo) || costo <= 0) {
    return null;
  }
  return Math.round((pagado / costo) * 100);
}

export function formatDate(value: string): string {
  return new Intl.DateTimeFormat("es-AR", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function formatDateOnly(value: string): string {
  const parts = value.split("-").map(Number);
  if (parts.length !== 3 || parts.some((part) => Number.isNaN(part))) {
    return value;
  }
  const [year, month, day] = parts;
  return new Intl.DateTimeFormat("es-AR", { dateStyle: "medium" }).format(
    new Date(year, month - 1, day),
  );
}

const ESCRIBANO_LABELS: Record<Escribano, string> = {
  costanza: "Costanza",
  gabriel: "Gabriel",
  victoria: "Victoria",
};

export function labelEscribano(escribano: Escribano): string {
  return ESCRIBANO_LABELS[escribano];
}

export function displayEscribanoNombre(
  escribanoId: string,
  nombre: string,
  escribanos?: EscribanoResponse[],
): string {
  const record = escribanos?.find((item) => item.id === escribanoId);
  if (record && !record.activo) {
    return `${nombre} (inactivo)`;
  }
  return nombre;
}

export function labelEstado(estado: EstadoEscritura): string {
  return estado === "abierta" ? "Abierta" : "Cerrada";
}

const MONTH_NAMES = [
  "Enero",
  "Febrero",
  "Marzo",
  "Abril",
  "Mayo",
  "Junio",
  "Julio",
  "Agosto",
  "Septiembre",
  "Octubre",
  "Noviembre",
  "Diciembre",
] as const;

export function formatMonthYear(anio: number, mes: number): string {
  const name = MONTH_NAMES[mes - 1] ?? String(mes);
  return `${name} ${anio}`;
}

export function getDefaultPeriod(): { anio: number; mes: number } {
  const now = new Date();
  return { anio: now.getFullYear(), mes: now.getMonth() + 1 };
}

export { MONTH_NAMES };
