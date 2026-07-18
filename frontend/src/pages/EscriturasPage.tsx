import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { EscrituraForm } from "@/components/escrituras/EscrituraForm";
import { EscrituraList } from "@/components/escrituras/EscrituraList";
import { useCreateEscritura, useEscrituras } from "@/hooks/useEscrituras";
import type { EstadoEscritura } from "@/types/api";

type FilterTab = "todas" | EstadoEscritura;

const TABS: { id: FilterTab; label: string }[] = [
  { id: "todas", label: "Todas" },
  { id: "abierta", label: "Abiertas" },
  { id: "cerrada", label: "Cerradas" },
];

export function EscriturasPage() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<FilterTab>("todas");
  const [showCreate, setShowCreate] = useState(false);

  const filters = useMemo(
    () => (activeTab === "todas" ? undefined : { estado: activeTab }),
    [activeTab],
  );

  const { data, isLoading, error } = useEscrituras(filters);
  const createMutation = useCreateEscritura();

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

      <div className="filter-tabs" role="tablist" aria-label="Filtrar por estado">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={activeTab === tab.id}
            className={`filter-tabs__tab${activeTab === tab.id ? " filter-tabs__tab--active" : ""}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {error ? <p className="form-error">No se pudieron cargar las escrituras.</p> : null}

      <EscrituraList items={data ?? []} loading={isLoading} />

      {showCreate ? (
        <div className="modal-backdrop" role="presentation" onClick={() => setShowCreate(false)}>
          <div
            className="modal-card"
            role="dialog"
            aria-modal="true"
            aria-labelledby="nueva-escritura-title"
            onClick={(e) => e.stopPropagation()}
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
