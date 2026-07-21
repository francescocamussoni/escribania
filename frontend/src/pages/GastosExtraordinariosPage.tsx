import { useState } from "react";
import { GastoExtraordinarioForm } from "@/components/gastos-extraordinarios/GastoExtraordinarioForm";
import { GastoExtraordinarioList } from "@/components/gastos-extraordinarios/GastoExtraordinarioList";
import {
  useCreateGastoExtraordinario,
  useDeleteGastoExtraordinario,
  useGastosExtraordinarios,
  useUpdateGastoExtraordinario,
} from "@/hooks/useGastosExtraordinarios";
import type { GastoExtraordinarioResponse } from "@/types/api";
import { formatMonthYear, formatMoney, getDefaultPeriod, MONTH_NAMES } from "@/utils/format";

const YEAR_RANGE = 3;

function buildYearOptions(): number[] {
  const current = new Date().getFullYear();
  return Array.from({ length: YEAR_RANGE * 2 + 1 }, (_, index) => current - YEAR_RANGE + index);
}

export function GastosExtraordinariosPage() {
  const defaults = getDefaultPeriod();
  const [anio, setAnio] = useState(defaults.anio);
  const [mes, setMes] = useState(defaults.mes);
  const [editing, setEditing] = useState<GastoExtraordinarioResponse | null>(null);

  const period = { anio, mes };
  const { data, isLoading, error } = useGastosExtraordinarios(period);
  const createMutation = useCreateGastoExtraordinario(period);
  const updateMutation = useUpdateGastoExtraordinario(period);
  const deleteMutation = useDeleteGastoExtraordinario(period);

  const handleSubmit = async (payload: { concepto: string; monto: string; fecha: string }) => {
    if (editing) {
      await updateMutation.mutateAsync({ gastoId: editing.id, payload });
      setEditing(null);
      return;
    }
    await createMutation.mutateAsync(payload);
  };

  return (
    <div className="gastos-extraordinarios-page">
      <header className="page-header page-header--stacked">
        <div>
          <h1>Gastos extraordinarios</h1>
          <p className="page-muted">
            Gastos de la escribanía no vinculados a escrituras. Se reflejan en el Libro de Salida y
            se deducen del pago de escribanos.
          </p>
        </div>
        <div className="period-selector">
          <label className="field">
            <span>Mes</span>
            <select value={mes} onChange={(e) => setMes(Number(e.target.value))}>
              {MONTH_NAMES.map((name, index) => (
                <option key={name} value={index + 1}>
                  {name}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>Año</span>
            <select value={anio} onChange={(e) => setAnio(Number(e.target.value))}>
              {buildYearOptions().map((year) => (
                <option key={year} value={year}>
                  {year}
                </option>
              ))}
            </select>
          </label>
        </div>
      </header>

      <p className="period-label">{formatMonthYear(anio, mes)}</p>

      {error ? <p className="form-error">No se pudieron cargar los gastos extraordinarios.</p> : null}
      {isLoading ? <p className="page-muted">Cargando gastos…</p> : null}

      {data ? (
        <p className="gastos-extraordinarios-page__total">
          Total del mes: <strong>{formatMoney(data.total)}</strong>
        </p>
      ) : null}

      <section className="detail-card">
        <GastoExtraordinarioForm
          initial={editing}
          onSubmit={handleSubmit}
          onCancel={editing ? () => setEditing(null) : undefined}
        />
      </section>

      <section className="detail-card">
        <h2>Gastos registrados</h2>
        {data ? (
          <GastoExtraordinarioList
            gastos={data.gastos}
            onEdit={setEditing}
            onDelete={(gastoId) => deleteMutation.mutateAsync(gastoId)}
          />
        ) : null}
      </section>
    </div>
  );
}
