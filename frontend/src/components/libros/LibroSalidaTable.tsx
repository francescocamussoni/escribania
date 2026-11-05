import { Link } from "react-router-dom";
import type { LibroLineaResponse, LibroSalidaResponse } from "@/types/api";
import { formatDateOnly, formatMoney } from "@/utils/format";
import { labelTipoPagoLibroSalida } from "@/utils/tipoPagoEscribania";

interface LibroSalidaTableProps {
  data: LibroSalidaResponse | undefined;
  isLoading: boolean;
  error: boolean;
}

function lineaKey(linea: LibroLineaResponse, index: number): string {
  return `${linea.escritura_id ?? "sin-escritura"}-${linea.tipo_pago ?? "pago"}-${linea.concepto}-${index}`;
}

function LibroSalidaLineaRow({ linea }: { linea: LibroLineaResponse }) {
  const tipoLabel = linea.tipo_pago ? labelTipoPagoLibroSalida(linea.tipo_pago) : "—";

  return (
    <div className="libro-table__grid libro-table__grid--row libro-table__grid--salida">
      <span>{tipoLabel}</span>
      <span>{linea.concepto || "—"}</span>
      <span className="libro-table__amount">{formatMoney(linea.monto)}</span>
      {linea.escritura_id && linea.escritura_nombre ? (
        <Link to={`/escrituras/${linea.escritura_id}`} className="text-link">
          {linea.escritura_nombre}
        </Link>
      ) : (
        <span className="page-muted">—</span>
      )}
      <span>{formatDateOnly(linea.fecha_pago)}</span>
    </div>
  );
}

export function LibroSalidaTable({ data, isLoading, error }: LibroSalidaTableProps) {
  if (error) {
    return <p className="form-error">No se pudo cargar el libro de salida.</p>;
  }

  if (isLoading) {
    return <p className="page-muted">Cargando libro de salida…</p>;
  }

  if (!data || data.lineas.length === 0) {
    return (
      <p className="page-muted">No hay pagos de la escribanía registrados en este período.</p>
    );
  }

  return (
    <section className="libro-table card" aria-label="Pagos de la escribanía en el período">
      <div className="libro-table__grid libro-table__grid--header libro-table__grid--salida">
        <span>Tipo pago</span>
        <span>Detalle</span>
        <span>Monto</span>
        <span>Escritura</span>
        <span>Fecha de pago</span>
      </div>
      {data.lineas.map((linea, index) => (
        <LibroSalidaLineaRow key={lineaKey(linea, index)} linea={linea} />
      ))}
      <div className="libro-table__footer">
        <span>Total del período</span>
        <span className="libro-table__total">{formatMoney(data.total)}</span>
      </div>
    </section>
  );
}
