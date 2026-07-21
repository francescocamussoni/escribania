import { Link } from "react-router-dom";
import type { LibroLineaResponse } from "@/types/api";
import { formatDateOnly, formatMoney } from "@/utils/format";
import { labelTipoImpuesto } from "@/utils/impuesto";

interface LibroLineaRowProps {
  linea: LibroLineaResponse;
}

function lineaKey(linea: LibroLineaResponse, index: number): string {
  if (linea.gasto_extraordinario_id) {
    return `extra-${linea.gasto_extraordinario_id}`;
  }
  return `${linea.escritura_id ?? "sin-escritura"}-${linea.concepto}-${index}`;
}

export function LibroLineaRow({ linea }: LibroLineaRowProps) {
  const isImpuesto = linea.origen === "impuesto";
  const isExtraordinario = linea.origen === "extraordinario";

  return (
    <div className="libro-table__grid libro-table__grid--row">
      <span className="libro-table__concepto">
        {linea.concepto || "—"}
        {isImpuesto ? <span className="badge badge--muted libro-table__origen">Impuesto</span> : null}
        {isExtraordinario ? (
          <span className="badge badge--extraordinario libro-table__origen">Extraordinario</span>
        ) : null}
      </span>
      <span>{isImpuesto && linea.tipo_impuesto ? labelTipoImpuesto(linea.tipo_impuesto) : "—"}</span>
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

export { lineaKey };
