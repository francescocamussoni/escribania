import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createImpuesto,
  deleteImpuesto,
  deletePagoImpuestoCliente,
  deletePagoImpuestoEscribania,
  listImpuestos,
  updateImpuesto,
  updatePagoImpuestoCliente,
  updatePagoImpuestoEscribania,
  upsertPagoImpuestoCliente,
  upsertPagoImpuestoEscribania,
} from "@/api/impuestos";
import type { ImpuestoInput, ImpuestoUpdate, PagoImpuestoInput } from "@/types/api";

function invalidateImpuestosCaches(
  queryClient: ReturnType<typeof useQueryClient>,
  escrituraId: string,
): void {
  void queryClient.invalidateQueries({ queryKey: ["impuestos", escrituraId] });
  void queryClient.invalidateQueries({ queryKey: ["escritura", escrituraId] });
  void queryClient.invalidateQueries({ queryKey: ["escrituras"] });
  void queryClient.invalidateQueries({ queryKey: ["libros"] });
  void queryClient.invalidateQueries({ queryKey: ["liquidacion"] });
  void queryClient.invalidateQueries({ queryKey: ["salarios"] });
}

export function useImpuestos(escrituraId: string) {
  return useQuery({
    queryKey: ["impuestos", escrituraId],
    queryFn: () => listImpuestos(escrituraId),
    enabled: Boolean(escrituraId),
  });
}

export function useCreateImpuesto(escrituraId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ImpuestoInput) => createImpuesto(escrituraId, payload),
    onSuccess: () => invalidateImpuestosCaches(queryClient, escrituraId),
  });
}

export function useUpdateImpuesto(escrituraId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ impuestoId, payload }: { impuestoId: string; payload: ImpuestoUpdate }) =>
      updateImpuesto(escrituraId, impuestoId, payload),
    onSuccess: () => invalidateImpuestosCaches(queryClient, escrituraId),
  });
}

export function useDeleteImpuesto(escrituraId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (impuestoId: string) => deleteImpuesto(escrituraId, impuestoId),
    onSuccess: () => invalidateImpuestosCaches(queryClient, escrituraId),
  });
}

export function useUpsertPagoImpuestoCliente(escrituraId: string, impuestoId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: PagoImpuestoInput) =>
      upsertPagoImpuestoCliente(escrituraId, impuestoId, payload),
    onSuccess: () => invalidateImpuestosCaches(queryClient, escrituraId),
  });
}

export function useUpdatePagoImpuestoCliente(escrituraId: string, impuestoId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: PagoImpuestoInput) =>
      updatePagoImpuestoCliente(escrituraId, impuestoId, payload),
    onSuccess: () => invalidateImpuestosCaches(queryClient, escrituraId),
  });
}

export function useDeletePagoImpuestoCliente(escrituraId: string, impuestoId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => deletePagoImpuestoCliente(escrituraId, impuestoId),
    onSuccess: () => invalidateImpuestosCaches(queryClient, escrituraId),
  });
}

export function useUpsertPagoImpuestoEscribania(escrituraId: string, impuestoId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: PagoImpuestoInput) =>
      upsertPagoImpuestoEscribania(escrituraId, impuestoId, payload),
    onSuccess: () => invalidateImpuestosCaches(queryClient, escrituraId),
  });
}

export function useUpdatePagoImpuestoEscribania(escrituraId: string, impuestoId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: PagoImpuestoInput) =>
      updatePagoImpuestoEscribania(escrituraId, impuestoId, payload),
    onSuccess: () => invalidateImpuestosCaches(queryClient, escrituraId),
  });
}

export function useDeletePagoImpuestoEscribania(escrituraId: string, impuestoId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => deletePagoImpuestoEscribania(escrituraId, impuestoId),
    onSuccess: () => invalidateImpuestosCaches(queryClient, escrituraId),
  });
}
