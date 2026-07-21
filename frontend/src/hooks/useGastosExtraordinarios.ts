import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { PeriodParams } from "@/api/liquidacion";
import {
  createGastoExtraordinario,
  deleteGastoExtraordinario,
  listGastosExtraordinarios,
  updateGastoExtraordinario,
} from "@/api/gastosExtraordinarios";
import type { GastoExtraordinarioInput, GastoExtraordinarioUpdate } from "@/types/api";

function invalidateGastosCaches(
  queryClient: ReturnType<typeof useQueryClient>,
  params: PeriodParams,
): void {
  void queryClient.invalidateQueries({
    queryKey: ["gastos-extraordinarios", params.anio, params.mes],
  });
  void queryClient.invalidateQueries({ queryKey: ["libros"] });
  void queryClient.invalidateQueries({ queryKey: ["salarios"] });
}

export function useGastosExtraordinarios(params: PeriodParams) {
  return useQuery({
    queryKey: ["gastos-extraordinarios", params.anio, params.mes],
    queryFn: () => listGastosExtraordinarios(params),
  });
}

export function useCreateGastoExtraordinario(params: PeriodParams) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: GastoExtraordinarioInput) => createGastoExtraordinario(payload),
    onSuccess: () => invalidateGastosCaches(queryClient, params),
  });
}

export function useUpdateGastoExtraordinario(params: PeriodParams) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      gastoId,
      payload,
    }: {
      gastoId: string;
      payload: GastoExtraordinarioUpdate;
    }) => updateGastoExtraordinario(gastoId, payload),
    onSuccess: () => invalidateGastosCaches(queryClient, params),
  });
}

export function useDeleteGastoExtraordinario(params: PeriodParams) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (gastoId: string) => deleteGastoExtraordinario(gastoId),
    onSuccess: () => invalidateGastosCaches(queryClient, params),
  });
}
