import { useState } from "react";
import { ImpuestoForm } from "@/components/escrituras/ImpuestoForm";
import { ImpuestoPagoClienteForm } from "@/components/escrituras/ImpuestoPagoClienteForm";
import { ImpuestoPagoEscribaniaForm } from "@/components/escrituras/ImpuestoPagoEscribaniaForm";
import {
  useDeleteImpuesto,
  useDeletePagoImpuestoCliente,
  useDeletePagoImpuestoEscribania,
  useUpdateImpuesto,
  useUpdatePagoImpuestoCliente,
  useUpdatePagoImpuestoEscribania,
  useUpsertPagoImpuestoCliente,
  useUpsertPagoImpuestoEscribania,
} from "@/hooks/useImpuestos";
import type { ImpuestoResponse } from "@/types/api";
import {
  labelDireccionProrrateo,
  labelEstadoPagos,
  labelTipoImpuesto,
} from "@/utils/impuesto";
import { friendlyApiError } from "@/utils/errors";
import { formatDateOnly, formatMoney } from "@/utils/format";

interface ImpuestoRowProps {
  escrituraId: string;
  impuesto: ImpuestoResponse;
  readOnly: boolean;
}

function ImpuestoRow({ escrituraId, impuesto, readOnly }: ImpuestoRowProps) {
  const [expanded, setExpanded] = useState(false);
  const [editing, setEditing] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const deleteImpuestoMutation = useDeleteImpuesto(escrituraId);
  const updateImpuestoMutation = useUpdateImpuesto(escrituraId);
  const upsertCliente = useUpsertPagoImpuestoCliente(escrituraId, impuesto.id);
  const updateCliente = useUpdatePagoImpuestoCliente(escrituraId, impuesto.id);
  const deleteCliente = useDeletePagoImpuestoCliente(escrituraId, impuesto.id);
  const upsertEscribania = useUpsertPagoImpuestoEscribania(escrituraId, impuesto.id);
  const updateEscribania = useUpdatePagoImpuestoEscribania(escrituraId, impuesto.id);
  const deleteEscribania = useDeletePagoImpuestoEscribania(escrituraId, impuesto.id);

  const canDeleteImpuesto =
    !readOnly && impuesto.estado_pagos === "sin_pagos" && !deleteImpuestoMutation.isPending;

  const handleDeleteImpuesto = async () => {
    const confirmed = window.confirm(`¿Eliminar el impuesto ${labelTipoImpuesto(impuesto.tipo)}?`);
    if (!confirmed) {
      return;
    }
    setDeleteError(null);
    try {
      await deleteImpuestoMutation.mutateAsync(impuesto.id);
    } catch (err) {
      setDeleteError(friendlyApiError(err, "No se pudo eliminar el impuesto."));
    }
  };

  return (
    <article className="impuesto-card">
      <div className="impuesto-card__header">
        <div>
          <strong>{labelTipoImpuesto(impuesto.tipo)}</strong>
          <span className={`badge badge--${impuesto.estado_pagos === "completos" ? "abierta" : "cerrada"}`}>
            {labelEstadoPagos(impuesto.estado_pagos)}
          </span>
        </div>
        <div className="impuesto-card__actions">
          {!readOnly ? (
            <button
              type="button"
              className="button button--small"
              onClick={() => {
                setEditing((value) => !value);
                setExpanded(false);
              }}
            >
              {editing ? "Cerrar edición" : "Editar"}
            </button>
          ) : null}
          <button
            type="button"
            className="button button--small"
            onClick={() => setExpanded((value) => !value)}
          >
            {expanded ? "Ocultar pagos" : "Pagos"}
          </button>
          {canDeleteImpuesto ? (
            <button
              type="button"
              className="button button--danger button--small"
              onClick={handleDeleteImpuesto}
            >
              Eliminar
            </button>
          ) : null}
        </div>
      </div>
      <dl className="impuesto-card__meta">
        <div>
          <dt>Período</dt>
          <dd>
            {formatDateOnly(impuesto.periodo_inicio)} – {formatDateOnly(impuesto.periodo_fin)}
          </dd>
        </div>
        <div>
          <dt>Corte</dt>
          <dd>{formatDateOnly(impuesto.fecha_corte)}</dd>
        </div>
        <div>
          <dt>Prorrateo</dt>
          <dd>{labelDireccionProrrateo(impuesto.direccion_prorrateo)}</dd>
        </div>
        <div>
          <dt>Monto sugerido</dt>
          <dd>{formatMoney(impuesto.monto_prorrateado_sugerido)}</dd>
        </div>
      </dl>
      {deleteError ? <p className="form-error">{deleteError}</p> : null}
      {editing && !readOnly ? (
        <ImpuestoForm
          initial={impuesto}
          onCancel={() => setEditing(false)}
          onSubmit={async (payload) => {
            await updateImpuestoMutation.mutateAsync({ impuestoId: impuesto.id, payload });
            setEditing(false);
          }}
        />
      ) : null}
      {expanded ? (
        <div className="impuesto-card__pagos">
          {!readOnly ? (
            <>
              <ImpuestoPagoClienteForm
                montoSugerido={impuesto.monto_prorrateado_sugerido}
                initialMonto={impuesto.pago_cliente?.monto}
                initialFecha={impuesto.pago_cliente?.fecha}
                isUpdate={impuesto.pago_cliente !== null}
                onSubmit={async (payload) => {
                  if (impuesto.pago_cliente) {
                    await updateCliente.mutateAsync(payload);
                  } else {
                    await upsertCliente.mutateAsync(payload);
                  }
                }}
                onDelete={
                  impuesto.pago_cliente
                    ? async () => {
                        await deleteCliente.mutateAsync();
                      }
                    : undefined
                }
              />
              <ImpuestoPagoEscribaniaForm
                initialMonto={impuesto.pago_escribania?.monto}
                initialFecha={impuesto.pago_escribania?.fecha}
                isUpdate={impuesto.pago_escribania !== null}
                onSubmit={async (payload) => {
                  if (impuesto.pago_escribania) {
                    await updateEscribania.mutateAsync(payload);
                  } else {
                    await upsertEscribania.mutateAsync(payload);
                  }
                }}
                onDelete={
                  impuesto.pago_escribania
                    ? async () => {
                        await deleteEscribania.mutateAsync();
                      }
                    : undefined
                }
              />
            </>
          ) : (
            <div className="impuesto-card__pagos-readonly">
              <p>
                Cliente:{" "}
                {impuesto.pago_cliente
                  ? `${formatMoney(impuesto.pago_cliente.monto)} (${formatDateOnly(impuesto.pago_cliente.fecha)})`
                  : "—"}
              </p>
              <p>
                Escribanía:{" "}
                {impuesto.pago_escribania
                  ? `${formatMoney(impuesto.pago_escribania.monto)} (${formatDateOnly(impuesto.pago_escribania.fecha)})`
                  : "—"}
              </p>
            </div>
          )}
        </div>
      ) : null}
    </article>
  );
}

interface ImpuestoListProps {
  escrituraId: string;
  impuestos: ImpuestoResponse[];
  readOnly: boolean;
}

export function ImpuestoList({ escrituraId, impuestos, readOnly }: ImpuestoListProps) {
  if (impuestos.length === 0) {
    return <p className="page-muted">Sin impuestos registrados.</p>;
  }

  return (
    <div className="impuestos-list">
      {impuestos.map((impuesto) => (
        <ImpuestoRow key={impuesto.id} escrituraId={escrituraId} impuesto={impuesto} readOnly={readOnly} />
      ))}
    </div>
  );
}
