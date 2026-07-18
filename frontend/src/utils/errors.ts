import { ApiRequestError } from "@/api/client";

export function friendlyApiError(error: unknown, fallback: string): string {
  if (error instanceof ApiRequestError) {
    if (error.status === 401) {
      if (error.message === "Invalid credentials") {
        return "Usuario o contraseña incorrectos.";
      }
      return "Tu sesión expiró. Volvé a iniciar sesión.";
    }
    if (error.status === 403) {
      return "No tenés permiso para realizar esta acción.";
    }
    if (error.status === 409) {
      return "No se puede modificar un registro cerrado.";
    }
    if (error.status === 413) {
      return "Los datos enviados son demasiado grandes.";
    }
    if (error.status === 422) {
      return "Revisá los valores ingresados e intentá de nuevo.";
    }
    if (error.status === 429) {
      return "Demasiados intentos. Esperá un momento e intentá de nuevo.";
    }
    if (error.status >= 500) {
      return "El servidor no está disponible en este momento. Intentá más tarde.";
    }
    return error.message;
  }
  return fallback;
}
