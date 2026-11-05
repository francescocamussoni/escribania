import type { EscrituraListItem, EscribanoResponse, PlazoColegioEstado } from "@/types/api";

/** Sort order for escritura list columns. */
export type SortDirection = "asc" | "desc";

/** Client-side sort field for the escrituras list. */
export type SortField = "created_at" | "vencimiento";

export interface EscritanoFilterOption {
  id: string;
  label: string;
  activo: boolean;
}

/**
 * Filters escrituras by partial, case-insensitive match on nombre.
 * Empty or whitespace-only query returns all items unchanged.
 */
export function filterByNombre(
  items: EscrituraListItem[],
  query: string,
): EscrituraListItem[] {
  const trimmed = query.trim();
  if (!trimmed) {
    return items;
  }
  const lower = trimmed.toLowerCase();
  return items.filter((item) => item.nombre.toLowerCase().includes(lower));
}

/**
 * Returns a new array sorted by created_at.
 * Does not mutate the input array.
 */
export function sortByCreatedAt(
  items: EscrituraListItem[],
  direction: SortDirection,
): EscrituraListItem[] {
  const sorted = [...items].sort((a, b) => {
    const timeA = new Date(a.created_at).getTime();
    const timeB = new Date(b.created_at).getTime();
    if (!Number.isNaN(timeA) && !Number.isNaN(timeB) && timeA !== timeB) {
      return timeA - timeB;
    }
    return a.created_at.localeCompare(b.created_at);
  });
  return direction === "desc" ? sorted.reverse() : sorted;
}

function isTerminalPlazo(estado: PlazoColegioEstado): boolean {
  return estado === "pagado" || estado === "no_aplica";
}

/**
 * Returns a new array sorted by plazo_colegio.fecha_vencimiento.
 * Rows with estado pagado or no_aplica (or without fecha_vencimiento) stay at the end.
 * Stable secondary order by id within each group.
 */
export function sortByVencimiento(
  items: EscrituraListItem[],
  direction: SortDirection,
): EscrituraListItem[] {
  const active: EscrituraListItem[] = [];
  const terminal: EscrituraListItem[] = [];

  for (const item of items) {
    if (!item.plazo_colegio) {
      terminal.push(item);
      continue;
    }
    const { estado, fecha_vencimiento } = item.plazo_colegio;
    if (isTerminalPlazo(estado) || !fecha_vencimiento) {
      terminal.push(item);
    } else {
      active.push(item);
    }
  }

  const compareByVencimiento = (a: EscrituraListItem, b: EscrituraListItem) => {
    const fechaA = a.plazo_colegio?.fecha_vencimiento ?? "";
    const fechaB = b.plazo_colegio?.fecha_vencimiento ?? "";
    const timeA = new Date(fechaA).getTime();
    const timeB = new Date(fechaB).getTime();
    if (!Number.isNaN(timeA) && !Number.isNaN(timeB) && timeA !== timeB) {
      return timeA - timeB;
    }
    return fechaA.localeCompare(fechaB);
  };

  active.sort(compareByVencimiento);
  if (direction === "desc") {
    active.reverse();
  }

  terminal.sort((a, b) => a.id.localeCompare(b.id));

  return [...active, ...terminal];
}

/**
 * Builds escribano pill options for escrituras that have at least one trámite.
 * Includes inactive escribanos when they have associated escrituras.
 */
export function buildEscribanoFilterOptions(
  escribanos: EscribanoResponse[],
  escrituras: EscrituraListItem[],
): EscritanoFilterOption[] {
  const idsWithEscrituras = new Set(escrituras.map((item) => item.escribano_id));

  return escribanos
    .filter((escribano) => idsWithEscrituras.has(escribano.id))
    .map((escribano) => ({
      id: escribano.id,
      label: escribano.activo ? escribano.nombre : `${escribano.nombre} (inactivo)`,
      activo: escribano.activo,
    }))
    .sort((a, b) => a.label.localeCompare(b.label, "es"));
}

/** Escrituras abiertas con pendiente al Colegio > 0 pueden incluirse en pago masivo. */
export function isSelectableForBulkPagoColegio(item: EscrituraListItem): boolean {
  if (item.estado === "cerrada") {
    return false;
  }
  const pendiente = Number(item.plazo_colegio?.monto_pendiente ?? "0");
  return !Number.isNaN(pendiente) && pendiente > 0;
}
