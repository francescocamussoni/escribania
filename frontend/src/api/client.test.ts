import { describe, expect, it } from "vitest";
import { API_BASE } from "@/api/client";

describe("api client", () => {
  it("uses /api/v1 by default for same-origin proxy", () => {
    expect(API_BASE).toBe("/api/v1");
  });
});
