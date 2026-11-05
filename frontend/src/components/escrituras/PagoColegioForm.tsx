import { FormEvent, useState } from "react";
import type { PagoColegioInput, TipoPagoEscribania } from "@/types/api";
import { TIPO_PAGO_ESCRIBANIA_OPTIONS } from "@/utils/tipoPagoEscribania";
import { friendlyApiError } from "@/utils/errors";

interface PagoColegioFormProps {
  onSubmit: (payload: PagoColegioInput) => Promise<void>;
}

function todayIsoDate(): string {
  return new Date().toISOString().slice(0, 10);
}

export function PagoColegioForm({ onSubmit }: PagoColegioFormProps) {
  const [tipo, setTipo] = useState<TipoPagoEscribania>("colegio");
  const [concepto, setConcepto] = useState("");
  const [monto, setMonto] = useState("");
  const [fecha, setFecha] = useState(todayIsoDate());
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const requiereDetalle = tipo === "otros";

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);

    const detalle = concepto.trim();
    if (requiereDetalle && !detalle) {
      setError("El detalle es obligatorio para pagos tipo Otros.");
      return;
    }

    setLoading(true);
    try {
      await onSubmit({
        monto,
        fecha,
        tipo,
        concepto: detalle,
      });
      setTipo("colegio");
      setConcepto("");
      setMonto("");
      setFecha(todayIsoDate());
    } catch (err) {
      setError(friendlyApiError(err, "No se pudo registrar el pago de la escribanía."));
    } finally {
      setLoading(false);
    }
  };

  return (
    <form className="gasto-form" onSubmit={handleSubmit}>
      <h3 className="gasto-form__title">Registrar pago de la escribanía</h3>
      <div className="gasto-form__grid">
        <label className="field">
          <span>Tipo de pago</span>
          <select
            value={tipo}
            onChange={(e) => setTipo(e.target.value as TipoPagoEscribania)}
            required
          >
            {TIPO_PAGO_ESCRIBANIA_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>Monto</span>
          <input
            type="number"
            step="0.01"
            min="0"
            value={monto}
            onChange={(e) => setMonto(e.target.value)}
            required
          />
        </label>
        <label className="field">
          <span>Fecha</span>
          <input type="date" value={fecha} onChange={(e) => setFecha(e.target.value)} required />
        </label>
        {requiereDetalle ? (
          <label className="field field--full">
            <span>Detalle</span>
            <textarea
              value={concepto}
              onChange={(e) => setConcepto(e.target.value)}
              placeholder="Describa el concepto del pago…"
              rows={2}
              required
            />
          </label>
        ) : null}
      </div>
      {error ? <p className="form-error">{error}</p> : null}
      <button type="submit" className="button button--primary" disabled={loading}>
        {loading ? "Guardando…" : "Registrar pago"}
      </button>
    </form>
  );
}
