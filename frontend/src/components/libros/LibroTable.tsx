import { Link } from "react-router-dom";
import type { LibroResponse } from "@/types/api";
import { formatDateOnly, formatMoney } from "@/utils/format";

export interface LibroTableProps {
  data: LibroResponse | undefined;
  isLoading: boolean;
  error: boolean;
  emptyMessage: string;
}

export function LibroTable({ data, isLoading, error, emptyMessage }: LibroTableProps) {
  if (error) {
    return <p className="form-error">No se pudo cargar el libro.</p>;
  }

  if (isLoading) {
    return <p className="page-muted">Cargando libro…</p>;
  }

  if (!data || data.lineas.length === 0) {
    return <p className="page-muted">{emptyMessage}</p>;
  }

  return (
    <section className="libro-table card" aria-label="Líneas del libro">
      <div className="libro-table__grid libro-table__grid--header">
        <span>Concepto</span>
        <span>Monto</span>
        <span>Escritura</span>
        <span>Fecha</span>
      </div>
      {data.lineas.map((linea, index) => (
        <div
          key={`${linea.escritura_id}-${linea.concepto}-${index}`}
          className="libro-table__grid libro-table__grid--row"
        >
          <span>{linea.concepto}</span>
          <span className="libro-table__amount">{formatMoney(linea.monto)}</span>
          <Link to={`/escrituras/${linea.escritura_id}`} className="text-link">
            {linea.escritura_nombre}
          </Link>
          <span>{formatDateOnly(linea.fecha_escritura)}</span>
        </div>
      ))}
      <div className="libro-table__footer">
        <span>Total del período</span>
        <span className="libro-table__total">{formatMoney(data.total)}</span>
      </div>
    </section>
  );
}
