import { useState } from "react";
import type { GastoExtraordinarioResponse } from "@/types/api";
import { friendlyApiError } from "@/utils/errors";
import { formatDateOnly, formatMoney } from "@/utils/format";

interface GastoExtraordinarioListProps {
  gastos: GastoExtraordinarioResponse[];
  onEdit: (gasto: GastoExtraordinarioResponse) => void;
  onDelete: (gastoId: string) => Promise<void>;
}

export function GastoExtraordinarioList({ gastos, onEdit, onDelete }: GastoExtraordinarioListProps) {
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  if (gastos.length === 0) {
    return <p className="page-muted">Sin gastos extraordinarios registrados en este período.</p>;
  }

  const handleDelete = async (gasto: GastoExtraordinarioResponse) => {
    const confirmed = window.confirm(`¿Eliminar el gasto "${gasto.concepto}"?`);
    if (!confirmed) {
      return;
    }
    setDeleteError(null);
    setDeletingId(gasto.id);
    try {
      await onDelete(gasto.id);
    } catch (err) {
      setDeleteError(friendlyApiError(err, "No se pudo eliminar el gasto extraordinario."));
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="gastos-list">
      <div className="gastos-list__header gastos-extra-list__row">
        <span>Concepto</span>
        <span>Fecha</span>
        <span className="gastos-list__amount">Monto</span>
        <span className="gastos-extra-list__actions">Acciones</span>
      </div>
      {gastos.map((gasto) => (
        <div key={gasto.id} className="gastos-list__row gastos-extra-list__row">
          <span>{gasto.concepto}</span>
          <span>{formatDateOnly(gasto.fecha)}</span>
          <span className="gastos-list__amount">{formatMoney(gasto.monto)}</span>
          <span className="gastos-extra-list__actions">
            <button
              type="button"
              className="button button--small"
              onClick={() => onEdit(gasto)}
              disabled={deletingId === gasto.id}
            >
              Editar
            </button>
            <button
              type="button"
              className="button button--danger button--small"
              onClick={() => void handleDelete(gasto)}
              disabled={deletingId === gasto.id}
            >
              {deletingId === gasto.id ? "Eliminando…" : "Eliminar"}
            </button>
          </span>
        </div>
      ))}
      {deleteError ? <p className="form-error">{deleteError}</p> : null}
    </div>
  );
}
