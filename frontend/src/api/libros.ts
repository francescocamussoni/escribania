import { apiFetch } from "@/api/client";
import type { LibroResponse } from "@/types/api";
import type { PeriodParams } from "@/api/liquidacion";

export function getLibroEntrada({ anio, mes }: PeriodParams): Promise<LibroResponse> {
  return apiFetch(`/libros/entrada?anio=${anio}&mes=${mes}`);
}

export function getLibroSalida({ anio, mes }: PeriodParams): Promise<LibroResponse> {
  return apiFetch(`/libros/salida?anio=${anio}&mes=${mes}`);
}
