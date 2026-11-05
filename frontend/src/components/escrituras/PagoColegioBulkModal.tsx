import { FormEvent, useEffect, useMemo, useState } from "react";
import { previewPagoColegioBulk, useConfirmPagoColegioBulk } from "@/hooks/usePagosColegio";
import type { PagoColegioBulkMotivoNoElegible, PagoColegioBulkPreviewItem } from "@/types/api";
import { friendlyApiError } from "@/utils/errors";
import { formatMoney } from "@/utils/format";

interface PagoColegioBulkModalProps {
  escrituraIds: string[];
  onClose: () => void;
  onSuccess: () => void;
}

function todayIsoDate(): string {
  return new Date().toISOString().slice(0, 10);
}

function labelMotivoNoElegible(motivo: PagoColegioBulkMotivoNoElegible | null | undefined): string {
  switch (motivo) {
    case "cerrada":
      return "Cerrada";
    case "sin_pendiente":
      return "Sin pendiente";
    default:
      return "No elegible";
  }
}

function initialMontosFromItems(items: PagoColegioBulkPreviewItem[]): Record<string, string> {
  return Object.fromEntries(
    items.filter((item) => item.elegible).map((item) => [item.escritura_id, item.pendiente]),
  );
}

export function PagoColegioBulkModal({
  escrituraIds,
  onClose,
  onSuccess,
}: PagoColegioBulkModalProps) {
  const confirmMutation = useConfirmPagoColegioBulk();
  const [fecha, setFecha] = useState(todayIsoDate());
  const [items, setItems] = useState<PagoColegioBulkPreviewItem[]>([]);
  const [montos, setMontos] = useState<Record<string, string>>({});
  const [loadingPreview, setLoadingPreview] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoadingPreview(true);
    setError(null);

    void previewPagoColegioBulk({ escritura_ids: escrituraIds })
      .then((response) => {
        if (cancelled) {
          return;
        }
        setItems(response.items);
        setMontos(initialMontosFromItems(response.items));
      })
      .catch((err) => {
        if (!cancelled) {
          setError(friendlyApiError(err, "No se pudo cargar el preview del pago masivo."));
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoadingPreview(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [escrituraIds]);

  const elegibleItems = useMemo(() => items.filter((item) => item.elegible), [items]);

  const totalConfirmacion = useMemo(() => {
    return elegibleItems.reduce((acc, item) => {
      const value = Number(montos[item.escritura_id] ?? "0");
      return acc + (Number.isNaN(value) ? 0 : value);
    }, 0);
  }, [elegibleItems, montos]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);

    if (elegibleItems.length === 0) {
      setError("No hay escrituras elegibles para confirmar.");
      return;
    }

    const payloadItems = elegibleItems.map((item) => {
      const monto = (montos[item.escritura_id] ?? "").trim();
      return { escritura_id: item.escritura_id, monto };
    });

    if (payloadItems.some((item) => !item.monto || Number(item.monto) <= 0)) {
      setError("Todos los montos deben ser mayores a cero.");
      return;
    }

    try {
      await confirmMutation.mutateAsync({
        fecha,
        items: payloadItems,
      });
      onSuccess();
      onClose();
    } catch (err) {
      setError(friendlyApiError(err, "No se pudo confirmar el pago masivo."));
    }
  };

  return (
    <div className="modal-backdrop" role="presentation" onClick={onClose}>
      <div
        className="modal-card modal-card--wide"
        role="dialog"
        aria-modal="true"
        aria-labelledby="pago-colegio-bulk-title"
        onClick={(event) => event.stopPropagation()}
      >
        <h2 id="pago-colegio-bulk-title">Pago al colegio de escribanos</h2>
        <p className="page-muted">
          Revise el pendiente de Total impuestos por escritura. Puede ajustar los montos antes de
          confirmar.
        </p>

        {loadingPreview ? <p className="page-muted">Cargando preview…</p> : null}

        {!loadingPreview && items.length > 0 ? (
          <form className="bulk-pago-form" onSubmit={handleSubmit}>
            <div className="bulk-pago-table">
              <div className="bulk-pago-table__header">
                <span>Escritura</span>
                <span>Pendiente</span>
                <span>Monto a pagar</span>
                <span>Estado</span>
              </div>
              {items.map((item) => (
                <div key={item.escritura_id} className="bulk-pago-table__row">
                  <span className="bulk-pago-table__nombre">{item.escritura_nombre}</span>
                  <span className="bulk-pago-table__amount">{formatMoney(item.pendiente)}</span>
                  <label className="field bulk-pago-table__monto">
                    <span className="visually-hidden">Monto para {item.escritura_nombre}</span>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={montos[item.escritura_id] ?? ""}
                      disabled={!item.elegible || confirmMutation.isPending}
                      onChange={(event) =>
                        setMontos((current) => ({
                          ...current,
                          [item.escritura_id]: event.target.value,
                        }))
                      }
                      required={item.elegible}
                    />
                  </label>
                  <span>
                    {item.elegible ? (
                      <span className="badge badge--abierta">Elegible</span>
                    ) : (
                      <span className="badge badge--muted">{labelMotivoNoElegible(item.motivo)}</span>
                    )}
                  </span>
                </div>
              ))}
            </div>

            <label className="field">
              <span>Fecha de pago (todas las escrituras)</span>
              <input
                type="date"
                value={fecha}
                onChange={(event) => setFecha(event.target.value)}
                required
                disabled={confirmMutation.isPending}
              />
            </label>

            <p className="bulk-pago-form__total">
              Total a confirmar: <strong>{formatMoney(totalConfirmacion.toFixed(2))}</strong>
            </p>

            {error ? <p className="form-error">{error}</p> : null}

            <div className="modal-card__actions">
              <button
                type="button"
                className="button button--secondary"
                onClick={onClose}
                disabled={confirmMutation.isPending}
              >
                Cancelar
              </button>
              <button
                type="submit"
                className="button button--primary"
                disabled={confirmMutation.isPending || elegibleItems.length === 0}
              >
                {confirmMutation.isPending ? "Confirmando…" : "Confirmar pagos"}
              </button>
            </div>
          </form>
        ) : null}

        {!loadingPreview && items.length === 0 && !error ? (
          <p className="page-muted">No hay escrituras para procesar.</p>
        ) : null}

        {!loadingPreview && error && items.length === 0 ? (
          <div className="modal-card__actions">
            <button type="button" className="button button--secondary" onClick={onClose}>
              Cerrar
            </button>
          </div>
        ) : null}
      </div>
    </div>
  );
}
