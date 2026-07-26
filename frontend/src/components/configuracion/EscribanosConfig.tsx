import { FormEvent, useState } from "react";
import { ApiRequestError } from "@/api/client";
import {
  useCreateEscribano,
  useDeactivateEscribano,
  useEscribanos,
  useUpdateEscribano,
} from "@/hooks/useEscribanos";
import type { EscribanoResponse } from "@/types/api";
import { friendlyApiError } from "@/utils/errors";

type DeactivateModal =
  | { kind: "confirm"; escribano: EscribanoResponse }
  | { kind: "force"; escribano: EscribanoResponse; escriturasCount: number };

function getEscriturasCount(error: unknown): number | null {
  if (!(error instanceof ApiRequestError) || error.status !== 409) {
    return null;
  }
  const detail = error.body?.detail as unknown;
  if (typeof detail === "object" && detail !== null && "escrituras_count" in detail) {
    const count = (detail as { escrituras_count: number }).escrituras_count;
    return Number.isFinite(count) ? count : null;
  }
  return null;
}

export function EscribanosConfig() {
  const { data, isLoading, error } = useEscribanos(true);
  const createMutation = useCreateEscribano();
  const deactivateMutation = useDeactivateEscribano();
  const updateMutation = useUpdateEscribano();

  const [nombre, setNombre] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [modal, setModal] = useState<DeactivateModal | null>(null);

  const handleCreate = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmed = nombre.trim();
    if (!trimmed) {
      setFormError("Ingresá un nombre para el escribano.");
      return;
    }

    setFormError(null);
    try {
      await createMutation.mutateAsync(trimmed);
      setNombre("");
    } catch (err) {
      setFormError(friendlyApiError(err, "No se pudo crear el escribano."));
    }
  };

  const handleDeactivate = async (escribano: EscribanoResponse, force = false) => {
    setActionError(null);
    try {
      await deactivateMutation.mutateAsync({ id: escribano.id, force });
      setModal(null);
    } catch (err) {
      const count = getEscriturasCount(err);
      if (!force && count !== null) {
        setModal({ kind: "force", escribano, escriturasCount: count });
        return;
      }
      setActionError(friendlyApiError(err, "No se pudo desactivar el escribano."));
    }
  };

  const handleMonotributistaToggle = async (escribano: EscribanoResponse, checked: boolean) => {
    setActionError(null);
    try {
      await updateMutation.mutateAsync({
        id: escribano.id,
        payload: { monotributista: checked },
      });
    } catch (err) {
      setActionError(
        friendlyApiError(err, "No se pudo actualizar el régimen del escribano."),
      );
    }
  };

  if (isLoading) {
    return <p className="page-muted">Cargando escribanos…</p>;
  }

  if (error) {
    return <p className="form-error">No se pudieron cargar los escribanos.</p>;
  }

  const escribanos = [...(data ?? [])].sort((a, b) => a.nombre.localeCompare(b.nombre, "es"));

  return (
    <div className="config-section">
      <section className="detail-card">
        <h2>Agregar escribano</h2>
        <form className="config-inline-form" onSubmit={handleCreate}>
          <label className="field">
            <span>Nombre</span>
            <input
              type="text"
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
              placeholder="Ej: Martínez"
              maxLength={100}
            />
          </label>
          <button type="submit" className="button button--primary" disabled={createMutation.isPending}>
            {createMutation.isPending ? "Agregando…" : "Agregar"}
          </button>
        </form>
        {formError ? <p className="form-error">{formError}</p> : null}
      </section>

      <section className="detail-card">
        <h2>Escribanos configurados</h2>
        {actionError ? <p className="form-error">{actionError}</p> : null}
        {escribanos.length === 0 ? (
          <p className="page-muted">No hay escribanos configurados.</p>
        ) : (
          <div className="config-table">
            <div className="config-table__header config-table__header--escribanos">
              <span>Nombre</span>
              <span>Estado</span>
              <span>Monotributista</span>
              <span>Acciones</span>
            </div>
            {escribanos.map((escribano) => (
              <div key={escribano.id} className="config-table__row config-table__row--escribanos">
                <span>
                  {escribano.nombre}
                  {!escribano.activo ? <span className="badge badge--muted"> (inactivo)</span> : null}
                </span>
                <span>{escribano.activo ? "Activo" : "Inactivo"}</span>
                <span>
                  {escribano.activo ? (
                    <label className="config-toggle">
                      <input
                        type="checkbox"
                        checked={escribano.monotributista}
                        disabled={updateMutation.isPending}
                        onChange={(event) =>
                          void handleMonotributistaToggle(escribano, event.target.checked)
                        }
                      />
                      <span>{escribano.monotributista ? "Sí" : "No"}</span>
                    </label>
                  ) : (
                    <span className="page-muted">—</span>
                  )}
                </span>
                <span>
                  {escribano.activo ? (
                    <button
                      type="button"
                      className="button button--danger button--small"
                      onClick={() => setModal({ kind: "confirm", escribano })}
                      disabled={deactivateMutation.isPending}
                    >
                      Desactivar
                    </button>
                  ) : (
                    <span className="page-muted">—</span>
                  )}
                </span>
              </div>
            ))}
          </div>
        )}
      </section>

      {modal ? (
        <div className="modal-backdrop" role="presentation" onClick={() => setModal(null)}>
          <div
            className="modal-card"
            role="dialog"
            aria-modal="true"
            aria-labelledby="deactivate-escribano-title"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 id="deactivate-escribano-title">
              {modal.kind === "force" ? "Confirmar desactivación" : "Desactivar escribano"}
            </h2>
            {modal.kind === "confirm" ? (
              <p>
                ¿Desactivar a <strong>{modal.escribano.nombre}</strong>? Ya no aparecerá al crear
                nuevas escrituras.
              </p>
            ) : (
              <p>
                <strong>{modal.escribano.nombre}</strong> tiene{" "}
                <strong>{modal.escriturasCount}</strong>{" "}
                {modal.escriturasCount === 1 ? "escritura asociada" : "escrituras asociadas"}.
                Las escrituras históricas conservarán su nombre con la etiqueta &quot;(inactivo)&quot;.
                ¿Confirmás la desactivación?
              </p>
            )}
            <div className="form-actions">
              <button type="button" className="button button--secondary" onClick={() => setModal(null)}>
                Cancelar
              </button>
              <button
                type="button"
                className="button button--danger"
                disabled={deactivateMutation.isPending}
                onClick={() =>
                  void handleDeactivate(modal.escribano, modal.kind === "force")
                }
              >
                {deactivateMutation.isPending ? "Desactivando…" : "Desactivar"}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
