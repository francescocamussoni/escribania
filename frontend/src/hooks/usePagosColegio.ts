import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createPagoColegio } from "@/api/pagosColegio";
import type { PagoColegioInput } from "@/types/api";

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
