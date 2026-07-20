import { useCallback, useEffect, useState } from "react";
import type { EstadoEscritura } from "@/types/api";
import type { SortDirection } from "@/utils/escrituraList";

export type EstadoFilter = "todas" | EstadoEscritura;
/** `null` means no escribano filter (show all). */
export type EscribanoFilter = string | null;

export interface CreatedAtPeriod {
  anio: number;
  mes: number;
}

/** `null` means no created-at period filter (show all months). */
export type CreatedAtPeriodFilter = CreatedAtPeriod | null;

export interface EscriturasListSessionState {
  escribanoFilter: EscribanoFilter;
  estadoFilter: EstadoFilter;
  searchQuery: string;
  sortDirection: SortDirection;
  createdAtPeriod: CreatedAtPeriodFilter;
}

export const SESSION_KEY = "escrituras-list-state";

export const DEFAULT_SESSION_STATE: EscriturasListSessionState = {
  escribanoFilter: null,
  estadoFilter: "todas",
  searchQuery: "",
  sortDirection: "desc",
  createdAtPeriod: null,
};

function isEstadoFilter(value: unknown): value is EstadoFilter {
  return value === "todas" || value === "abierta" || value === "cerrada";
}

function isSortDirection(value: unknown): value is SortDirection {
  return value === "asc" || value === "desc";
}

function isCreatedAtPeriod(value: unknown): value is CreatedAtPeriod {
  if (!value || typeof value !== "object") {
    return false;
  }
  const period = value as Partial<CreatedAtPeriod>;
  return (
    typeof period.anio === "number" &&
    Number.isInteger(period.anio) &&
    typeof period.mes === "number" &&
    Number.isInteger(period.mes) &&
    period.mes >= 1 &&
    period.mes <= 12
  );
}

function parseCreatedAtPeriod(value: unknown): CreatedAtPeriodFilter {
  if (value === null) {
    return null;
  }
  return isCreatedAtPeriod(value) ? value : DEFAULT_SESSION_STATE.createdAtPeriod;
}

/** Reads list UI state from sessionStorage with safe defaults. */
export function loadEscriturasListSessionState(): EscriturasListSessionState {
  if (typeof sessionStorage === "undefined") {
    return { ...DEFAULT_SESSION_STATE };
  }

  try {
    const raw = sessionStorage.getItem(SESSION_KEY);
    if (!raw) {
      return { ...DEFAULT_SESSION_STATE };
    }

    const parsed = JSON.parse(raw) as Partial<EscriturasListSessionState>;
    const escribanoFilter =
      typeof parsed.escribanoFilter === "string"
        ? parsed.escribanoFilter === "todas"
          ? null
          : parsed.escribanoFilter
        : parsed.escribanoFilter === null
          ? null
          : DEFAULT_SESSION_STATE.escribanoFilter;
    return {
      escribanoFilter,
      estadoFilter: isEstadoFilter(parsed.estadoFilter)
        ? parsed.estadoFilter
        : DEFAULT_SESSION_STATE.estadoFilter,
      searchQuery:
        typeof parsed.searchQuery === "string"
          ? parsed.searchQuery
          : DEFAULT_SESSION_STATE.searchQuery,
      sortDirection: isSortDirection(parsed.sortDirection)
        ? parsed.sortDirection
        : DEFAULT_SESSION_STATE.sortDirection,
      createdAtPeriod: parseCreatedAtPeriod(parsed.createdAtPeriod),
    };
  } catch {
    return { ...DEFAULT_SESSION_STATE };
  }
}

/** Merges partial state into sessionStorage. No-op when storage is unavailable. */
export function saveEscriturasListSessionState(
  partial: Partial<EscriturasListSessionState>,
): void {
  if (typeof sessionStorage === "undefined") {
    return;
  }

  try {
    const current = loadEscriturasListSessionState();
    sessionStorage.setItem(SESSION_KEY, JSON.stringify({ ...current, ...partial }));
  } catch {
    // Private mode or quota exceeded — ignore.
  }
}

export function useEscriturasListSession() {
  const [state, setState] = useState<EscriturasListSessionState>(loadEscriturasListSessionState);

  useEffect(() => {
    saveEscriturasListSessionState(state);
  }, [state]);

  const update = useCallback((partial: Partial<EscriturasListSessionState>) => {
    setState((prev) => ({ ...prev, ...partial }));
  }, []);

  return {
    ...state,
    update,
    setEscribanoFilter: (escribanoFilter: EscribanoFilter) => update({ escribanoFilter }),
    toggleEscribanoFilter: (escribanoId: string) =>
      setState((prev) => ({
        ...prev,
        escribanoFilter: prev.escribanoFilter === escribanoId ? null : escribanoId,
      })),
    setEstadoFilter: (estadoFilter: EstadoFilter) => update({ estadoFilter }),
    setCreatedAtPeriod: (createdAtPeriod: CreatedAtPeriod) => update({ createdAtPeriod }),
    clearCreatedAtPeriod: () => update({ createdAtPeriod: null }),
    setSearchQuery: (searchQuery: string) => update({ searchQuery }),
    setSortDirection: (sortDirection: SortDirection) => update({ sortDirection }),
    toggleSortDirection: () =>
      setState((prev) => ({
        ...prev,
        sortDirection: prev.sortDirection === "desc" ? "asc" : "desc",
      })),
  };
}
