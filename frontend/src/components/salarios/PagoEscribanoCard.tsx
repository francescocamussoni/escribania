import { useState } from "react";
import { Link } from "react-router-dom";
import type { PagoEscribano } from "@/types/api";
import { formatMoney, formatSignedMoney, labelEstado, signedMoneyClass } from "@/utils/format";

interface PagoEscribanoCardProps {
  pago: PagoEscribano;
}

function hasDeduccion(deduccion: string): boolean {
  return Number.parseFloat(deduccion) > 0;
}

export function PagoEscribanoCard({ pago }: PagoEscribanoCardProps) {
  const [expanded, setExpanded] = useState(false);
  const conDeduccion = hasDeduccion(pago.deduccion_gastos_extraordinarios);

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
            {pago.escrituras.length} escritura{pago.escrituras.length === 1 ? "" : "s"} con actividad
          </p>
          {conDeduccion ? (
            <p className="pago-card__deduccion page-muted">
              Bruto {formatMoney(pago.monto_total)} − deducción{" "}
              {formatMoney(pago.deduccion_gastos_extraordinarios)}
            </p>
          ) : null}
        </div>
        <div className="pago-card__total">
          <span className="pago-card__total-label">{conDeduccion ? "Neto" : "Total"}</span>
          {formatMoney(conDeduccion ? pago.monto_neto : pago.monto_total)}
        </div>
        <span className="pago-card__chevron" aria-hidden="true">
          {expanded ? "▾" : "▸"}
        </span>
      </button>

      {expanded ? (
        <div className="pago-card__body">
          {conDeduccion ? (
            <div className="pago-card__summary">
              <div className="pago-card__summary-row">
                <span>Monto bruto</span>
                <span>{formatMoney(pago.monto_total)}</span>
              </div>
              <div className="pago-card__summary-row">
                <span>Deducción gastos extraordinarios</span>
                <span>−{formatMoney(pago.deduccion_gastos_extraordinarios)}</span>
              </div>
              <div className="pago-card__summary-row pago-card__summary-row--total">
                <span>Monto neto</span>
                <strong>{formatMoney(pago.monto_neto)}</strong>
              </div>
            </div>
          ) : null}
          {pago.escrituras.length === 0 ? (
            <p className="page-muted">Sin cobros registrados en este período.</p>
          ) : (
            <div className="pago-card__table">
              <div className="pago-card__row pago-card__row--header">
                <span>Escritura</span>
                <span>Estado</span>
                <span>Monto cobrado</span>
                <span>Neto impuestos</span>
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
                  <span
                    className={`pago-card__subtotal neto-impuestos${
                      signedMoneyClass(
                        item.neto_impuestos,
                        " neto-impuestos--positive",
                        " neto-impuestos--negative",
                      ) ?? ""
                    }`}
                  >
                    {formatSignedMoney(item.neto_impuestos)}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : null}
    </article>
  );
}
