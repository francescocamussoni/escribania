import type { PagoColegioResponse } from "@/types/api";
import { formatDateOnly, formatMoney } from "@/utils/format";
import { labelTipoPagoEscribania } from "@/utils/tipoPagoEscribania";

interface PagoColegioListProps {
  pagos: PagoColegioResponse[];
}

export function PagoColegioList({ pagos }: PagoColegioListProps) {
  if (pagos.length === 0) {
    return <p className="page-muted">Sin pagos de la escribanía registrados.</p>;
  }

  return (
    <div className="gastos-list">
      <div className="gastos-list__header pagos-list__row--4col">
        <span>Tipo</span>
        <span>Detalle</span>
        <span>Fecha</span>
        <span className="gastos-list__amount">Monto</span>
      </div>
      {pagos.map((pago) => (
        <div key={pago.id} className="gastos-list__row pagos-list__row--4col">
          <span>{labelTipoPagoEscribania(pago.tipo)}</span>
          <span>{pago.concepto || "—"}</span>
          <span>{formatDateOnly(pago.fecha)}</span>
          <span className="gastos-list__amount">{formatMoney(pago.monto)}</span>
        </div>
      ))}
    </div>
  );
}
