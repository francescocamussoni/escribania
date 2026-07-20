import { useCallback, useState } from "react";
import { ApiRequestError } from "@/api/client";
import { getCotizacion } from "@/api/cotizacion";
import type { CasaCotizacion, CotizacionResponse } from "@/types/api";
import { friendlyApiError } from "@/utils/errors";

export type CotizacionStatus = "idle" | "loading" | "success" | "error";

function cotizacionErrorMessage(error: unknown): string {
  if (error instanceof ApiRequestError) {
    if (error.status === 404) {
      return "No hay cotización disponible para esa fecha.";
    }
    if (error.status === 503) {
      return error.message;
    }
  }
  return friendlyApiError(
    error,
    "No se pudo consultar la cotización. Podés ingresar los valores manualmente.",
  );
}

export function useCotizacion() {
  const [status, setStatus] = useState<CotizacionStatus>("idle");
  const [data, setData] = useState<CotizacionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchRate = useCallback(async (casa: CasaCotizacion, fecha: string) => {
    setStatus("loading");
    setError(null);
    try {
      const result = await getCotizacion(casa, fecha);
      setData(result);
      setStatus("success");
      return result;
    } catch (err) {
      setData(null);
      setStatus("error");
      setError(cotizacionErrorMessage(err));
      throw err;
    }
  }, []);

  const reset = useCallback(() => {
    setStatus("idle");
    setData(null);
    setError(null);
  }, []);

  return { status, data, error, fetchRate, reset };
}
