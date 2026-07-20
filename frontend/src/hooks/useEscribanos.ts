import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createEscribano, deactivateEscribano, listEscribanos } from "@/api/escribanos";

export function useEscribanos(includeInactive = true) {
  return useQuery({
    queryKey: ["escribanos", { includeInactive }],
    queryFn: () => listEscribanos(includeInactive),
  });
}

export function useCreateEscribano() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (nombre: string) => createEscribano(nombre),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["escribanos"] });
    },
  });
}

export function useDeactivateEscribano() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, force }: { id: string; force?: boolean }) =>
      deactivateEscribano(id, force ?? false),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["escribanos"] });
    },
  });
}
