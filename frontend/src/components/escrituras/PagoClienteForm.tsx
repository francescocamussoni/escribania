import { FormEvent, useState } from "react";
import type { PagoClienteInput } from "@/types/api";
import { friendlyApiError } from "@/utils/errors";

interface PagoClienteFormProps {
  saldoPendiente: string;
  onSubmit: (payload: PagoClienteInput) => Promise<void>;
}

function todayIsoDate(): string {
  return new Date().toISOString().slice(0, 10);
}

export function PagoClienteForm({ saldoPendiente, onSubmit }: PagoClienteFormProps) {
  const [concepto, setConcepto] = useState("");
  const [monto, setMonto] = useState("");
  const [fecha, setFecha] = useState(todayIsoDate());
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);

    const montoNum = Number(monto);
    const saldoNum = Number(saldoPendiente);
    if (!Number.isNaN(montoNum) && !Number.isNaN(saldoNum) && montoNum > saldoNum) {
      setError(`El monto no puede superar el saldo pendiente (${saldoPendiente}).`);
      return;
    }

    setLoading(true);
    try {
      await onSubmit({
        concepto: concepto.trim(),
        monto,
        fecha,
      });
      setConcepto("");
      setMonto("");
      setFecha(todayIsoDate());
    } catch (err) {
      setError(friendlyApiError(err, "No se pudo registrar el pago del cliente."));
    } finally {
      setLoading(false);
    }
  };

  return (
    <form className="gasto-form" onSubmit={handleSubmit}>
      <h3 className="gasto-form__title">Registrar pago del cliente</h3>
      <div className="gasto-form__grid">
        <label className="field">
          <span>Concepto</span>
          <input
            type="text"
            value={concepto}
            onChange={(e) => setConcepto(e.target.value)}
            placeholder="Anticipo, saldo final…"
          />
        </label>
        <label className="field">
          <span>Monto</span>
          <input
            type="number"
            step="0.01"
            min="0"
            max={saldoPendiente}
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
      <button type="submit" className="button button--primary" disabled={loading}>
        {loading ? "Guardando…" : "Registrar pago"}
      </button>
    </form>
  );
}
