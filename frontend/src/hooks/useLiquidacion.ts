import { useQuery } from "@tanstack/react-query";
import { getLiquidacion, type PeriodParams } from "@/api/liquidacion";

export function useLiquidacion(params: PeriodParams) {
  return useQuery({
    queryKey: ["liquidacion", params.anio, params.mes],
    queryFn: () => getLiquidacion(params),
  });
}
