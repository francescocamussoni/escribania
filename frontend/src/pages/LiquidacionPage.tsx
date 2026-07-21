import { useState } from "react";
import { EscribanoCard } from "@/components/liquidacion/EscribanoCard";
import { LiquidacionResumen } from "@/components/liquidacion/LiquidacionResumen";
import { useLiquidacion } from "@/hooks/useLiquidacion";
import { formatMonthYear, getDefaultPeriod, MONTH_NAMES } from "@/utils/format";

const YEAR_RANGE = 3;

function buildYearOptions(): number[] {
  const current = new Date().getFullYear();
  return Array.from({ length: YEAR_RANGE * 2 + 1 }, (_, index) => current - YEAR_RANGE + index);
}

export function LiquidacionPage() {
  const defaults = getDefaultPeriod();
  const [anio, setAnio] = useState(defaults.anio);
  const [mes, setMes] = useState(defaults.mes);

  const { data, isLoading, error } = useLiquidacion({ anio, mes });

  return (
    <div className="liquidacion-page">
      <header className="page-header page-header--stacked">
        <div>
          <h1>Liquidación</h1>
          <p className="page-muted">Cobros reales del mes por escribano, incluyendo neto de impuestos.</p>
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

      {error ? <p className="form-error">No se pudo cargar la liquidación.</p> : null}
      {isLoading ? <p className="page-muted">Cargando liquidación…</p> : null}

      {data ? (
        <>
          <LiquidacionResumen data={data} />
          <div className="card-stack">
            {data.por_escribano.map((grupo) => (
              <EscribanoCard key={grupo.escribano_id} grupo={grupo} />
            ))}
          </div>
        </>
      ) : null}

      {!isLoading && !error && data?.por_escribano.every((g) => g.escrituras.length === 0) ? (
        <p className="page-muted">No hay cobros de clientes registrados para este período.</p>
      ) : null}
    </div>
  );
}
