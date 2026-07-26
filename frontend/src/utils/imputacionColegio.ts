import type { ImputacionPagoColegio } from "@/types/api";

export const IMPUTACION_PAGO_COLEGIO_OPTIONS: Array<{
  value: ImputacionPagoColegio;
  label: string;
}> = [
  { value: "total_impuestos", label: "Total impuestos / Corresponde" },
  { value: "honorarios_varios", label: "Honorarios varios" },
  { value: "otro", label: "Otro" },
];

export function labelImputacionPagoColegio(imputacion: ImputacionPagoColegio): string {
  return IMPUTACION_PAGO_COLEGIO_OPTIONS.find((option) => option.value === imputacion)?.label ?? imputacion;
}
