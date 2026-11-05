import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  confirmPagoColegioBulk,
  createPagoColegio,
  previewPagoColegioBulk,
} from "@/api/pagosColegio";
import type { PagoColegioBulkRequest, PagoColegioInput } from "@/types/api";

export function useCreatePagoColegio(escrituraId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: PagoColegioInput) => createPagoColegio(escrituraId, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["escrituras"] });
      void queryClient.invalidateQueries({ queryKey: ["escritura", escrituraId] });
      void queryClient.invalidateQueries({ queryKey: ["libros"] });
    },
  });
}

export function useConfirmPagoColegioBulk() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: PagoColegioBulkRequest) => confirmPagoColegioBulk(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["escrituras"] });
      void queryClient.invalidateQueries({ queryKey: ["escritura"] });
      void queryClient.invalidateQueries({ queryKey: ["libros"] });
    },
  });
}

export { previewPagoColegioBulk };
