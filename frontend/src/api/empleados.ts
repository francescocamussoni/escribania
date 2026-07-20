import { apiFetch } from "@/api/client";
import type { EmpleadoResponse } from "@/types/api";

export function listEmpleados(): Promise<EmpleadoResponse[]> {
  return apiFetch("/configuracion/empleados");
}

export function createEmpleado(nombre: string, sueldo: string): Promise<EmpleadoResponse> {
  return apiFetch("/configuracion/empleados", {
    method: "POST",
    body: JSON.stringify({ nombre, sueldo }),
  });
}

export function updateSueldo(id: string, sueldo: string): Promise<EmpleadoResponse> {
  return apiFetch(`/configuracion/empleados/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ sueldo }),
  });
}

export function deleteEmpleado(id: string): Promise<void> {
  return apiFetch(`/configuracion/empleados/${id}`, {
    method: "DELETE",
  });
}
