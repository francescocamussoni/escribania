import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createConfiguracion,
  getConfiguracion,
  getConfiguracionHistory,
} from "@/api/configuracion";
import type { ConfiguracionInput } from "@/types/api";

export function useConfiguracion() {
  return useQuery({
    queryKey: ["configuracion"],
    queryFn: getConfiguracion,
  });
}

export function useConfiguracionHistory() {
  return useQuery({
    queryKey: ["configuracion", "history"],
    queryFn: getConfiguracionHistory,
  });
}

export function useCreateConfiguracion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ConfiguracionInput) => createConfiguracion(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["configuracion"] });
    },
  });
}
