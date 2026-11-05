import { useState } from "react";
import type { FacturaLineaItem, FacturaLineaSeccion, FacturaPrincipalResponse } from "@/types/api";
import { friendlyApiError } from "@/utils/errors";
import { formatMoney } from "@/utils/format";

interface FacturaDetalleProps {
  factura: FacturaPrincipalResponse;
  readOnly?: boolean;
  onLineasChange?: (lineasDeshabilitadas: string[]) => Promise<void>;
}

interface LineItem {
  key?: string;
  label: string;
  value: string;
  montoEfectivo?: string;
  habilitada?: boolean;
  emphasis?: boolean;
  tone?: "colegio" | "impuestos" | "gastos-admin";
  toggleable?: boolean;
}

interface SubtotalLine {
  label: string;
  value: string;
  tone?: "colegio" | "impuestos" | "gastos-admin";
  highlight?: boolean;
}

interface Section {
  title: string;
  items?: LineItem[];
  subtotal?: SubtotalLine;
  subtotals?: SubtotalLine[];
  groups?: Array<{
    items: LineItem[];
    subtotal?: SubtotalLine;
  }>;
  spanFullWidth?: boolean;
}

const COLEGIO_KEYS = new Set(["aporte_12pct", "cinco_pct_hon", "firma_honorarios"]);
const IMPUESTO_KEYS = new Set(["tasa_3pm", "sellos", "tasa_75pm", "firma_impuestos"]);

function rowToneClass(tone?: LineItem["tone"]): string {
  switch (tone) {
    case "colegio":
      return " factura-row--colegio";
    case "impuestos":
      return " factura-row--impuestos";
    case "gastos-admin":
      return " factura-row--gastos-admin";
    default:
      return "";
  }
}

function toneForLineaKey(key: string): LineItem["tone"] | undefined {
  if (COLEGIO_KEYS.has(key)) {
    return "colegio";
  }
  if (IMPUESTO_KEYS.has(key)) {
    return "impuestos";
  }
  const gastosAdminKeys = new Set([
    "inscripcion",
    "protocolo",
    "ii_certificados",
    "municipio",
    "fotocopias_urgentes",
    "certificaciones_extra",
    "catastro",
    "testimonio",
    "concuerda",
    "informes_notariales",
    "extracto",
    "fotocopias_simples",
    "tasas_minimas",
  ]);
  if (gastosAdminKeys.has(key)) {
    return "gastos-admin";
  }
  return undefined;
}

function sumMontoEfectivo(lineas: FacturaLineaItem[], seccion: FacturaLineaSeccion): string {
  const total = lineas
    .filter((linea) => linea.seccion === seccion)
    .reduce((acc, linea) => acc + Number(linea.monto_efectivo), 0);
  return total.toFixed(2);
}

function effectiveTotalFactura(factura: FacturaPrincipalResponse): string {
  if (!factura.lineas?.length) {
    return factura.total_factura;
  }
  const descuento = factura.lineas
    .filter((linea) => !linea.habilitada)
    .reduce((acc, linea) => acc + Number(linea.monto), 0);
  return (Number(factura.total_factura) - descuento).toFixed(2);
}

function lineaToItem(linea: FacturaLineaItem): LineItem {
  return {
    key: linea.key,
    label: linea.label,
    value: linea.monto,
    montoEfectivo: linea.monto_efectivo,
    habilitada: linea.habilitada,
    tone: toneForLineaKey(linea.key),
    toggleable: true,
  };
}

function buildSectionsFromLineas(factura: FacturaPrincipalResponse): Section[] {
  const lineas = factura.lineas ?? [];
  const byKey = Object.fromEntries(lineas.map((linea) => [linea.key, linea]));

  const honorariosItems: LineItem[] = [];
  const honorarioPrincipal = byKey.honorario_principal;
  const certificacion = byKey.certificacion;
  if (honorarioPrincipal) {
    honorariosItems.push(lineaToItem(honorarioPrincipal));
  }
  if (certificacion) {
    honorariosItems.push(lineaToItem(certificacion));
  }
  honorariosItems.push({
    label: "Suma hon. + cert.",
    value: factura.suma_hon_cert,
    emphasis: true,
    toggleable: false,
  });
  for (const key of ["aporte_12pct", "cinco_pct_hon", "firma_honorarios"] as const) {
    const linea = byKey[key];
    if (linea) {
      honorariosItems.push(lineaToItem(linea));
    }
  }

  const honorariosVariosItems = lineas
    .filter((linea) => linea.seccion === "honorarios_varios")
    .map(lineaToItem);

  const impuestosItems = lineas
    .filter((linea) => linea.seccion === "impuestos")
    .map(lineaToItem);

  const gastosAdminItems = lineas
    .filter((linea) => linea.seccion === "gastos_admin")
    .map(lineaToItem);

  const totalImpuestosEfectivo = factura.total_impuestos_efectivo ?? factura.total_impuestos;
  const impuestosSubtotalLabel =
    totalImpuestosEfectivo !== factura.total_impuestos
      ? "Total impuestos (cobrados)"
      : "Total impuestos";

  return [
    {
      title: "Bases de cálculo",
      spanFullWidth: true,
      items: [
        { label: "Monto base MEP", value: factura.monto_base_mep, toggleable: false },
        { label: "Precio base Valor", value: factura.precio_base_nacion, toggleable: false },
      ],
    },
    {
      title: "Honorarios",
      items: honorariosItems,
      subtotal: {
        label: "Subtotal honorarios",
        value: lineas.length ? sumMontoEfectivo(lineas, "honorarios") : factura.subtotal_honorarios,
        tone: "colegio",
      },
    },
    {
      title: "Honorarios varios",
      items: honorariosVariosItems,
      subtotal: {
        label: "Total honorarios varios",
        value: lineas.length
          ? sumMontoEfectivo(lineas, "honorarios_varios")
          : factura.total_leyes_notariales,
      },
    },
    {
      title: "Corresponde",
      spanFullWidth: true,
      groups: [
        {
          items: impuestosItems,
          subtotal: {
            label: impuestosSubtotalLabel,
            value: totalImpuestosEfectivo,
            tone: "impuestos",
          },
        },
        {
          items: gastosAdminItems,
          subtotal: {
            label: "Total gastos admin.",
            value: lineas.length ? sumMontoEfectivo(lineas, "gastos_admin") : factura.total_gastos_admin,
            tone: "gastos-admin",
          },
        },
      ],
    },
    {
      title: "Totales",
      spanFullWidth: true,
      items: [
        { label: "Dif Honorarios", value: factura.dif_honorarios, toggleable: false },
        { label: "Total parcial", value: factura.total_parcial, toggleable: false },
        { label: "Total", value: factura.total_sin_iva, toggleable: false },
        { label: "IVA", value: factura.iva, toggleable: false },
      ],
      subtotal: {
        label: "Total + IVA",
        value: effectiveTotalFactura(factura),
        highlight: true,
      },
    },
  ];
}

function buildSectionsLegacy(factura: FacturaPrincipalResponse): Section[] {
  return [
    {
      title: "Bases de cálculo",
      spanFullWidth: true,
      items: [
        { label: "Monto base MEP", value: factura.monto_base_mep },
        { label: "Precio base Valor", value: factura.precio_base_nacion },
      ],
    },
    {
      title: "Honorarios",
      items: [
        { label: "Honorario principal", value: factura.honorario_principal },
        { label: "Certificación", value: factura.certificacion },
        { label: "Suma hon. + cert.", value: factura.suma_hon_cert, emphasis: true },
        { label: "Aporte 12%", value: factura.aporte_12pct, tone: "colegio" },
        { label: "5% honorarios", value: factura.cinco_pct_hon, tone: "colegio" },
        { label: "Firma honorarios", value: factura.firma_honorarios, tone: "colegio" },
      ],
      subtotal: {
        label: "Subtotal honorarios",
        value: factura.subtotal_honorarios,
        tone: "colegio",
      },
    },
    {
      title: "Honorarios varios",
      items: [
        { label: "Art. 2 a)", value: factura.art2_a },
        { label: "Art. 12 a)", value: factura.art12_a },
        { label: "Art. 12 c)", value: factura.art12_c },
        { label: "Art. 12 f)", value: factura.art12_f },
      ],
      subtotal: {
        label: "Total honorarios varios",
        value: factura.total_leyes_notariales,
      },
    },
    {
      title: "Corresponde",
      spanFullWidth: true,
      groups: [
        {
          items: [
            { label: "Tasa 3‰", value: factura.tasa_3pm, tone: "impuestos" },
            { label: "Sellos", value: factura.sellos, tone: "impuestos" },
            { label: "Tasa 7,5‰", value: factura.tasa_75pm, tone: "impuestos" },
            { label: "Firma impuestos", value: factura.firma_impuestos, tone: "impuestos" },
          ],
          subtotal: {
            label: "Total impuestos",
            value: factura.total_impuestos_efectivo ?? factura.total_impuestos,
            tone: "impuestos",
          },
        },
        {
          items: [
            { label: "Inscripción", value: factura.inscripcion, tone: "gastos-admin" },
            { label: "Protocolo", value: factura.protocolo, tone: "gastos-admin" },
            { label: "II Certificados", value: factura.ii_certificados, tone: "gastos-admin" },
            { label: "Municipio", value: factura.municipio, tone: "gastos-admin" },
            { label: "Fotocopias urgentes", value: factura.fotocopias_urgentes, tone: "gastos-admin" },
            {
              label: "Certificaciones extra",
              value: factura.certificaciones_extra,
              tone: "gastos-admin",
            },
            { label: "Catastro", value: factura.catastro, tone: "gastos-admin" },
            { label: "Testimonio", value: factura.testimonio, tone: "gastos-admin" },
            { label: "Concuerda", value: factura.concuerda, tone: "gastos-admin" },
            {
              label: "Informes notariales",
              value: factura.informes_notariales,
              tone: "gastos-admin",
            },
            { label: "Extracto", value: factura.extracto, tone: "gastos-admin" },
            { label: "Fotocopias simples", value: factura.fotocopias_simples, tone: "gastos-admin" },
            { label: "Tasas mínimas", value: factura.tasas_minimas, tone: "gastos-admin" },
          ],
          subtotal: {
            label: "Total gastos admin.",
            value: factura.total_gastos_admin,
            tone: "gastos-admin",
          },
        },
      ],
    },
    {
      title: "Totales",
      spanFullWidth: true,
      items: [
        { label: "Dif Honorarios", value: factura.dif_honorarios },
        { label: "Total parcial", value: factura.total_parcial },
        { label: "Total", value: factura.total_sin_iva },
        { label: "IVA", value: factura.iva },
      ],
      subtotal: {
        label: "Total + IVA",
        value: factura.total_factura,
        highlight: true,
      },
    },
  ];
}

function buildSections(factura: FacturaPrincipalResponse): Section[] {
  if (factura.lineas && factura.lineas.length > 0) {
    return buildSectionsFromLineas(factura);
  }
  return buildSectionsLegacy(factura);
}

function SubtotalRow({ subtotal }: { subtotal: SubtotalLine }) {
  return (
    <div
      className={`factura-row factura-row--subtotal${rowToneClass(subtotal.tone)}${
        subtotal.highlight ? " factura-row--total-final" : ""
      }`}
    >
      <span>{subtotal.label}</span>
      <span>{formatMoney(subtotal.value)}</span>
    </div>
  );
}

interface ItemRowProps {
  item: LineItem;
  readOnly: boolean;
  saving: boolean;
  onToggle?: (key: string, currentlyEnabled: boolean) => void;
}

function ItemRow({ item, readOnly, saving, onToggle }: ItemRowProps) {
  const isDisabled = item.toggleable && item.habilitada === false;
  const displayValue = isDisabled ? (item.montoEfectivo ?? "0") : item.value;

  return (
    <div
      className={`factura-row${rowToneClass(item.tone)}${isDisabled ? " factura-row--disabled" : ""}`}
    >
      {item.toggleable && item.key ? (
        <label className="factura-row__label">
          <input
            type="checkbox"
            checked={item.habilitada ?? true}
            disabled={readOnly || saving}
            onChange={() => onToggle?.(item.key!, item.habilitada ?? true)}
            aria-label={`${item.habilitada ? "Deshabilitar" : "Habilitar"} ${item.label}`}
          />
          <span>{item.label}</span>
        </label>
      ) : (
        <span>{item.label}</span>
      )}
      <span className={item.emphasis ? "factura-row__value--emphasis" : undefined}>
        {formatMoney(displayValue)}
      </span>
    </div>
  );
}

interface FacturaSectionProps {
  section: Section;
  readOnly: boolean;
  saving: boolean;
  onToggle?: (key: string, currentlyEnabled: boolean) => void;
}

function FacturaSection({ section, readOnly, saving, onToggle }: FacturaSectionProps) {
  const [expanded, setExpanded] = useState(true);

  return (
    <section
      className={`factura-section${section.spanFullWidth ? " factura-section--full-width" : ""}${
        expanded ? "" : " factura-section--collapsed"
      }`}
    >
      <button
        type="button"
        className="factura-section__header"
        onClick={() => setExpanded((prev) => !prev)}
        aria-expanded={expanded}
      >
        <h3 className="factura-section__title">{section.title}</h3>
        <span className="factura-section__chevron" aria-hidden="true">
          {expanded ? "▾" : "▸"}
        </span>
      </button>
      {expanded ? (
        <div className="factura-section__body">
          {section.groups
            ? section.groups.map((group, index) => (
                <div key={index} className="factura-section__rows">
                  {group.items.map((item) => (
                    <ItemRow
                      key={item.key ?? item.label}
                      item={item}
                      readOnly={readOnly}
                      saving={saving}
                      onToggle={onToggle}
                    />
                  ))}
                  {group.subtotal ? <SubtotalRow subtotal={group.subtotal} /> : null}
                </div>
              ))
            : (
              <>
                <div className="factura-section__rows">
                  {section.items?.map((item) => (
                    <ItemRow
                      key={item.key ?? item.label}
                      item={item}
                      readOnly={readOnly}
                      saving={saving}
                      onToggle={onToggle}
                    />
                  ))}
                </div>
                {section.subtotals?.map((subtotal) => (
                  <SubtotalRow key={subtotal.label} subtotal={subtotal} />
                ))}
                {section.subtotal ? <SubtotalRow subtotal={section.subtotal} /> : null}
              </>
            )}
        </div>
      ) : null}
    </section>
  );
}

export function FacturaDetalle({ factura, readOnly = false, onLineasChange }: FacturaDetalleProps) {
  const [saving, setSaving] = useState(false);
  const [toggleError, setToggleError] = useState<string | null>(null);
  const sections = buildSections(factura);

  const handleToggle = async (key: string, currentlyEnabled: boolean) => {
    if (!onLineasChange || readOnly) {
      return;
    }

    const lineas = factura.lineas ?? [];
    const enabledCount = lineas.filter((linea) => linea.habilitada).length;
    if (currentlyEnabled && enabledCount <= 1) {
      setToggleError("Debe quedar al menos una línea habilitada.");
      return;
    }

    const disabled = new Set(factura.lineas_deshabilitadas ?? []);
    if (currentlyEnabled) {
      disabled.add(key);
    } else {
      disabled.delete(key);
    }

    setToggleError(null);
    setSaving(true);
    try {
      await onLineasChange([...disabled]);
    } catch (err) {
      setToggleError(friendlyApiError(err, "No se pudo actualizar las líneas de la factura."));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="factura-detalle factura-detalle--two-col">
      {toggleError ? <p className="form-error">{toggleError}</p> : null}
      {saving ? <p className="page-muted">Guardando líneas…</p> : null}
      {sections.map((section) => (
        <FacturaSection
          key={section.title}
          section={section}
          readOnly={readOnly}
          saving={saving}
          onToggle={onLineasChange ? handleToggle : undefined}
        />
      ))}
    </div>
  );
}
