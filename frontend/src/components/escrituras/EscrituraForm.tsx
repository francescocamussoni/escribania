import { FormEvent, useEffect, useMemo, useState } from "react";
import type { EscrituraInput, EscrituraResponse } from "@/types/api";
import { useCotizacion } from "@/hooks/useCotizacion";
import { useEscribanos } from "@/hooks/useEscribanos";
import { displayEscribanoNombre } from "@/utils/format";
import { friendlyApiError } from "@/utils/errors";

function todayISODate(): string {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

interface EscrituraFormProps {
  initial?: EscrituraResponse;
  readOnly?: boolean;
  submitLabel?: string;
  onSubmit: (payload: EscrituraInput) => Promise<void>;
  onCancel?: () => void;
}

export function EscrituraForm({
  initial,
  readOnly = false,
  submitLabel = "Guardar",
  onSubmit,
  onCancel,
}: EscrituraFormProps) {
  const { data: escribanosActivos, isLoading: escribanosLoading } = useEscribanos(false);
  const { data: todosEscribanos } = useEscribanos(true);

  const [nombre, setNombre] = useState(initial?.nombre ?? "");
  const [escribanoId, setEscribanoId] = useState(initial?.escribano_id ?? "");
  const [usdValue, setUsdValue] = useState(initial?.usd_value ?? "");
  const [dolarMep, setDolarMep] = useState(initial?.dolar_mep ?? "");
  const [dolarNacion, setDolarNacion] = useState(initial?.dolar_nacion ?? "");
  const [cotizacionFecha, setCotizacionFecha] = useState(todayISODate);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const {
    status: cotizacionStatus,
    error: cotizacionError,
    fetchRate,
    reset: resetCotizacion,
  } = useCotizacion();

  const escribanoOptions = useMemo(() => {
    const active = escribanosActivos ?? [];
    const optionIds = new Set(active.map((item) => item.id));
    if (initial?.escribano_id && !optionIds.has(initial.escribano_id)) {
      const current = todosEscribanos?.find((item) => item.id === initial.escribano_id);
      if (current) {
        return [...active, current];
      }
    }
    return active;
  }, [escribanosActivos, initial?.escribano_id, todosEscribanos]);

  useEffect(() => {
    if (escribanoId || escribanoOptions.length === 0) {
      return;
    }
    setEscribanoId(escribanoOptions[0].id);
  }, [escribanoId, escribanoOptions]);

  const handleConsultarCotizacion = async () => {
    resetCotizacion();
    try {
      const mep = await fetchRate("bolsa", cotizacionFecha);
      const nacion = await fetchRate("oficial", cotizacionFecha);
      setDolarMep(mep.venta);
      setDolarNacion(nacion.venta);
    } catch {
      // Error message is exposed via cotizacionError.
    }
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (readOnly || !escribanoId) {
      return;
    }
    setError(null);
    setLoading(true);
    try {
      await onSubmit({
        nombre: nombre.trim(),
        escribano_id: escribanoId,
        usd_value: usdValue,
        dolar_mep: dolarMep,
        dolar_nacion: dolarNacion,
      });
    } catch (err) {
      setError(friendlyApiError(err, "No se pudo guardar la escritura."));
    } finally {
      setLoading(false);
    }
  };

  const selectedEscribano = escribanoOptions.find((item) => item.id === escribanoId);

  return (
    <form className="escritura-form" onSubmit={handleSubmit}>
      <div className="escritura-form__grid escritura-form__grid--two">
        <label className="field">
          <span>Nombre</span>
          <input
            type="text"
            value={nombre}
            onChange={(e) => setNombre(e.target.value)}
            required
            readOnly={readOnly}
          />
        </label>

        <label className="field">
          <span>Escribano</span>
          {readOnly ? (
            <input
              type="text"
              readOnly
              value={displayEscribanoNombre(
                initial?.escribano_id ?? escribanoId,
                initial?.escribano_nombre ?? selectedEscribano?.nombre ?? "",
                todosEscribanos,
              )}
            />
          ) : escribanosLoading ? (
            <input type="text" readOnly value="Cargando escribanos…" />
          ) : escribanoOptions.length === 0 ? (
            <p className="form-error">No hay escribanos activos. Agregá uno en Configuración.</p>
          ) : (
            <select
              value={escribanoId}
              onChange={(e) => setEscribanoId(e.target.value)}
              required
            >
              {escribanoOptions.map((item) => (
                <option key={item.id} value={item.id}>
                  {displayEscribanoNombre(item.id, item.nombre, todosEscribanos)}
                </option>
              ))}
            </select>
          )}
        </label>
      </div>

      {!readOnly ? (
        <div className="escritura-form__cotizacion">
          <label className="field">
            <span>Fecha de cotización</span>
            <input
              type="date"
              value={cotizacionFecha}
              onChange={(e) => {
                setCotizacionFecha(e.target.value);
                resetCotizacion();
              }}
            />
          </label>
          <button
            type="button"
            className="button button--secondary"
            onClick={() => void handleConsultarCotizacion()}
            disabled={cotizacionStatus === "loading"}
          >
            {cotizacionStatus === "loading" ? "Consultando…" : "Consultar cotización"}
          </button>
        </div>
      ) : null}

      {cotizacionError ? <p className="form-error">{cotizacionError}</p> : null}

      <div className="escritura-form__grid">
        <label className="field">
          <span>USD</span>
          <input
            type="number"
            step="0.01"
            min="0"
            value={usdValue}
            onChange={(e) => setUsdValue(e.target.value)}
            required
            readOnly={readOnly}
          />
        </label>
        <label className="field">
          <span>Dólar MEP</span>
          <input
            type="number"
            step="0.01"
            min="0"
            value={dolarMep}
            onChange={(e) => setDolarMep(e.target.value)}
            required
            readOnly={readOnly}
          />
        </label>
        <label className="field">
          <span>Dólar Nación</span>
          <input
            type="number"
            step="0.01"
            min="0"
            value={dolarNacion}
            onChange={(e) => setDolarNacion(e.target.value)}
            required
            readOnly={readOnly}
          />
        </label>
      </div>

      {error ? <p className="form-error">{error}</p> : null}

      {!readOnly ? (
        <div className="form-actions">
          {onCancel ? (
            <button type="button" className="button button--secondary" onClick={onCancel}>
              Cancelar
            </button>
          ) : null}
          <button
            type="submit"
            className="button button--primary"
            disabled={loading || !escribanoId || escribanoOptions.length === 0}
          >
            {loading ? "Guardando…" : submitLabel}
          </button>
        </div>
      ) : null}
    </form>
  );
}
