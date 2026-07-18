import { useState } from "react";
import { PagoEscribanoCard } from "@/components/salarios/PagoEscribanoCard";
import { PagoSecretariaCard } from "@/components/salarios/PagoSecretariaCard";
import { useSalarios } from "@/hooks/useSalarios";
import { formatMonthYear, getDefaultPeriod, MONTH_NAMES } from "@/utils/format";

const YEAR_RANGE = 3;

function buildYearOptions(): number[] {
  const current = new Date().getFullYear();
  return Array.from({ length: YEAR_RANGE * 2 + 1 }, (_, index) => current - YEAR_RANGE + index);
}

export function SalariosPage() {
  const defaults = getDefaultPeriod();
  const [anio, setAnio] = useState(defaults.anio);
  const [mes, setMes] = useState(defaults.mes);

  const { data, isLoading, error } = useSalarios({ anio, mes });

  return (
    <div className="salarios-page">
      <header className="page-header page-header--stacked">
        <div>
          <h1>Pago de salarios</h1>
          <p className="page-muted">Desglose de pagos a escribanos y secretarias por mes.</p>
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

      {error ? <p className="form-error">No se pudieron cargar los salarios.</p> : null}
      {isLoading ? <p className="page-muted">Cargando salarios…</p> : null}

      {data ? (
        <>
          <section className="detail-card">
            <h2>Escribanos</h2>
            <div className="card-stack">
              {data.escribanos.map((pago) => (
                <PagoEscribanoCard key={pago.nombre} pago={pago} />
              ))}
            </div>
            {data.escribanos.length === 0 ? (
              <p className="page-muted">Sin pagos de escribanos en este período.</p>
            ) : null}
          </section>

          <section className="detail-card">
            <h2>Secretarias</h2>
            <div className="secretaria-grid">
              {data.secretarias.map((pago) => (
                <PagoSecretariaCard key={pago.nombre} pago={pago} />
              ))}
            </div>
            {data.secretarias.length === 0 ? (
              <p className="page-muted">Sin pagos de secretarias en este período.</p>
            ) : null}
          </section>
        </>
      ) : null}
    </div>
  );
}
