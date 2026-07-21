import { LibroLineaRow, lineaKey } from "@/components/libros/LibroLineaRow";
import type { LibroSalidaResponse } from "@/types/api";
import { formatMoney } from "@/utils/format";

export interface LibroTableProps {
  data: LibroSalidaResponse | undefined;
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
        <span>Tipo impuesto</span>
        <span>Monto</span>
        <span>Escritura</span>
        <span>Fecha de pago</span>
      </div>
      {data.lineas.map((linea, index) => (
        <LibroLineaRow key={lineaKey(linea, index)} linea={linea} />
      ))}
      <div className="libro-table__footer">
        <span>Total del período</span>
        <span className="libro-table__total">{formatMoney(data.total)}</span>
      </div>
    </section>
  );
}
