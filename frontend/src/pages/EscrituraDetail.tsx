import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { EscrituraForm } from "@/components/escrituras/EscrituraForm";
import { FacturaDetalle } from "@/components/escrituras/FacturaDetalle";
import { ImpuestoForm } from "@/components/escrituras/ImpuestoForm";
import { ImpuestoList } from "@/components/escrituras/ImpuestoList";
import { ImpuestosBalanceBanner } from "@/components/escrituras/ImpuestosBalanceBanner";
import { PagoClienteForm } from "@/components/escrituras/PagoClienteForm";
import { PagoClienteList } from "@/components/escrituras/PagoClienteList";
import { PagoColegioForm } from "@/components/escrituras/PagoColegioForm";
import { PagoColegioList } from "@/components/escrituras/PagoColegioList";
import { PlazoColegioBadge } from "@/components/escrituras/PlazoColegioBadge";
import { useCloseEscritura, useEscritura, usePatchEscritura } from "@/hooks/useEscrituras";
import { useCreateImpuesto, useImpuestos } from "@/hooks/useImpuestos";
import { useCreatePagoCliente } from "@/hooks/usePagosCliente";
import { useCreatePagoColegio } from "@/hooks/usePagosColegio";
import { useEscribanos } from "@/hooks/useEscribanos";
import type { BalanceImpuestosResponse } from "@/types/api";
import {
  closeEscrituraImpuestosMessage,
  closeEscrituraSaldoMessage,
  friendlyApiError,
} from "@/utils/errors";
import { formatDate, formatDateOnly, formatMoney, formatCobroPercent, displayEscribanoNombre, labelEstado } from "@/utils/format";
import { labelTipoImpuesto } from "@/utils/impuesto";

function hasSaldoPendiente(saldo: string): boolean {
  const value = Number(saldo);
  return !Number.isNaN(value) && value > 0;
}

function buildCloseTooltip(
  saldoPendiente: boolean,
  saldo: string,
  balance: BalanceImpuestosResponse | null | undefined,
): string | undefined {
  if (saldoPendiente) {
    return `Saldo pendiente de cobro: ${formatMoney(saldo)}`;
  }
  if (!balance || balance.puede_cerrar) {
    return undefined;
  }
  if (balance.impuestos_pendientes.length > 0) {
    const tipos = balance.impuestos_pendientes.map((item) => labelTipoImpuesto(item.tipo)).join(", ");
    return `Impuestos con pagos incompletos: ${tipos}`;
  }
  return `Balance de impuestos: ${formatMoney(balance.balance)}`;
}

export function EscrituraDetail() {
  const { id } = useParams<{ id: string }>();
  const { data: escritura, isLoading, error } = useEscritura(id);
  const { data: impuestosData, isLoading: impuestosLoading } = useImpuestos(id ?? "");
  const patchMutation = usePatchEscritura(id ?? "");
  const closeMutation = useCloseEscritura(id ?? "");
  const createImpuestoMutation = useCreateImpuesto(id ?? "");
  const pagoClienteMutation = useCreatePagoCliente(id ?? "");
  const pagoColegioMutation = useCreatePagoColegio(id ?? "");
  const [closeError, setCloseError] = useState<string | null>(null);

  const { data: escribanos } = useEscribanos(true);

  if (isLoading) {
    return <p className="page-muted">Cargando escritura…</p>;
  }

  if (error || !escritura || !id) {
    return (
      <div>
        <p className="form-error">No se pudo cargar la escritura.</p>
        <Link to="/escrituras" className="text-link">
          Volver al listado
        </Link>
      </div>
    );
  }

  const isClosed = escritura.estado === "cerrada";
  const saldoPendiente = hasSaldoPendiente(escritura.saldo_pendiente);
  const balanceImpuestos = impuestosData?.balance ?? escritura.balance_impuestos ?? null;
  const impuestosBlockClose = balanceImpuestos ? !balanceImpuestos.puede_cerrar : false;
  const cobroPercent = formatCobroPercent(escritura.total_pagado, escritura.costo_total);
  const closeDisabled = closeMutation.isPending || saldoPendiente || impuestosBlockClose;
  const closeTooltip = buildCloseTooltip(saldoPendiente, escritura.saldo_pendiente, balanceImpuestos);

  const handleClose = async () => {
    const confirmed = window.confirm(
      "¿Cerrar esta escritura? No podrá editarse ni registrar pagos.",
    );
    if (!confirmed) {
      return;
    }

    setCloseError(null);
    try {
      await closeMutation.mutateAsync();
    } catch (err) {
      setCloseError(
        closeEscrituraSaldoMessage(err) ??
          closeEscrituraImpuestosMessage(err) ??
          friendlyApiError(err, "No se pudo cerrar la escritura."),
      );
    }
  };

  return (
    <div className="escritura-detail">
      <header className="page-header page-header--stacked">
        <div>
          <Link to="/escrituras" className="text-link">
            ← Volver a escrituras
          </Link>
          <h1>{escritura.nombre}</h1>
          <p className="page-muted">
            {displayEscribanoNombre(
              escritura.escribano_id,
              escritura.escribano_nombre,
              escribanos,
            )}{" "}
            ·{" "}
            <span className={`badge badge--${escritura.estado}`}>{labelEstado(escritura.estado)}</span>
            {escritura.plazo_colegio ? (
              <>
                {" · "}
                <PlazoColegioBadge plazo={escritura.plazo_colegio} />
                {escritura.plazo_colegio.fecha_vencimiento ? (
                  <> · Vence {formatDateOnly(escritura.plazo_colegio.fecha_vencimiento)}</>
                ) : null}
              </>
            ) : null}
            {escritura.closed_at ? ` · Cerrada ${formatDate(escritura.closed_at)}` : null}
          </p>
        </div>
        {!isClosed ? (
          <div className="escritura-detail__close">
            <button
              type="button"
              className="button button--danger"
              onClick={handleClose}
              disabled={closeDisabled}
              title={closeTooltip}
            >
              {closeMutation.isPending ? "Cerrando…" : "Cerrar escritura"}
            </button>
            {closeError ? <p className="form-error">{closeError}</p> : null}
          </div>
        ) : null}
      </header>

      <section className="detail-card saldo-resumen">
        <h2>Saldo</h2>
        <dl className="saldo-resumen__grid">
          <div>
            <dt>Costo total</dt>
            <dd>{formatMoney(escritura.costo_total)}</dd>
          </div>
          <div>
            <dt>Total pagado</dt>
            <dd>{formatMoney(escritura.total_pagado)}</dd>
          </div>
          <div>
            <dt>Saldo pendiente</dt>
            <dd className={saldoPendiente ? "saldo-resumen__pendiente" : undefined}>
              {formatMoney(escritura.saldo_pendiente)}
            </dd>
          </div>
        </dl>
        <div className="saldo-resumen__badges">
          {cobroPercent !== null ? (
            <span
              className={`badge ${
                escritura.pagada_al_100 || cobroPercent >= 100 ? "badge--abierta" : "badge--cerrada"
              }`}
            >
              {escritura.pagada_al_100 || cobroPercent >= 100
                ? "Pagada al 100%"
                : `Cobrado al ${cobroPercent}%`}
            </span>
          ) : null}
          {escritura.sobrepago ? <span className="badge badge--muted">Sobrepago</span> : null}
        </div>
      </section>

      <section className="detail-card">
        <h2>Datos de la escritura</h2>
        <EscrituraForm
          initial={escritura}
          readOnly={isClosed}
          submitLabel="Actualizar escritura"
          onSubmit={async (payload) => {
            await patchMutation.mutateAsync(payload);
          }}
        />
      </section>

      <div className="escritura-detail__grid">
        <section className="detail-card escritura-detail__factura">
          <h2>Factura principal</h2>
          <FacturaDetalle
            factura={escritura.factura}
            readOnly={isClosed}
            onLineasChange={
              isClosed
                ? undefined
                : async (lineas_deshabilitadas) => {
                    await patchMutation.mutateAsync({ lineas_deshabilitadas });
                  }
            }
          />
        </section>

        <div className="escritura-detail__pagos-col">
          <section className="detail-card">
            <h2>Pagos del cliente</h2>
            <PagoClienteList pagos={escritura.pagos_cliente} />
            {!isClosed ? (
              <PagoClienteForm
                saldoPendiente={escritura.saldo_pendiente}
                onSubmit={async (payload) => {
                  await pagoClienteMutation.mutateAsync(payload);
                }}
              />
            ) : null}
          </section>

          <section className="detail-card">
            <h2>Pagos de la escribanía</h2>
            <p className="page-muted saldo-resumen__referencia">
              Honorarios varios proyectados (referencia):{" "}
              <strong>{formatMoney(escritura.total_leyes_notariales_proyectadas)}</strong>
            </p>
            <PagoColegioList pagos={escritura.pagos_colegio} />
            {!isClosed ? (
              <PagoColegioForm
                onSubmit={async (payload) => {
                  await pagoColegioMutation.mutateAsync(payload);
                }}
              />
            ) : null}
          </section>

          <section className="detail-card escritura-detail__impuestos">
            <h2>Impuestos</h2>
            <ImpuestosBalanceBanner balance={balanceImpuestos} />
            {impuestosLoading ? (
              <p className="page-muted">Cargando impuestos…</p>
            ) : (
              <ImpuestoList
                escrituraId={id}
                impuestos={impuestosData?.impuestos ?? []}
                readOnly={isClosed}
              />
            )}
            {!isClosed ? (
              <ImpuestoForm
                onSubmit={async (payload) => {
                  await createImpuestoMutation.mutateAsync(payload);
                }}
              />
            ) : null}
          </section>
        </div>
      </div>
    </div>
  );
}
