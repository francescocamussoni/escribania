import type { FacturaPrincipalResponse } from "@/types/api";
import { formatMoney } from "@/utils/format";

interface FacturaDetalleProps {
  factura: FacturaPrincipalResponse;
}

interface LineItem {
  label: string;
  value: string;
  emphasis?: boolean;
}

interface Section {
  title: string;
  items: LineItem[];
  subtotal?: { label: string; value: string };
}

function FacturaSection({ section }: { section: Section }) {
  return (
    <section className="factura-section">
      <h3 className="factura-section__title">{section.title}</h3>
      <div className="factura-section__rows">
        {section.items.map((item) => (
          <div key={item.label} className="factura-row">
            <span>{item.label}</span>
            <span className={item.emphasis ? "factura-row__value--emphasis" : undefined}>
              {formatMoney(item.value)}
            </span>
          </div>
        ))}
      </div>
      {section.subtotal ? (
        <div className="factura-row factura-row--subtotal">
          <span>{section.subtotal.label}</span>
          <span>{formatMoney(section.subtotal.value)}</span>
        </div>
      ) : null}
    </section>
  );
}

function buildSections(factura: FacturaPrincipalResponse): Section[] {
  return [
    {
      title: "Bases de cálculo",
      items: [
        { label: "Monto base MEP", value: factura.monto_base_mep },
        { label: "Precio base Nación", value: factura.precio_base_nacion },
      ],
    },
    {
      title: "Honorarios profesionales",
      items: [
        { label: "Honorario principal", value: factura.honorario_principal },
        { label: "Certificación", value: factura.certificacion },
        { label: "Suma hon. + cert.", value: factura.suma_hon_cert, emphasis: true },
        { label: "Aporte 12%", value: factura.aporte_12pct },
        { label: "5% honorarios", value: factura.cinco_pct_hon },
        { label: "Firma honorarios", value: factura.firma_honorarios },
      ],
      subtotal: { label: "Subtotal honorarios", value: factura.subtotal_honorarios },
    },
    {
      title: "Leyes notariales",
      items: [
        { label: "Art. 2 a)", value: factura.art2_a },
        { label: "Art. 12 a)", value: factura.art12_a },
        { label: "Art. 12 c)", value: factura.art12_c },
        { label: "Art. 12 f)", value: factura.art12_f },
      ],
      subtotal: { label: "Total leyes notariales", value: factura.total_leyes_notariales },
    },
    {
      title: "Impuestos y sellos",
      items: [
        { label: "Tasa 3‰", value: factura.tasa_3pm },
        { label: "Sellos", value: factura.sellos },
        { label: "Tasa 7,5‰", value: factura.tasa_75pm },
        { label: "Firma impuestos", value: factura.firma_impuestos },
      ],
      subtotal: { label: "Total impuestos", value: factura.total_impuestos },
    },
    {
      title: "Gastos administrativos fijos",
      items: [
        { label: "Inscripción", value: factura.inscripcion },
        { label: "Protocolo", value: factura.protocolo },
        { label: "II Certificados", value: factura.ii_certificados },
        { label: "Municipio", value: factura.municipio },
        { label: "Fotocopias urgentes", value: factura.fotocopias_urgentes },
        { label: "Certificaciones extra", value: factura.certificaciones_extra },
        { label: "Catastro", value: factura.catastro },
        { label: "Testimonio", value: factura.testimonio },
        { label: "Concuerda", value: factura.concuerda },
        { label: "Informes notariales", value: factura.informes_notariales },
        { label: "Extracto", value: factura.extracto },
        { label: "Fotocopias simples", value: factura.fotocopias_simples },
        { label: "Tasas mínimas", value: factura.tasas_minimas },
      ],
      subtotal: { label: "Total gastos admin.", value: factura.total_gastos_admin },
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
      <div className="factura-total">
        <span>Total factura</span>
        <span>{formatMoney(factura.total_factura)}</span>
      </div>
    </div>
  );
}
