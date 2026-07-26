import { describe, expect, it } from "vitest";
import type { EscrituraListItem, EscribanoResponse } from "@/types/api";
import {
  buildEscribanoFilterOptions,
  filterByNombre,
  sortByCreatedAt,
} from "@/utils/escrituraList";

function makeEscritura(
  overrides: Partial<EscrituraListItem> & Pick<EscrituraListItem, "id" | "nombre" | "created_at" | "escribano_id">,
): EscrituraListItem {
  return {
    estado: "abierta",
    escribano_nombre: "Escribano",
    usd_value: "100000",
    costo_total: "1000000",
    total_pagado: "0",
    saldo_pendiente: "1000000",
    pagada_al_100: false,
    sobrepago: false,
    ...overrides,
  };
}

const SAMPLE_ESCRITURAS: EscrituraListItem[] = [
  makeEscritura({
    id: "1",
    nombre: "Compraventa García — Palermo",
    created_at: "2026-07-01T10:00:00Z",
    escribano_id: "esc-a",
  }),
  makeEscritura({
    id: "2",
    nombre: "Hipoteca López — Belgrano",
    created_at: "2026-07-15T14:30:00Z",
    escribano_id: "esc-b",
  }),
  makeEscritura({
    id: "3",
    nombre: "COMPRAVENTA Vera — Monserrat",
    created_at: "2026-06-20T08:00:00Z",
    escribano_id: "esc-a",
  }),
];

describe("filterByNombre", () => {
  it("returns all items when query is empty or whitespace", () => {
    expect(filterByNombre(SAMPLE_ESCRITURAS, "")).toEqual(SAMPLE_ESCRITURAS);
    expect(filterByNombre(SAMPLE_ESCRITURAS, "   ")).toEqual(SAMPLE_ESCRITURAS);
  });

  it("filters by partial match case-insensitively", () => {
    const result = filterByNombre(SAMPLE_ESCRITURAS, "compraventa");
    expect(result.map((item) => item.id)).toEqual(["1", "3"]);
  });

  it("matches substring in the middle of the name", () => {
    const result = filterByNombre(SAMPLE_ESCRITURAS, "belgrano");
    expect(result).toHaveLength(1);
    expect(result[0]?.id).toBe("2");
  });

  it("returns empty array when nothing matches", () => {
    expect(filterByNombre(SAMPLE_ESCRITURAS, "inexistente")).toEqual([]);
  });
});

describe("sortByCreatedAt", () => {
  it("sorts ascending by created_at", () => {
    const sorted = sortByCreatedAt(SAMPLE_ESCRITURAS, "asc");
    expect(sorted.map((item) => item.id)).toEqual(["3", "1", "2"]);
  });

  it("sorts descending by created_at", () => {
    const sorted = sortByCreatedAt(SAMPLE_ESCRITURAS, "desc");
    expect(sorted.map((item) => item.id)).toEqual(["2", "1", "3"]);
  });

  it("does not mutate the input array", () => {
    const copy = [...SAMPLE_ESCRITURAS];
    sortByCreatedAt(SAMPLE_ESCRITURAS, "desc");
    expect(SAMPLE_ESCRITURAS).toEqual(copy);
  });
});

describe("buildEscribanoFilterOptions", () => {
  const escribanos: EscribanoResponse[] = [
    {
      id: "esc-a",
      nombre: "Monica",
      activo: true,
      created_at: "2026-01-01T00:00:00Z",
    },
    {
      id: "esc-b",
      nombre: "Gabriel",
      activo: true,
      created_at: "2026-01-01T00:00:00Z",
    },
    {
      id: "esc-c",
      nombre: "Costanza",
      activo: false,
      created_at: "2026-01-01T00:00:00Z",
    },
    {
      id: "esc-d",
      nombre: "Sin trámites",
      activo: true,
      created_at: "2026-01-01T00:00:00Z",
    },
  ];

  it("includes only escribanos with at least one escritura", () => {
    const options = buildEscribanoFilterOptions(escribanos, SAMPLE_ESCRITURAS);
    expect(options.map((option) => option.id).sort()).toEqual(["esc-a", "esc-b"]);
  });

  it("labels inactive escribanos when they have escrituras", () => {
    const escrituras = [
      makeEscritura({
        id: "10",
        nombre: "Test",
        created_at: "2026-07-01T00:00:00Z",
        escribano_id: "esc-c",
      }),
    ];
    const options = buildEscribanoFilterOptions(escribanos, escrituras);
    expect(options).toEqual([
      { id: "esc-c", label: "Costanza (inactivo)", activo: false },
    ]);
  });

  it("sorts options alphabetically by label", () => {
    const options = buildEscribanoFilterOptions(escribanos, SAMPLE_ESCRITURAS);
    expect(options.map((option) => option.label)).toEqual(["Gabriel", "Monica"]);
  });
});

describe("filterByNombre + sortByCreatedAt", () => {
  it("applies search then sort on the same pipeline", () => {
    const filtered = filterByNombre(SAMPLE_ESCRITURAS, "compraventa");
    const sorted = sortByCreatedAt(filtered, "desc");
    expect(sorted.map((item) => item.id)).toEqual(["1", "3"]);
  });
});
