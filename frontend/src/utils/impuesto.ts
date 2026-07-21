import type { DireccionProrrateo, EstadoPagos, TipoImpuesto } from "@/types/api";

const TIPO_LABELS: Record<TipoImpuesto, string> = {
  API: "API",
  TGI: "TGI",
  AGUAS_SANTAFESINAS: "Aguas Santafesinas",
  EPE: "EPE",
  EXPENSAS: "Expensas",
  LITORAL_GAS: "Litoral Gas",
};

const ESTADO_PAGOS_LABELS: Record<EstadoPagos, string> = {
  sin_pagos: "Sin pagos",
  solo_cliente: "Solo cliente",
  solo_escribania: "Solo escribanía",
  completos: "Completos",
};

const DIRECCION_LABELS: Record<DireccionProrrateo, string> = {
  hacia_atras: "Hacia atrás",
  hacia_adelante: "Hacia adelante",
};

export function labelTipoImpuesto(tipo: TipoImpuesto): string {
  return TIPO_LABELS[tipo];
}

export function labelEstadoPagos(estado: EstadoPagos): string {
  return ESTADO_PAGOS_LABELS[estado];
}

export function labelDireccionProrrateo(direccion: DireccionProrrateo): string {
  return DIRECCION_LABELS[direccion];
}

export const TIPOS_IMPUESTO: TipoImpuesto[] = [
  "API",
  "TGI",
  "AGUAS_SANTAFESINAS",
  "EPE",
  "EXPENSAS",
  "LITORAL_GAS",
];

function parseIsoDate(value: string): Date | null {
  const parts = value.split("-").map(Number);
  if (parts.length !== 3 || parts.some((part) => Number.isNaN(part))) {
    return null;
  }
  return new Date(parts[0], parts[1] - 1, parts[2]);
}

/** Mirrors backend calc_monto_sugerido for live preview in the form. */
export function calcMontoSugeridoPreview(
  montoTotal: string,
  periodoInicio: string,
  periodoFin: string,
  fechaCorte: string,
  direccion: DireccionProrrateo,
): string | null {
  const monto = Number(montoTotal);
  const inicio = parseIsoDate(periodoInicio);
  const fin = parseIsoDate(periodoFin);
  const corte = parseIsoDate(fechaCorte);
  if (
    Number.isNaN(monto) ||
    monto <= 0 ||
    !inicio ||
    !fin ||
    !corte ||
    fin < inicio ||
    corte < inicio ||
    corte > fin
  ) {
    return null;
  }

  const diasPeriodo = Math.floor((fin.getTime() - inicio.getTime()) / 86_400_000) + 1;
  let tramoInicio: Date;
  let tramoFin: Date;
  if (direccion === "hacia_atras") {
    tramoInicio = inicio;
    tramoFin = corte;
  } else {
    tramoInicio = new Date(corte.getFullYear(), corte.getMonth(), corte.getDate() + 1);
    tramoFin = fin;
  }
  if (tramoInicio > tramoFin) {
    return "0.00";
  }
  const diasTramo = Math.floor((tramoFin.getTime() - tramoInicio.getTime()) / 86_400_000) + 1;
  const sugerido = (monto * diasTramo) / diasPeriodo;
  return sugerido.toFixed(2);
}
