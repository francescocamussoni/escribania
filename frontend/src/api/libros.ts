import { apiFetch } from "@/api/client";
import type { LibroEntradaResponse, LibroSalidaResponse } from "@/types/api";
import type { PeriodParams } from "@/api/liquidacion";

export function getLibroEntrada({ anio, mes }: PeriodParams): Promise<LibroEntradaResponse> {
  return apiFetch(`/libros/entrada?anio=${anio}&mes=${mes}`);
}

export function getLibroSalida({ anio, mes }: PeriodParams): Promise<LibroSalidaResponse> {
  return apiFetch(`/libros/salida?anio=${anio}&mes=${mes}`);
}
