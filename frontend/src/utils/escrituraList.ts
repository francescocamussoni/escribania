import type { EscrituraListItem, EscribanoResponse } from "@/types/api";

/** Sort order for escritura list by creation timestamp. */
export type SortDirection = "asc" | "desc";

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
