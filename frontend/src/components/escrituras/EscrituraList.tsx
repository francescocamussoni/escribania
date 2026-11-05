import { Link } from "react-router-dom";
import type { EscrituraListItem } from "@/types/api";
import { useEscribanos } from "@/hooks/useEscribanos";
import type { SortDirection, SortField } from "@/utils/escrituraList";
import { isSelectableForBulkPagoColegio } from "@/utils/escrituraList";
import { PlazoColegioBadge } from "@/components/escrituras/PlazoColegioBadge";
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
  sortField: SortField;
  sortDirection: SortDirection;
  onSort: (field: SortField) => void;
  selectedIds?: ReadonlySet<string>;
  onToggleSelect?: (id: string) => void;
  onToggleSelectAll?: () => void;
}

function hasSaldoPendiente(saldo: string): boolean {
  const value = Number(saldo);
  return !Number.isNaN(value) && value > 0;
}

function sortIndicator(active: boolean, direction: SortDirection): string {
  if (!active) {
    return "";
  }
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
  sortField,
  sortDirection,
  onSort,
  selectedIds,
  onToggleSelect,
  onToggleSelectAll,
}: EscrituraListProps) {
  const { data: escribanos } = useEscribanos(true);
  const selectionEnabled = Boolean(selectedIds && onToggleSelect && onToggleSelectAll);

  const selectableItems = selectionEnabled ? items.filter(isSelectableForBulkPagoColegio) : [];
  const allSelectableSelected =
    selectionEnabled &&
    selectableItems.length > 0 &&
    selectableItems.every((item) => selectedIds?.has(item.id));

  if (loading) {
    return <p className="page-muted">Cargando escrituras…</p>;
  }

  if (items.length === 0) {
    return <p className="page-muted">{emptyMessage}</p>;
  }

  return (
    <div
      className={`escritura-list escritura-list--saldo${
        selectionEnabled ? " escritura-list--selectable" : ""
      }`}
    >
      <div className="escritura-list__header">
        {selectionEnabled ? (
          <label className="escritura-list__checkbox">
            <span className="visually-hidden">Seleccionar todas las escrituras elegibles</span>
            <input
              type="checkbox"
              checked={allSelectableSelected}
              disabled={selectableItems.length === 0}
              onChange={onToggleSelectAll}
              aria-label="Seleccionar todas las escrituras elegibles"
            />
          </label>
        ) : null}
        <span>Nombre</span>
        <span>Escribano</span>
        <span>Estado</span>
        <button
          type="button"
          className="escritura-list__sortable"
          onClick={() => onSort("vencimiento")}
          aria-label={`Ordenar por vencimiento, actualmente ${
            sortField === "vencimiento"
              ? sortDirection === "asc"
                ? "ascendente"
                : "descendente"
              : "inactivo"
          }`}
        >
          Plazo Colegio{" "}
          <span aria-hidden="true">{sortIndicator(sortField === "vencimiento", sortDirection)}</span>
        </button>
        <button
          type="button"
          className="escritura-list__sortable"
          onClick={() => onSort("created_at")}
          aria-label={`Ordenar por fecha de creación, actualmente ${
            sortField === "created_at"
              ? sortDirection === "asc"
                ? "ascendente"
                : "descendente"
              : "inactivo"
          }`}
        >
          Fecha de creación{" "}
          <span aria-hidden="true">{sortIndicator(sortField === "created_at", sortDirection)}</span>
        </button>
        <span className="escritura-list__amount">Costo total</span>
        <span className="escritura-list__amount">Total pagado</span>
        <span className="escritura-list__amount">Saldo pendiente</span>
        <span>Cobro</span>
      </div>
      {items.map((item) => {
        const selectable = selectionEnabled && isSelectableForBulkPagoColegio(item);
        const selected = selectionEnabled && selectedIds?.has(item.id);

        return (
          <div key={item.id} className="escritura-list__row">
            {selectionEnabled ? (
              <label
                className="escritura-list__checkbox"
                onClick={(event) => event.stopPropagation()}
              >
                <span className="visually-hidden">Seleccionar {item.nombre}</span>
                <input
                  type="checkbox"
                  checked={Boolean(selected)}
                  disabled={!selectable}
                  onChange={() => onToggleSelect?.(item.id)}
                  aria-label={`Seleccionar ${item.nombre}`}
                />
              </label>
            ) : null}
            <Link to={`/escrituras/${item.id}`} className="escritura-list__nombre text-link">
              {item.nombre}
            </Link>
            <span>
              {displayEscribanoNombre(item.escribano_id, item.escribano_nombre, escribanos)}
            </span>
            <span>
              <span className={`badge badge--${item.estado}`}>{labelEstado(item.estado)}</span>
            </span>
            <span>
              {item.plazo_colegio ? <PlazoColegioBadge plazo={item.plazo_colegio} /> : null}
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
          </div>
        );
      })}
    </div>
  );
}
