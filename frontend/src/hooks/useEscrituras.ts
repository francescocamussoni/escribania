import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  closeEscritura,
  createEscritura,
  type EscrituraListFilters,
  getEscritura,
  listEscrituras,
  updateEscritura,
} from "@/api/escrituras";
import type { EscrituraInput, EscrituraUpdate } from "@/types/api";

export function useEscrituras(filters?: EscrituraListFilters) {
  return useQuery({
    queryKey: ["escrituras", filters ?? {}],
    queryFn: () => listEscrituras(filters),
  });
}

export function useEscritura(id: string | undefined) {
  return useQuery({
    queryKey: ["escritura", id],
    queryFn: () => getEscritura(id!),
    enabled: Boolean(id),
  });
}

export function useCreateEscritura() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: EscrituraInput) => createEscritura(payload),
    onSuccess: (data) => {
      void queryClient.invalidateQueries({ queryKey: ["escrituras"] });
      void queryClient.setQueryData(["escritura", data.id], data);
    },
  });
}

export function usePatchEscritura(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: EscrituraUpdate) => updateEscritura(id, payload),
    onSuccess: (data) => {
      void queryClient.invalidateQueries({ queryKey: ["escrituras"] });
      void queryClient.setQueryData(["escritura", id], data);
    },
  });
}

export function useCloseEscritura(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => closeEscritura(id),
    onSuccess: (data) => {
      void queryClient.invalidateQueries({ queryKey: ["escrituras"] });
      void queryClient.setQueryData(["escritura", id], data);
      void queryClient.invalidateQueries({ queryKey: ["liquidacion"] });
      void queryClient.invalidateQueries({ queryKey: ["salarios"] });
      void queryClient.invalidateQueries({ queryKey: ["libros"] });
    },
  });
}
