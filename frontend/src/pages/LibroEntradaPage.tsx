import { useState } from "react";
import { LibroEntradaTable } from "@/components/libros/LibroEntradaTable";
import { useLibroEntrada } from "@/hooks/useLibros";
import { formatMonthYear, getDefaultPeriod, MONTH_NAMES } from "@/utils/format";

const YEAR_RANGE = 3;

function buildYearOptions(): number[] {
  const current = new Date().getFullYear();
  return Array.from({ length: YEAR_RANGE * 2 + 1 }, (_, index) => current - YEAR_RANGE + index);
}

export function LibroEntradaPage() {
  const defaults = getDefaultPeriod();
  const [anio, setAnio] = useState(defaults.anio);
  const [mes, setMes] = useState(defaults.mes);

  const { data, isLoading, isError } = useLibroEntrada({ anio, mes });

  return (
    <div className="libro-page">
      <header className="page-header page-header--stacked">
        <div>
          <h1>Libro de Entrada</h1>
          <p className="page-muted">
            Flujos de entrada del mes: honorarios, certificación y gastos adicionales tipo entrada.
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

      <LibroEntradaTable data={data} isLoading={isLoading} error={isError} />
    </div>
  );
}
