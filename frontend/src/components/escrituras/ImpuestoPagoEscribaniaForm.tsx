import { FormEvent, useState } from "react";
import type { PagoImpuestoInput } from "@/types/api";
import { friendlyApiError } from "@/utils/errors";

interface ImpuestoPagoEscribaniaFormProps {
  initialMonto?: string;
  initialFecha?: string;
  isUpdate: boolean;
  onSubmit: (payload: PagoImpuestoInput) => Promise<void>;
  onDelete?: () => Promise<void>;
}

function todayIsoDate(): string {
  return new Date().toISOString().slice(0, 10);
}

export function ImpuestoPagoEscribaniaForm({
  initialMonto = "",
  initialFecha,
  isUpdate,
  onSubmit,
  onDelete,
}: ImpuestoPagoEscribaniaFormProps) {
  const [monto, setMonto] = useState(initialMonto);
  const [fecha, setFecha] = useState(initialFecha ?? todayIsoDate());
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await onSubmit({ monto, fecha });
    } catch (err) {
      setError(friendlyApiError(err, "No se pudo registrar el pago de la escribanía."));
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!onDelete) {
      return;
    }
    const confirmed = window.confirm("¿Eliminar el pago de la escribanía por este impuesto?");
    if (!confirmed) {
      return;
    }
    setError(null);
    setLoading(true);
    try {
      await onDelete();
    } catch (err) {
      setError(friendlyApiError(err, "No se pudo eliminar el pago."));
    } finally {
      setLoading(false);
    }
  };

  return (
    <form className="gasto-form impuesto-pago-form" onSubmit={handleSubmit}>
      <h4 className="gasto-form__title">Pago de la escribanía</h4>
      <div className="gasto-form__grid impuesto-pago-form__grid">
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
      <div className="impuesto-pago-form__actions">
        <button type="submit" className="button button--primary button--small" disabled={loading}>
          {loading ? "Guardando…" : isUpdate ? "Actualizar pago" : "Registrar pago"}
        </button>
        {isUpdate && onDelete ? (
          <button
            type="button"
            className="button button--danger button--small"
            onClick={handleDelete}
            disabled={loading}
          >
            Eliminar
          </button>
        ) : null}
      </div>
    </form>
  );
}
