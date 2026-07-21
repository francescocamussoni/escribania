import { FormEvent, useEffect, useMemo, useState } from "react";
import type { DireccionProrrateo, ImpuestoInput, ImpuestoResponse, TipoImpuesto } from "@/types/api";
import {
  TIPOS_IMPUESTO,
  calcMontoSugeridoPreview,
  labelDireccionProrrateo,
  labelTipoImpuesto,
} from "@/utils/impuesto";
import { friendlyApiError } from "@/utils/errors";
import { formatMoney } from "@/utils/format";

interface ImpuestoFormProps {
  onSubmit: (payload: ImpuestoInput) => Promise<void>;
  initial?: ImpuestoResponse;
  onCancel?: () => void;
}

const DEFAULT_FORM: ImpuestoInput = {
  tipo: "API",
  monto_total: "",
  periodo_inicio: "",
  periodo_fin: "",
  fecha_corte: "",
  direccion_prorrateo: "hacia_atras",
};

function toFormValues(impuesto: ImpuestoResponse): ImpuestoInput {
  return {
    tipo: impuesto.tipo,
    monto_total: impuesto.monto_total,
    periodo_inicio: impuesto.periodo_inicio,
    periodo_fin: impuesto.periodo_fin,
    fecha_corte: impuesto.fecha_corte,
    direccion_prorrateo: impuesto.direccion_prorrateo,
  };
}

export function ImpuestoForm({ onSubmit, initial, onCancel }: ImpuestoFormProps) {
  const isEdit = initial !== undefined;
  const [form, setForm] = useState<ImpuestoInput>(initial ? toFormValues(initial) : DEFAULT_FORM);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setForm(initial ? toFormValues(initial) : DEFAULT_FORM);
    setError(null);
  }, [initial]);

  const montoSugerido = useMemo(
    () =>
      calcMontoSugeridoPreview(
        form.monto_total,
        form.periodo_inicio,
        form.periodo_fin,
        form.fecha_corte,
        form.direccion_prorrateo,
      ),
    [form],
  );

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await onSubmit(form);
      if (!isEdit) {
        setForm(DEFAULT_FORM);
      } else {
        onCancel?.();
      }
    } catch (err) {
      setError(friendlyApiError(err, isEdit ? "No se pudo actualizar el impuesto." : "No se pudo registrar el impuesto."));
    } finally {
      setLoading(false);
    }
  };

  return (
    <form className="gasto-form impuesto-form" onSubmit={handleSubmit}>
      <h3 className="gasto-form__title">{isEdit ? "Editar impuesto" : "Registrar impuesto"}</h3>
      <div className="gasto-form__grid impuesto-form__grid">
        <label className="field">
          <span>Tipo</span>
          <select
            value={form.tipo}
            onChange={(e) => setForm((prev) => ({ ...prev, tipo: e.target.value as TipoImpuesto }))}
            required
          >
            {TIPOS_IMPUESTO.map((tipo) => (
              <option key={tipo} value={tipo}>
                {labelTipoImpuesto(tipo)}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>Monto total del período</span>
          <input
            type="number"
            step="0.01"
            min="0.01"
            value={form.monto_total}
            onChange={(e) => setForm((prev) => ({ ...prev, monto_total: e.target.value }))}
            required
          />
        </label>
        <label className="field">
          <span>Período desde</span>
          <input
            type="date"
            value={form.periodo_inicio}
            onChange={(e) => setForm((prev) => ({ ...prev, periodo_inicio: e.target.value }))}
            required
          />
        </label>
        <label className="field">
          <span>Período hasta</span>
          <input
            type="date"
            value={form.periodo_fin}
            onChange={(e) => setForm((prev) => ({ ...prev, periodo_fin: e.target.value }))}
            required
          />
        </label>
        <label className="field">
          <span>Fecha de corte</span>
          <input
            type="date"
            value={form.fecha_corte}
            onChange={(e) => setForm((prev) => ({ ...prev, fecha_corte: e.target.value }))}
            required
          />
        </label>
        <label className="field">
          <span>Dirección del prorrateo</span>
          <select
            value={form.direccion_prorrateo}
            onChange={(e) =>
              setForm((prev) => ({
                ...prev,
                direccion_prorrateo: e.target.value as DireccionProrrateo,
              }))
            }
            required
          >
            <option value="hacia_atras">{labelDireccionProrrateo("hacia_atras")}</option>
            <option value="hacia_adelante">{labelDireccionProrrateo("hacia_adelante")}</option>
          </select>
        </label>
      </div>
      {montoSugerido !== null ? (
        <p className="impuesto-form__preview">
          Monto sugerido cliente: <strong>{formatMoney(montoSugerido)}</strong>
        </p>
      ) : null}
      {error ? <p className="form-error">{error}</p> : null}
      <div className="impuesto-form__actions">
        {isEdit && onCancel ? (
          <button type="button" className="button" onClick={onCancel} disabled={loading}>
            Cancelar
          </button>
        ) : null}
        <button type="submit" className="button button--primary" disabled={loading}>
          {loading ? "Guardando…" : isEdit ? "Guardar cambios" : "Registrar impuesto"}
        </button>
      </div>
    </form>
  );
}
