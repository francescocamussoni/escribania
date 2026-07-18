import { FormEvent, useEffect, useState } from "react";
import type { ConfiguracionInput, ConfiguracionResponse } from "@/types/api";
import {
  useConfiguracion,
  useConfiguracionHistory,
  useCreateConfiguracion,
} from "@/hooks/useConfiguracion";
import { formatDate } from "@/utils/format";
import { friendlyApiError } from "@/utils/errors";

type ConfigFieldKey = Exclude<keyof ConfiguracionInput, "descripcion">;

interface FieldDef {
  key: ConfigFieldKey;
  label: string;
  step?: string;
}

interface SectionDef {
  title: string;
  fields: FieldDef[];
}

const CONFIG_SECTIONS: SectionDef[] = [
  {
    title: "Honorarios",
    fields: [
      { key: "honorario_pct", label: "% honorario principal", step: "0.0001" },
      { key: "honorario_min", label: "Honorario mínimo (ARS)" },
      { key: "certificacion_pct", label: "% certificación", step: "0.0001" },
      { key: "aporte_pct", label: "% aporte 12", step: "0.0001" },
      { key: "cinco_pct_hon_pct", label: "% 5 honorarios", step: "0.0001" },
      { key: "cinco_pct_hon_min", label: "Mínimo 5% honorarios (ARS)" },
      { key: "firma_honorarios", label: "Firma honorarios (ARS)" },
    ],
  },
  {
    title: "Leyes notariales",
    fields: [
      { key: "art2_a_pct", label: "Art. 2 a) %", step: "0.0001" },
      { key: "art12_a_pct", label: "Art. 12 a) %", step: "0.0001" },
      { key: "art12_a_min", label: "Art. 12 a) mínimo (ARS)" },
      { key: "art12_c_pct", label: "Art. 12 c) %", step: "0.0001" },
      { key: "art12_f", label: "Art. 12 f) fijo (ARS)" },
    ],
  },
  {
    title: "Impuestos y sellos",
    fields: [
      { key: "tasa_3pm_pct", label: "Tasa 3‰ %", step: "0.0001" },
      { key: "sellos_pct", label: "Sellos %", step: "0.0001" },
      { key: "sellos_ajuste_fijo", label: "Ajuste fijo sellos (ARS)" },
      { key: "tasa_75pm_pct", label: "Tasa 7,5‰ %", step: "0.0001" },
      { key: "firma_impuestos", label: "Firma impuestos (ARS)" },
    ],
  },
  {
    title: "Gastos administrativos fijos",
    fields: [
      { key: "inscripcion", label: "Inscripción (ARS)" },
      { key: "protocolo", label: "Protocolo (ARS)" },
      { key: "ii_certificados", label: "II Certificados (ARS)" },
      { key: "municipio", label: "Municipio (ARS)" },
      { key: "fotocopias_urgentes", label: "Fotocopias urgentes (ARS)" },
      { key: "certificaciones_extra", label: "Certificaciones extra (ARS)" },
      { key: "catastro", label: "Catastro (ARS)" },
      { key: "testimonio", label: "Testimonio (ARS)" },
      { key: "concuerda", label: "Concuerda (ARS)" },
      { key: "informes_notariales", label: "Informes notariales (ARS)" },
      { key: "extracto", label: "Extracto (ARS)" },
      { key: "fotocopias_simples", label: "Fotocopias simples (ARS)" },
      { key: "tasas_minimas", label: "Tasas mínimas (ARS)" },
    ],
  },
  {
    title: "Salarios",
    fields: [{ key: "salario_secretarias_total", label: "Pool total secretarias (ARS)" }],
  },
];

const ALL_FIELD_KEYS = CONFIG_SECTIONS.flatMap((section) => section.fields.map((field) => field.key));

function responseToFormState(config: ConfiguracionResponse): Record<ConfigFieldKey, string> {
  const state = {} as Record<ConfigFieldKey, string>;
  for (const key of ALL_FIELD_KEYS) {
    state[key] = config[key] ?? "";
  }
  return state;
}

function buildPayload(
  descripcion: string,
  values: Record<ConfigFieldKey, string>,
): ConfiguracionInput {
  const payload: ConfiguracionInput = {
    descripcion: descripcion.trim() || null,
    honorario_min: values.honorario_min,
    cinco_pct_hon_min: values.cinco_pct_hon_min,
    firma_honorarios: values.firma_honorarios,
    art12_a_min: values.art12_a_min,
    art12_f: values.art12_f,
    firma_impuestos: values.firma_impuestos,
    inscripcion: values.inscripcion,
    protocolo: values.protocolo,
    ii_certificados: values.ii_certificados,
    municipio: values.municipio,
    fotocopias_urgentes: values.fotocopias_urgentes,
    certificaciones_extra: values.certificaciones_extra,
    catastro: values.catastro,
    testimonio: values.testimonio,
    concuerda: values.concuerda,
    informes_notariales: values.informes_notariales,
    extracto: values.extracto,
    fotocopias_simples: values.fotocopias_simples,
    tasas_minimas: values.tasas_minimas,
    salario_secretarias_total: values.salario_secretarias_total,
  };

  const optionalPctKeys: ConfigFieldKey[] = [
    "honorario_pct",
    "certificacion_pct",
    "aporte_pct",
    "cinco_pct_hon_pct",
    "art2_a_pct",
    "art12_a_pct",
    "art12_c_pct",
    "tasa_3pm_pct",
    "sellos_pct",
    "sellos_ajuste_fijo",
    "tasa_75pm_pct",
  ];

  for (const key of optionalPctKeys) {
    payload[key] = values[key];
  }

  return payload;
}

export function ConfiguracionPage() {
  const { data, isLoading, error } = useConfiguracion();
  const { data: history } = useConfiguracionHistory();
  const createMutation = useCreateConfiguracion();

  const [descripcion, setDescripcion] = useState("");
  const [values, setValues] = useState<Record<ConfigFieldKey, string> | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    if (data) {
      setValues(responseToFormState(data));
      setDescripcion(data.descripcion ?? "");
    }
  }, [data]);

  const handleFieldChange = (key: ConfigFieldKey, value: string) => {
    setValues((prev) => (prev ? { ...prev, [key]: value } : prev));
    setSuccessMessage(null);
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!values || !data) {
      return;
    }

    const confirmed = window.confirm(
      "¿Guardar una nueva versión de configuración? Las escrituras existentes conservan la versión con la que fueron creadas.",
    );
    if (!confirmed) {
      return;
    }

    setFormError(null);
    setSuccessMessage(null);

    try {
      const created = await createMutation.mutateAsync(buildPayload(descripcion, values));
      setSuccessMessage(`Configuración guardada como versión ${created.version}.`);
    } catch (err) {
      setFormError(friendlyApiError(err, "No se pudo guardar la configuración."));
    }
  };

  if (isLoading || !values) {
    return <p className="page-muted">Cargando configuración…</p>;
  }

  if (error) {
    return <p className="form-error">No se pudo cargar la configuración.</p>;
  }

  return (
    <div className="config-page">
      <header className="page-header page-header--stacked">
        <div>
          <h1>Configuración</h1>
          <p className="page-muted">
            Versión activa: <strong>v{data?.version}</strong>
            {data?.created_at ? ` · actualizada ${formatDate(data.created_at)}` : null}
            {history ? ` · ${history.length} versiones en historial` : null}
          </p>
        </div>
      </header>

      <form className="config-form" onSubmit={handleSubmit}>
        <section className="detail-card">
          <h2>Notas de la versión</h2>
          <label className="field">
            <span>Descripción (opcional)</span>
            <input
              type="text"
              value={descripcion}
              onChange={(e) => setDescripcion(e.target.value)}
              placeholder="Ej: Ajuste salarios julio 2026"
            />
          </label>
        </section>

        {CONFIG_SECTIONS.map((section) => (
          <section key={section.title} className="detail-card">
            <h2>{section.title}</h2>
            <div className="config-form__grid">
              {section.fields.map((field) => (
                <label key={field.key} className="field">
                  <span>{field.label}</span>
                  <input
                    type="number"
                    step={field.step ?? "0.01"}
                    min="0"
                    value={values[field.key]}
                    onChange={(e) => handleFieldChange(field.key, e.target.value)}
                    required
                  />
                </label>
              ))}
            </div>
          </section>
        ))}

        {formError ? <p className="form-error">{formError}</p> : null}
        {successMessage ? <p className="form-success">{successMessage}</p> : null}

        <div className="form-actions">
          <button type="submit" className="button button--primary" disabled={createMutation.isPending}>
            {createMutation.isPending ? "Guardando…" : "Guardar nueva versión"}
          </button>
        </div>
      </form>
    </div>
  );
}
