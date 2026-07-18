import { useQuery } from "@tanstack/react-query";
import { getSalarios } from "@/api/salarios";
import type { PeriodParams } from "@/api/liquidacion";

export function useSalarios(params: PeriodParams) {
  return useQuery({
    queryKey: ["salarios", params.anio, params.mes],
    queryFn: () => getSalarios(params),
  });
}
