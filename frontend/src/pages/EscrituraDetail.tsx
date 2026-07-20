import { Link, useParams } from "react-router-dom";
import { EscrituraForm } from "@/components/escrituras/EscrituraForm";
import { FacturaDetalle } from "@/components/escrituras/FacturaDetalle";
import { GastoForm } from "@/components/escrituras/GastoForm";
import {
  useAddGasto,
  useCloseEscritura,
  useEscritura,
  usePatchEscritura,
} from "@/hooks/useEscrituras";
import { formatDate, formatMoney, displayEscribanoNombre, labelEstado } from "@/utils/format";
import { useEscribanos } from "@/hooks/useEscribanos";

export function EscrituraDetail() {
  const { id } = useParams<{ id: string }>();
  const { data: escritura, isLoading, error } = useEscritura(id);
  const patchMutation = usePatchEscritura(id ?? "");
  const closeMutation = useCloseEscritura(id ?? "");
  const addGastoMutation = useAddGasto(id ?? "");

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

  const handleClose = async () => {
    const confirmed = window.confirm(
      "¿Cerrar esta escritura? No podrá editarse ni agregar gastos.",
    );
    if (!confirmed) {
      return;
    }
    await closeMutation.mutateAsync();
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
            {escritura.closed_at ? ` · Cerrada ${formatDate(escritura.closed_at)}` : null}
          </p>
        </div>
        {!isClosed ? (
          <button
            type="button"
            className="button button--danger"
            onClick={handleClose}
            disabled={closeMutation.isPending}
          >
            {closeMutation.isPending ? "Cerrando…" : "Cerrar escritura"}
          </button>
        ) : null}
      </header>

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

      <section className="detail-card">
        <h2>Factura principal</h2>
        <FacturaDetalle factura={escritura.factura} />
      </section>

      <section className="detail-card">
        <h2>Gastos adicionales</h2>
        {escritura.gastos_adicionales.length === 0 ? (
          <p className="page-muted">Sin gastos adicionales registrados.</p>
        ) : (
          <div className="gastos-list">
            <div className="gastos-list__header">
              <span>Concepto</span>
              <span>Dirección</span>
              <span>Fecha</span>
              <span className="gastos-list__amount">Monto</span>
            </div>
            {escritura.gastos_adicionales.map((gasto) => (
              <div key={gasto.id} className="gastos-list__row">
                <span>{gasto.concepto}</span>
                <span className="gastos-list__direccion">{gasto.direccion}</span>
                <span>{gasto.fecha}</span>
                <span className="gastos-list__amount">{formatMoney(gasto.monto)}</span>
              </div>
            ))}
          </div>
        )}

        {!isClosed ? (
          <GastoForm
            onSubmit={async (payload) => {
              await addGastoMutation.mutateAsync(payload);
            }}
          />
        ) : null}
      </section>
    </div>
  );
}
