import { useQuery } from "@tanstack/react-query";
import { getLibroEntrada, getLibroSalida } from "@/api/libros";
import type { PeriodParams } from "@/api/liquidacion";

export function useLibroEntrada(params: PeriodParams) {
  return useQuery({
    queryKey: ["libros", "entrada", params.anio, params.mes],
    queryFn: () => getLibroEntrada(params),
  });
}

export function useLibroSalida(params: PeriodParams) {
  return useQuery({
    queryKey: ["libros", "salida", params.anio, params.mes],
    queryFn: () => getLibroSalida(params),
  });
}
