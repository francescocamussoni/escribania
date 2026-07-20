import { FormEvent, useState } from "react";
import {
  useCreateEmpleado,
  useDeleteEmpleado,
  useEmpleados,
  useUpdateSueldo,
} from "@/hooks/useEmpleados";
import type { EmpleadoResponse } from "@/types/api";
import { formatMoney } from "@/utils/format";
import { friendlyApiError } from "@/utils/errors";

function isValidSueldo(value: string): boolean {
  const amount = Number(value);
  return Number.isFinite(amount) && amount > 0;
}

export function EmpleadosConfig() {
  const { data, isLoading, error } = useEmpleados();
  const createMutation = useCreateEmpleado();
  const updateMutation = useUpdateSueldo();
  const deleteMutation = useDeleteEmpleado();

  const [nombre, setNombre] = useState("");
  const [sueldo, setSueldo] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editSueldo, setEditSueldo] = useState("");

  const handleCreate = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmedNombre = nombre.trim();
    if (!trimmedNombre) {
      setFormError("Ingresá el nombre de la empleada.");
      return;
    }
    if (!isValidSueldo(sueldo)) {
      setFormError("El sueldo debe ser mayor a cero.");
      return;
    }

    setFormError(null);
    try {
      await createMutation.mutateAsync({ nombre: trimmedNombre, sueldo });
      setNombre("");
      setSueldo("");
    } catch (err) {
      setFormError(friendlyApiError(err, "No se pudo crear la empleada."));
    }
  };

  const startEdit = (empleado: EmpleadoResponse) => {
    setEditingId(empleado.id);
    setEditSueldo(empleado.sueldo);
    setActionError(null);
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditSueldo("");
  };

  const saveEdit = async (empleado: EmpleadoResponse) => {
    if (!isValidSueldo(editSueldo)) {
      setActionError("El sueldo debe ser mayor a cero.");
      return;
    }

    setActionError(null);
    try {
      await updateMutation.mutateAsync({ id: empleado.id, sueldo: editSueldo });
      cancelEdit();
    } catch (err) {
      setActionError(friendlyApiError(err, "No se pudo actualizar el sueldo."));
    }
  };

  const handleDelete = async (empleado: EmpleadoResponse) => {
    const confirmed = window.confirm(
      `¿Eliminar a ${empleado.nombre}? Ya no aparecerá en los cálculos futuros de Pago de Salarios.`,
    );
    if (!confirmed) {
      return;
    }

    setActionError(null);
    try {
      await deleteMutation.mutateAsync(empleado.id);
    } catch (err) {
      setActionError(friendlyApiError(err, "No se pudo eliminar la empleada."));
    }
  };

  if (isLoading) {
    return <p className="page-muted">Cargando empleados…</p>;
  }

  if (error) {
    return <p className="form-error">No se pudieron cargar los empleados.</p>;
  }

  const empleados = [...(data ?? [])].sort((a, b) => a.nombre.localeCompare(b.nombre, "es"));

  return (
    <div className="config-section">
      <section className="detail-card">
        <h2>Agregar empleada</h2>
        <form className="config-inline-form" onSubmit={handleCreate}>
          <label className="field">
            <span>Nombre</span>
            <input
              type="text"
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
              placeholder="Ej: Graciela"
              maxLength={100}
            />
          </label>
          <label className="field">
            <span>Sueldo (ARS)</span>
            <input
              type="number"
              step="0.01"
              min="0"
              value={sueldo}
              onChange={(e) => setSueldo(e.target.value)}
              placeholder="2000000"
            />
          </label>
          <button type="submit" className="button button--primary" disabled={createMutation.isPending}>
            {createMutation.isPending ? "Agregando…" : "Agregar"}
          </button>
        </form>
        {formError ? <p className="form-error">{formError}</p> : null}
      </section>

      <section className="detail-card">
        <h2>Empleadas y sueldos</h2>
        {actionError ? <p className="form-error">{actionError}</p> : null}
        {empleados.length === 0 ? (
          <p className="page-muted">No hay empleadas configuradas.</p>
        ) : (
          <div className="config-table config-table--empleados">
            <div className="config-table__header">
              <span>Nombre</span>
              <span>Sueldo</span>
              <span>Acciones</span>
            </div>
            {empleados.map((empleado) => (
              <div key={empleado.id} className="config-table__row">
                <span>{empleado.nombre}</span>
                <span>
                  {editingId === empleado.id ? (
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={editSueldo}
                      onChange={(e) => setEditSueldo(e.target.value)}
                      className="config-table__inline-input"
                    />
                  ) : (
                    <span className="config-table__amount">{formatMoney(empleado.sueldo)}</span>
                  )}
                </span>
                <span className="config-table__actions">
                  {editingId === empleado.id ? (
                    <>
                      <button
                        type="button"
                        className="button button--primary button--small"
                        onClick={() => void saveEdit(empleado)}
                        disabled={updateMutation.isPending}
                      >
                        {updateMutation.isPending ? "Guardando…" : "Guardar"}
                      </button>
                      <button
                        type="button"
                        className="button button--secondary button--small"
                        onClick={cancelEdit}
                        disabled={updateMutation.isPending}
                      >
                        Cancelar
                      </button>
                    </>
                  ) : (
                    <>
                      <button
                        type="button"
                        className="button button--secondary button--small"
                        onClick={() => startEdit(empleado)}
                      >
                        Editar sueldo
                      </button>
                      <button
                        type="button"
                        className="button button--danger button--small"
                        onClick={() => void handleDelete(empleado)}
                        disabled={deleteMutation.isPending}
                      >
                        Eliminar
                      </button>
                    </>
                  )}
                </span>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
