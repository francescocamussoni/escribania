import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createEscribano, deactivateEscribano, listEscribanos, updateEscribano } from "@/api/escribanos";
import type { EscribanoUpdateRequest } from "@/types/api";

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

export function useUpdateEscribano() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: EscribanoUpdateRequest }) =>
      updateEscribano(id, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["escribanos"] });
      void queryClient.invalidateQueries({ queryKey: ["escrituras"] });
    },
  });
}
