import type { PlazoColegioResponse } from "@/types/api";

interface PlazoColegioBadgeProps {
  plazo: PlazoColegioResponse;
}

function badgeClass(plazo: PlazoColegioResponse): string {
  switch (plazo.estado) {
    case "pagado":
      return "plazo-colegio--pagado";
    case "no_aplica":
      return "plazo-colegio--na";
    case "vencido":
      return "plazo-colegio--vencido";
    case "pendiente":
      if (plazo.urgencia === "verde") return "plazo-colegio--verde";
      if (plazo.urgencia === "amarillo") return "plazo-colegio--amarillo";
      return "plazo-colegio--rojo";
    default:
      return "plazo-colegio--na";
  }
}

function badgeLabel(plazo: PlazoColegioResponse): string {
  switch (plazo.estado) {
    case "pagado":
      return "Pagado";
    case "no_aplica":
      return "No aplica";
    case "vencido":
      return "Vencido";
    case "pendiente":
      if (plazo.dias_restantes === null) {
        return "Pendiente";
      }
      if (plazo.dias_restantes === 0) {
        return "0 días";
      }
      return `${plazo.dias_restantes} días`;
    default:
      return "—";
  }
}

export function PlazoColegioBadge({ plazo }: PlazoColegioBadgeProps) {
  return (
    <span className={`plazo-colegio-badge ${badgeClass(plazo)}`} title="Plazo pago Total impuestos al Colegio">
      {badgeLabel(plazo)}
    </span>
  );
}
