import { useState } from "react";
import type { FacturaPrincipalResponse } from "@/types/api";
import { formatMoney } from "@/utils/format";

interface FacturaDetalleProps {
  factura: FacturaPrincipalResponse;
}

interface LineItem {
  label: string;
  value: string;
  emphasis?: boolean;
  tone?: "colegio" | "impuestos" | "gastos-admin";
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

function ItemRow({ item }: { item: LineItem }) {
  return (
    <div className={`factura-row${rowToneClass(item.tone)}`}>
      <span>{item.label}</span>
      <span className={item.emphasis ? "factura-row__value--emphasis" : undefined}>
        {formatMoney(item.value)}
      </span>
    </div>
  );
}

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

function FacturaSection({ section }: { section: Section }) {
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
                  {group.items.map((item) => <ItemRow key={item.label} item={item} />)}
                  {group.subtotal ? <SubtotalRow subtotal={group.subtotal} /> : null}
                </div>
              ))
            : (
              <>
                <div className="factura-section__rows">
                  {section.items?.map((item) => <ItemRow key={item.label} item={item} />)}
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

function buildSections(factura: FacturaPrincipalResponse): Section[] {
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
            value: factura.total_impuestos,
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

export function FacturaDetalle({ factura }: FacturaDetalleProps) {
  const sections = buildSections(factura);

  return (
    <div className="factura-detalle factura-detalle--two-col">
      {sections.map((section) => (
        <FacturaSection key={section.title} section={section} />
      ))}
    </div>
  );
}
