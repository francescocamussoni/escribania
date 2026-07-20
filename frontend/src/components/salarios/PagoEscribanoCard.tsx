import { useState } from "react";
import { Link } from "react-router-dom";
import type { PagoEscribano } from "@/types/api";
import { formatMoney, labelEstado } from "@/utils/format";

interface PagoEscribanoCardProps {
  pago: PagoEscribano;
}

export function PagoEscribanoCard({ pago }: PagoEscribanoCardProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <article className="pago-card">
      <button
        type="button"
        className="pago-card__header"
        onClick={() => setExpanded((prev) => !prev)}
        aria-expanded={expanded}
      >
        <div>
          <h3>{pago.nombre}</h3>
          <p className="page-muted">
            {pago.escrituras.length} escritura{pago.escrituras.length === 1 ? "" : "s"} con cobros
          </p>
        </div>
        <div className="pago-card__total">{formatMoney(pago.monto_total)}</div>
        <span className="pago-card__chevron" aria-hidden="true">
          {expanded ? "▾" : "▸"}
        </span>
      </button>

      {expanded ? (
        <div className="pago-card__body">
          {pago.escrituras.length === 0 ? (
            <p className="page-muted">Sin cobros registrados en este período.</p>
          ) : (
            <div className="pago-card__table">
              <div className="pago-card__row pago-card__row--header">
                <span>Escritura</span>
                <span>Estado</span>
                <span>Monto cobrado</span>
              </div>
              {pago.escrituras.map((item) => (
                <div key={item.escritura_id} className="pago-card__row">
                  <Link to={`/escrituras/${item.escritura_id}`} className="text-link">
                    {item.nombre}
                  </Link>
                  <span>
                    <span className={`badge badge--${item.estado}`}>{labelEstado(item.estado)}</span>
                  </span>
                  <span className="pago-card__subtotal">{formatMoney(item.monto_cobrado)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : null}
    </article>
  );
}
