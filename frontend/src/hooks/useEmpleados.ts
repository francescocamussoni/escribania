import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createEmpleado,
  deleteEmpleado,
  listEmpleados,
  updateSueldo,
} from "@/api/empleados";

function invalidateEmpleadoQueries(queryClient: ReturnType<typeof useQueryClient>) {
  void queryClient.invalidateQueries({ queryKey: ["empleados"] });
  void queryClient.invalidateQueries({ queryKey: ["salarios"] });
}

export function useEmpleados() {
  return useQuery({
    queryKey: ["empleados"],
    queryFn: listEmpleados,
  });
}

export function useCreateEmpleado() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ nombre, sueldo }: { nombre: string; sueldo: string }) =>
      createEmpleado(nombre, sueldo),
    onSuccess: () => invalidateEmpleadoQueries(queryClient),
  });
}

export function useUpdateSueldo() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, sueldo }: { id: string; sueldo: string }) => updateSueldo(id, sueldo),
    onSuccess: () => invalidateEmpleadoQueries(queryClient),
  });
}

export function useDeleteEmpleado() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteEmpleado(id),
    onSuccess: () => invalidateEmpleadoQueries(queryClient),
  });
}
