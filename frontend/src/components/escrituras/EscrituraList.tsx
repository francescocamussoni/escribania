import { Link } from "react-router-dom";
import type { EscrituraListItem } from "@/types/api";
import { useEscribanos } from "@/hooks/useEscribanos";
import type { SortDirection } from "@/utils/escrituraList";
import {
  displayEscribanoNombre,
  formatCobroPercent,
  formatDate,
  formatMoney,
  labelEstado,
} from "@/utils/format";

interface EscrituraListProps {
  items: EscrituraListItem[];
  loading?: boolean;
  emptyMessage?: string;
  sortDirection: SortDirection;
  onSortToggle: () => void;
}

function hasSaldoPendiente(saldo: string): boolean {
  const value = Number(saldo);
  return !Number.isNaN(value) && value > 0;
}

function sortIndicator(direction: SortDirection): string {
  return direction === "asc" ? "↑" : "↓";
}

function cobroPercentBadge(item: EscrituraListItem) {
  const percent = formatCobroPercent(item.total_pagado, item.costo_total);
  if (percent === null) {
    return null;
  }
  const isComplete = item.pagada_al_100 || percent >= 100;
  return (
    <span className={`badge ${isComplete ? "badge--abierta" : "badge--cerrada"}`}>
      {isComplete ? "100%" : `${percent}%`}
    </span>
  );
}

export function EscrituraList({
  items,
  loading,
  emptyMessage = "No hay escrituras para mostrar.",
  sortDirection,
  onSortToggle,
}: EscrituraListProps) {
  const { data: escribanos } = useEscribanos(true);

  if (loading) {
    return <p className="page-muted">Cargando escrituras…</p>;
  }

  if (items.length === 0) {
    return <p className="page-muted">{emptyMessage}</p>;
  }

  return (
    <div className="escritura-list escritura-list--saldo">
      <div className="escritura-list__header">
        <span>Nombre</span>
        <span>Escribano</span>
        <span>Estado</span>
        <button
          type="button"
          className="escritura-list__sortable"
          onClick={onSortToggle}
          aria-label={`Ordenar por fecha de creación, actualmente ${
            sortDirection === "asc" ? "ascendente" : "descendente"
          }`}
        >
          Fecha de creación <span aria-hidden="true">{sortIndicator(sortDirection)}</span>
        </button>
        <span className="escritura-list__amount">Costo total</span>
        <span className="escritura-list__amount">Total pagado</span>
        <span className="escritura-list__amount">Saldo pendiente</span>
        <span>Cobro</span>
      </div>
      {items.map((item) => (
        <Link key={item.id} to={`/escrituras/${item.id}`} className="escritura-list__row">
          <span className="escritura-list__nombre">{item.nombre}</span>
          <span>
            {displayEscribanoNombre(item.escribano_id, item.escribano_nombre, escribanos)}
          </span>
          <span>
            <span className={`badge badge--${item.estado}`}>{labelEstado(item.estado)}</span>
          </span>
          <span>{formatDate(item.created_at)}</span>
          <span className="escritura-list__amount">{formatMoney(item.costo_total)}</span>
          <span className="escritura-list__amount">{formatMoney(item.total_pagado)}</span>
          <span
            className={`escritura-list__amount${
              hasSaldoPendiente(item.saldo_pendiente) ? " saldo-resumen__pendiente" : ""
            }`}
          >
            {formatMoney(item.saldo_pendiente)}
          </span>
          <span className="escritura-list__badges">
            {cobroPercentBadge(item)}
            {item.sobrepago ? <span className="badge badge--muted">Sobrepago</span> : null}
          </span>
        </Link>
      ))}
    </div>
  );
}
