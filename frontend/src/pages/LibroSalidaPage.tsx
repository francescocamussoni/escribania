import { useState } from "react";
import { LibroSalidaTable } from "@/components/libros/LibroSalidaTable";
import { useLibroSalida } from "@/hooks/useLibros";
import { formatMonthYear, getDefaultPeriod, MONTH_NAMES } from "@/utils/format";

const YEAR_RANGE = 3;

function buildYearOptions(): number[] {
  const current = new Date().getFullYear();
  return Array.from({ length: YEAR_RANGE * 2 + 1 }, (_, index) => current - YEAR_RANGE + index);
}

export function LibroSalidaPage() {
  const defaults = getDefaultPeriod();
  const [anio, setAnio] = useState(defaults.anio);
  const [mes, setMes] = useState(defaults.mes);

  const { data, isLoading, isError } = useLibroSalida({ anio, mes });

  return (
    <div className="libro-page">
      <header className="page-header page-header--stacked">
        <div>
          <h1>Libro de Salida</h1>
          <p className="page-muted">
            Flujos de salida del mes: impuestos, sellos, aportes notariales y gastos administrativos.
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

      <LibroSalidaTable data={data} isLoading={isLoading} error={isError} />
    </div>
  );
}
