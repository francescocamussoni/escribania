import type { PagoSecretaria } from "@/types/api";
import { formatMoney } from "@/utils/format";

interface PagoSecretariaCardProps {
  pago: PagoSecretaria;
}

export function PagoSecretariaCard({ pago }: PagoSecretariaCardProps) {
  return (
    <article className="secretaria-card">
      <div className="secretaria-card__header">
        <h3>{pago.nombre}</h3>
        <span className="secretaria-card__monto">{formatMoney(pago.monto)}</span>
      </div>
      <p className="page-muted">
        Pool total del mes: <strong>{formatMoney(pago.base_total)}</strong>
      </p>
    </article>
  );
}
