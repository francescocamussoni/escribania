import type { TipoPagoEscribania, TipoPagoLibroSalida } from "@/types/api";

export const TIPO_PAGO_ESCRIBANIA_OPTIONS: Array<{
  value: TipoPagoEscribania;
  label: string;
}> = [
  { value: "colegio", label: "Colegio" },
  { value: "otros", label: "Otros" },
];

export function labelTipoPagoEscribania(tipo: TipoPagoEscribania): string {
  return TIPO_PAGO_ESCRIBANIA_OPTIONS.find((option) => option.value === tipo)?.label ?? tipo;
}

export function labelTipoPagoLibroSalida(tipo: TipoPagoLibroSalida): string {
  return labelTipoPagoEscribania(tipo);
}
