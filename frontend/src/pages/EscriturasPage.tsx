import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { EscrituraForm } from "@/components/escrituras/EscrituraForm";
import { EscrituraList } from "@/components/escrituras/EscrituraList";
import { useEscriturasListSession } from "@/hooks/useEscriturasListSession";
import { useCreateEscritura, useEscrituras } from "@/hooks/useEscrituras";
import { useEscribanos } from "@/hooks/useEscribanos";
import type { EstadoEscritura } from "@/types/api";
import type { EscrituraListFilters } from "@/api/escrituras";
import {
  buildEscribanoFilterOptions,
  filterByNombre,
  sortByCreatedAt,
  sortByVencimiento,
} from "@/utils/escrituraList";
import type { EstadoFilter, EscribanoFilter, CreatedAtPeriodFilter } from "@/hooks/useEscriturasListSession";
import { getDefaultPeriod, MONTH_NAMES } from "@/utils/format";

const ESTADO_TABS: { id: EstadoFilter; label: string }[] = [
  { id: "todas", label: "Todas" },
  { id: "abierta", label: "Abiertas" },
  { id: "cerrada", label: "Cerradas" },
];

const YEAR_START = 1990;

function buildYearOptions(): number[] {
  const current = new Date().getFullYear();
  return Array.from({ length: current - YEAR_START + 2 }, (_, index) => YEAR_START + index);
}

function buildServerFilters(
  escribanoFilter: EscribanoFilter,
  estadoFilter: EstadoFilter,
  createdAtPeriod: CreatedAtPeriodFilter,
): EscrituraListFilters | undefined {
  const filters: EscrituraListFilters = {};
  if (escribanoFilter) {
    filters.escribano_id = escribanoFilter;
  }
  if (estadoFilter !== "todas") {
    filters.estado = estadoFilter as EstadoEscritura;
  }
  if (createdAtPeriod) {
    filters.anio = createdAtPeriod.anio;
    filters.mes = createdAtPeriod.mes;
  }
  return Object.keys(filters).length > 0 ? filters : undefined;
}

export function EscriturasPage() {
  const navigate = useNavigate();
  const [showCreate, setShowCreate] = useState(false);
  const {
    escribanoFilter,
    estadoFilter,
    searchQuery,
    createdAtPeriod,
    sortField,
    sortDirection,
    toggleEscribanoFilter,
    setEstadoFilter,
    setCreatedAtPeriod,
    clearCreatedAtPeriod,
    setSearchQuery,
    toggleSort,
  } = useEscriturasListSession();

  const serverFilters = useMemo(
    () => buildServerFilters(escribanoFilter, estadoFilter, createdAtPeriod),
    [escribanoFilter, estadoFilter, createdAtPeriod],
  );

  const { data: allEscrituras } = useEscrituras();
  const { data, isLoading, error } = useEscrituras(serverFilters);
  const { data: escribanos } = useEscribanos(true);
  const createMutation = useCreateEscritura();

  const escribanoOptions = useMemo(
    () => buildEscribanoFilterOptions(escribanos ?? [], allEscrituras ?? []),
    [escribanos, allEscrituras],
  );

  const displayItems = useMemo(() => {
    const filtered = filterByNombre(data ?? [], searchQuery);
    if (sortField === "vencimiento") {
      return sortByVencimiento(filtered, sortDirection);
    }
    return sortByCreatedAt(filtered, sortDirection);
  }, [data, searchQuery, sortField, sortDirection]);

  const hasActiveFilters =
    escribanoFilter !== null ||
    estadoFilter !== "todas" ||
    createdAtPeriod !== null ||
    searchQuery.trim().length > 0;

  const periodDisplay = createdAtPeriod ?? getDefaultPeriod();
  const yearOptions = useMemo(() => buildYearOptions(), []);

  const emptyMessage = hasActiveFilters
    ? "No hay escrituras que coincidan con los criterios actuales."
    : "No hay escrituras para mostrar.";

  return (
    <div className="escrituras-page">
      <header className="page-header">
        <div>
          <h1>Escrituras</h1>
          <p className="page-muted">Gestión de escrituras y facturación principal.</p>
        </div>
        <button type="button" className="button button--primary" onClick={() => setShowCreate(true)}>
          Nueva escritura
        </button>
      </header>

      <div className="escrituras-page__toolbar">
        <label className="escrituras-page__search-label">
          <span className="visually-hidden">Buscar escrituras por nombre</span>
          <input
            type="search"
            className="escrituras-page__search"
            placeholder="Buscar por nombre…"
            value={searchQuery}
            onChange={(event) => setSearchQuery(event.target.value)}
          />
        </label>

        <div className="escribano-filters" role="group" aria-label="Filtrar por escribano">
          {escribanoOptions.map((option) => {
            const isActive = escribanoFilter === option.id;
            return (
              <button
                key={option.id}
                type="button"
                aria-pressed={isActive}
                className={`escribano-filters__chip${
                  isActive ? " escribano-filters__chip--active" : ""
                }`}
                onClick={() => toggleEscribanoFilter(option.id)}
              >
                {option.label}
              </button>
            );
          })}
        </div>
      </div>

      <div className="escrituras-page__secondary-toolbar">
        <div className="filter-tabs" role="tablist" aria-label="Filtrar por estado">
          {ESTADO_TABS.map((tab) => (
            <button
              key={tab.id}
              type="button"
              role="tab"
              aria-selected={estadoFilter === tab.id}
              className={`filter-tabs__tab${
                estadoFilter === tab.id ? " filter-tabs__tab--active" : ""
              }`}
              onClick={() => setEstadoFilter(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="escrituras-page__period-filter" role="group" aria-label="Filtrar por fecha de creación">
          <label className="field escrituras-page__period-field">
            <span>Mes</span>
            <select
              value={periodDisplay.mes}
              onChange={(event) =>
                setCreatedAtPeriod({
                  anio: periodDisplay.anio,
                  mes: Number(event.target.value),
                })
              }
            >
              {MONTH_NAMES.map((name, index) => (
                <option key={name} value={index + 1}>
                  {name}
                </option>
              ))}
            </select>
          </label>
          <label className="field escrituras-page__period-field">
            <span>Año</span>
            <select
              value={periodDisplay.anio}
              onChange={(event) =>
                setCreatedAtPeriod({
                  anio: Number(event.target.value),
                  mes: periodDisplay.mes,
                })
              }
            >
              {yearOptions.map((year) => (
                <option key={year} value={year}>
                  {year}
                </option>
              ))}
            </select>
          </label>
          {createdAtPeriod ? (
            <button
              type="button"
              className="button button--secondary escrituras-page__period-clear"
              onClick={clearCreatedAtPeriod}
            >
              Eliminar filtro
            </button>
          ) : null}
        </div>
      </div>

      {error ? <p className="form-error">No se pudieron cargar las escrituras.</p> : null}

      <EscrituraList
        items={displayItems}
        loading={isLoading}
        emptyMessage={emptyMessage}
        sortField={sortField}
        sortDirection={sortDirection}
        onSort={toggleSort}
      />

      {showCreate ? (
        <div className="modal-backdrop" role="presentation" onClick={() => setShowCreate(false)}>
          <div
            className="modal-card"
            role="dialog"
            aria-modal="true"
            aria-labelledby="nueva-escritura-title"
            onClick={(event) => event.stopPropagation()}
          >
            <h2 id="nueva-escritura-title">Nueva escritura</h2>
            <EscrituraForm
              submitLabel="Crear escritura"
              onCancel={() => setShowCreate(false)}
              onSubmit={async (payload) => {
                const created = await createMutation.mutateAsync(payload);
                setShowCreate(false);
                navigate(`/escrituras/${created.id}`);
              }}
            />
          </div>
        </div>
      ) : null}
    </div>
  );
}
