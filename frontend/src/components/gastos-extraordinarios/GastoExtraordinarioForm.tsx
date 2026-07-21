import { FormEvent, useEffect, useState } from "react";
import type { GastoExtraordinarioInput, GastoExtraordinarioResponse } from "@/types/api";
import { friendlyApiError } from "@/utils/errors";

interface GastoExtraordinarioFormProps {
  initial?: GastoExtraordinarioResponse | null;
  onSubmit: (payload: GastoExtraordinarioInput) => Promise<void>;
  onCancel?: () => void;
}

function todayIsoDate(): string {
  return new Date().toISOString().slice(0, 10);
}

export function GastoExtraordinarioForm({
  initial = null,
  onSubmit,
  onCancel,
}: GastoExtraordinarioFormProps) {
  const isEdit = initial !== null;
  const [concepto, setConcepto] = useState(initial?.concepto ?? "");
  const [monto, setMonto] = useState(initial?.monto ?? "");
  const [fecha, setFecha] = useState(initial?.fecha ?? todayIsoDate());
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setConcepto(initial?.concepto ?? "");
    setMonto(initial?.monto ?? "");
    setFecha(initial?.fecha ?? todayIsoDate());
    setError(null);
  }, [initial]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await onSubmit({
        concepto: concepto.trim(),
        monto,
        fecha,
      });
      if (!isEdit) {
        setConcepto("");
        setMonto("");
        setFecha(todayIsoDate());
      }
    } catch (err) {
      setError(
        friendlyApiError(
          err,
          isEdit
            ? "No se pudo actualizar el gasto extraordinario."
            : "No se pudo registrar el gasto extraordinario.",
        ),
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <form className="gasto-form" onSubmit={handleSubmit}>
      <h3 className="gasto-form__title">
        {isEdit ? "Editar gasto extraordinario" : "Registrar gasto extraordinario"}
      </h3>
      <div className="gasto-form__grid">
        <label className="field">
          <span>Concepto</span>
          <input
            type="text"
            value={concepto}
            onChange={(e) => setConcepto(e.target.value)}
            placeholder="Celulares, papeles…"
            required
            maxLength={500}
          />
        </label>
        <label className="field">
          <span>Monto</span>
          <input
            type="number"
            step="0.01"
            min="0.01"
            value={monto}
            onChange={(e) => setMonto(e.target.value)}
            required
          />
        </label>
        <label className="field">
          <span>Fecha</span>
          <input type="date" value={fecha} onChange={(e) => setFecha(e.target.value)} required />
        </label>
      </div>
      {error ? <p className="form-error">{error}</p> : null}
      <div className="gasto-form__actions">
        <button type="submit" className="button button--primary" disabled={loading}>
          {loading ? "Guardando…" : isEdit ? "Guardar cambios" : "Registrar gasto"}
        </button>
        {isEdit && onCancel ? (
          <button type="button" className="button" onClick={onCancel} disabled={loading}>
            Cancelar
          </button>
        ) : null}
      </div>
    </form>
  );
}
