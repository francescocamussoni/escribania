import { describe, expect, it } from "vitest";
import { formatDateOnly } from "@/utils/format";

describe("formatDateOnly", () => {
  it("formats ISO date strings for display", () => {
    const formatted = formatDateOnly("2026-07-10");
    expect(formatted).toContain("2026");
    expect(formatted).toContain("10");
  });
});
