import { LibroLineaRow, lineaKey } from "@/components/libros/LibroLineaRow";
import { Link } from "react-router-dom";
import type { LibroEntradaResponse } from "@/types/api";
import { formatMoney } from "@/utils/format";

interface LibroEntradaTableProps {
  data: LibroEntradaResponse | undefined;
  isLoading: boolean;
  error: boolean;
}

function hasSaldoPendiente(saldo: string): boolean {
  const value = Number(saldo);
  return !Number.isNaN(value) && value > 0;
}

export function LibroEntradaTable({ data, isLoading, error }: LibroEntradaTableProps) {
  if (error) {
    return <p className="form-error">No se pudo cargar el libro de entrada.</p>;
  }

  if (isLoading) {
    return <p className="page-muted">Cargando libro de entrada…</p>;
  }

  if (!data) {
    return <p className="page-muted">No hay datos para este período.</p>;
  }

  const { lineas, resumen_deudas: deudas } = data;

  return (
    <div className="libro-entrada">
      <section className="libro-table card" aria-label="Pagos del cliente en el período">
        <h2 className="libro-section__title">Pagos del cliente en el período</h2>
        {lineas.length === 0 ? (
          <p className="page-muted libro-section__empty">
            No hay pagos del cliente registrados en este período.
          </p>
        ) : (
          <>
            <div className="libro-table__grid libro-table__grid--header">
              <span>Concepto</span>
              <span>Tipo impuesto</span>
              <span>Monto</span>
              <span>Escritura</span>
              <span>Fecha de pago</span>
            </div>
            {lineas.map((linea, index) => (
              <LibroLineaRow key={lineaKey(linea, index)} linea={linea} />
            ))}
            <div className="libro-table__footer">
              <span>Total cobrado en el período</span>
              <span className="libro-table__total">{formatMoney(data.total)}</span>
            </div>
          </>
        )}
      </section>

      <section className="libro-table card" aria-label="Resumen de deudas pendientes">
        <h2 className="libro-section__title">Deudas pendientes (escrituras abiertas)</h2>
        {deudas.length === 0 ? (
          <p className="page-muted libro-section__empty">No hay deudas pendientes de cobro.</p>
        ) : (
          <>
            <div className="libro-table__grid libro-table__grid--header libro-table__grid--deudas">
              <span>Escritura</span>
              <span>Costo total</span>
              <span>Total pagado</span>
              <span>Saldo pendiente</span>
            </div>
            {deudas.map((deuda) => (
              <div
                key={deuda.escritura_id}
                className="libro-table__grid libro-table__grid--row libro-table__grid--deudas"
              >
                <Link to={`/escrituras/${deuda.escritura_id}`} className="text-link">
                  {deuda.escritura_nombre}
                </Link>
                <span className="libro-table__amount">{formatMoney(deuda.costo_total)}</span>
                <span className="libro-table__amount">{formatMoney(deuda.total_pagado)}</span>
                <span
                  className={`libro-table__amount${
                    hasSaldoPendiente(deuda.saldo_pendiente) ? " saldo-resumen__pendiente" : ""
                  }`}
                >
                  {formatMoney(deuda.saldo_pendiente)}
                </span>
              </div>
            ))}
          </>
        )}
      </section>
    </div>
  );
}
