import type { Escribano, EstadoEscritura } from "@/types/api";

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

export function formatDate(value: string): string {
  return new Intl.DateTimeFormat("es-AR", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

const ESCRIBANO_LABELS: Record<Escribano, string> = {
  costanza: "Costanza",
  gabriel: "Gabriel",
  victoria: "Victoria",
};

export function labelEscribano(escribano: Escribano): string {
  return ESCRIBANO_LABELS[escribano];
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
