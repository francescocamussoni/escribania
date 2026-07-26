import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  DEFAULT_SESSION_STATE,
  SESSION_KEY,
  loadEscriturasListSessionState,
  saveEscriturasListSessionState,
} from "@/hooks/useEscriturasListSession";

describe("useEscriturasListSession helpers", () => {
  const storage = new Map<string, string>();

  beforeEach(() => {
    storage.clear();
    vi.stubGlobal("sessionStorage", {
      getItem: (key: string) => storage.get(key) ?? null,
      setItem: (key: string, value: string) => {
        storage.set(key, value);
      },
      removeItem: (key: string) => {
        storage.delete(key);
      },
      clear: () => storage.clear(),
      key: () => null,
      length: 0,
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("returns defaults when sessionStorage is empty", () => {
    expect(loadEscriturasListSessionState()).toEqual(DEFAULT_SESSION_STATE);
  });

  it("persists and loads state from sessionStorage", () => {
    saveEscriturasListSessionState({
      escribanoFilter: "esc-123",
      estadoFilter: "abierta",
      searchQuery: "garcía",
      sortField: "vencimiento",
      sortDirection: "asc",
      createdAtPeriod: { anio: 2026, mes: 3 },
    });

    expect(loadEscriturasListSessionState()).toEqual({
      escribanoFilter: "esc-123",
      estadoFilter: "abierta",
      searchQuery: "garcía",
      sortField: "vencimiento",
      sortDirection: "asc",
      createdAtPeriod: { anio: 2026, mes: 3 },
    });
    expect(storage.get(SESSION_KEY)).toBeTruthy();
  });

  it("merges partial updates with existing state", () => {
    saveEscriturasListSessionState({ searchQuery: "vera" });
    saveEscriturasListSessionState({ estadoFilter: "cerrada" });

    expect(loadEscriturasListSessionState()).toEqual({
      ...DEFAULT_SESSION_STATE,
      searchQuery: "vera",
      estadoFilter: "cerrada",
    });
  });

  it("falls back to defaults on invalid JSON", () => {
    storage.set(SESSION_KEY, "{not-json");
    expect(loadEscriturasListSessionState()).toEqual(DEFAULT_SESSION_STATE);
  });

  it("migrates legacy todas escribano filter to null", () => {
    storage.set(SESSION_KEY, JSON.stringify({ escribanoFilter: "todas" }));
    expect(loadEscriturasListSessionState().escribanoFilter).toBeNull();
  });

  it("rejects invalid createdAtPeriod and falls back to null", () => {
    storage.set(
      SESSION_KEY,
      JSON.stringify({
        createdAtPeriod: { anio: 2026, mes: 13 },
      }),
    );
    expect(loadEscriturasListSessionState().createdAtPeriod).toBeNull();
  });

  it("loads null createdAtPeriod explicitly", () => {
    storage.set(SESSION_KEY, JSON.stringify({ createdAtPeriod: null }));
    expect(loadEscriturasListSessionState().createdAtPeriod).toBeNull();
  });

  it("falls back invalid fields to defaults", () => {
    storage.set(
      SESSION_KEY,
      JSON.stringify({
        escribanoFilter: 42,
        estadoFilter: "invalid",
        searchQuery: null,
        sortField: "invalid",
        sortDirection: "sideways",
      }),
    );

    expect(loadEscriturasListSessionState()).toEqual(DEFAULT_SESSION_STATE);
  });
});
