import { describe, expect, it } from "vitest";
import { formatCobroPercent, formatDateOnly } from "@/utils/format";

describe("formatCobroPercent", () => {
  it("returns rounded percent of total paid over cost", () => {
    expect(formatCobroPercent("500000", "1000000")).toBe(50);
    expect(formatCobroPercent("1000000", "1000000")).toBe(100);
    expect(formatCobroPercent("0", "1000000")).toBe(0);
  });

  it("returns null when costo total is zero or invalid", () => {
    expect(formatCobroPercent("100", "0")).toBeNull();
    expect(formatCobroPercent("x", "100")).toBeNull();
  });
});

describe("formatDateOnly", () => {
  it("formats ISO date strings for display", () => {
    const formatted = formatDateOnly("2026-07-10");
    expect(formatted).toContain("2026");
    expect(formatted).toContain("10");
  });
});
