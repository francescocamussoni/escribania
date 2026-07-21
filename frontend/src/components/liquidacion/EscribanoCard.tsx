import { useState } from "react";
import { Link } from "react-router-dom";
import type { LiquidacionEscribano } from "@/types/api";
import { formatMoney, formatSignedMoney, labelEstado, signedMoneyClass } from "@/utils/format";

interface EscribanoCardProps {
  grupo: LiquidacionEscribano;
}

export function EscribanoCard({ grupo }: EscribanoCardProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <article className="escribano-card">
      <button
        type="button"
        className="escribano-card__header"
        onClick={() => setExpanded((prev) => !prev)}
        aria-expanded={expanded}
      >
        <div>
          <h3>{grupo.escribano_nombre}</h3>
          <p className="page-muted">
            {grupo.escrituras.length} escritura{grupo.escrituras.length === 1 ? "" : "s"} con actividad
          </p>
        </div>
        <div className="escribano-card__total">{formatMoney(grupo.total)}</div>
        <span className="escribano-card__chevron" aria-hidden="true">
          {expanded ? "▾" : "▸"}
        </span>
      </button>

      {expanded ? (
        <div className="escribano-card__body">
          {grupo.escrituras.length === 0 ? (
            <p className="page-muted">Sin cobros registrados en este período.</p>
          ) : (
            <div className="escribano-card__table">
              <div className="escribano-card__row escritano-card__row--header">
                <span>Escritura</span>
                <span>Estado</span>
                <span>Monto cobrado</span>
                <span>Neto impuestos</span>
              </div>
              {grupo.escrituras.map((item) => (
                <div key={item.escritura_id} className="escribano-card__row">
                  <Link to={`/escrituras/${item.escritura_id}`} className="text-link">
                    {item.nombre}
                  </Link>
                  <span>
                    <span className={`badge badge--${item.estado}`}>{labelEstado(item.estado)}</span>
                  </span>
                  <span className="escribano-card__subtotal">{formatMoney(item.monto_cobrado)}</span>
                  <span
                    className={`escribano-card__subtotal neto-impuestos${
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
