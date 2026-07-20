import type { PagoColegioResponse } from "@/types/api";
import { formatDateOnly, formatMoney } from "@/utils/format";

interface PagoColegioListProps {
  pagos: PagoColegioResponse[];
}

export function PagoColegioList({ pagos }: PagoColegioListProps) {
  if (pagos.length === 0) {
    return <p className="page-muted">Sin pagos al Colegio registrados.</p>;
  }

  return (
    <div className="gastos-list">
      <div className="gastos-list__header pagos-list__row--3col">
        <span>Concepto</span>
        <span>Fecha</span>
        <span className="gastos-list__amount">Monto</span>
      </div>
      {pagos.map((pago) => (
        <div key={pago.id} className="gastos-list__row pagos-list__row--3col">
          <span>{pago.concepto || "—"}</span>
          <span>{formatDateOnly(pago.fecha)}</span>
          <span className="gastos-list__amount">{formatMoney(pago.monto)}</span>
        </div>
      ))}
    </div>
  );
}
