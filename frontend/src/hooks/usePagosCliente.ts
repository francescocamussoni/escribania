import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createPagoCliente } from "@/api/pagosCliente";
import type { PagoClienteInput } from "@/types/api";

export function useCreatePagoCliente(escrituraId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: PagoClienteInput) => createPagoCliente(escrituraId, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["escrituras"] });
      void queryClient.invalidateQueries({ queryKey: ["escritura", escrituraId] });
      void queryClient.invalidateQueries({ queryKey: ["liquidacion"] });
      void queryClient.invalidateQueries({ queryKey: ["salarios"] });
      void queryClient.invalidateQueries({ queryKey: ["libros"] });
    },
  });
}
