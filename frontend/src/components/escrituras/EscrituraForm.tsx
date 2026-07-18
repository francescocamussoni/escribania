import { FormEvent, useState } from "react";
import type { EscrituraInput, EscrituraResponse, Escribano } from "@/types/api";
import { friendlyApiError } from "@/utils/errors";

const ESCRIBANOS: Escribano[] = ["costanza", "gabriel", "victoria"];

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
  const [nombre, setNombre] = useState(initial?.nombre ?? "");
  const [escribano, setEscribano] = useState<Escribano>(initial?.escribano ?? "costanza");
  const [usdValue, setUsdValue] = useState(initial?.usd_value ?? "");
  const [dolarMep, setDolarMep] = useState(initial?.dolar_mep ?? "");
  const [dolarNacion, setDolarNacion] = useState(initial?.dolar_nacion ?? "");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (readOnly) {
      return;
    }
    setError(null);
    setLoading(true);
    try {
      await onSubmit({
        nombre: nombre.trim(),
        escribano,
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

  return (
    <form className="escritura-form" onSubmit={handleSubmit}>
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
        <select
          value={escribano}
          onChange={(e) => setEscribano(e.target.value as Escribano)}
          disabled={readOnly}
        >
          {ESCRIBANOS.map((value) => (
            <option key={value} value={value}>
              {value.charAt(0).toUpperCase() + value.slice(1)}
            </option>
          ))}
        </select>
      </label>

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
          <button type="submit" className="button button--primary" disabled={loading}>
            {loading ? "Guardando…" : submitLabel}
          </button>
        </div>
      ) : null}
    </form>
  );
}
