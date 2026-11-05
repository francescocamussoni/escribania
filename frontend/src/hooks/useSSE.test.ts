import { describe, expect, it, vi } from "vitest";
import { invalidateForEvent } from "@/hooks/useSSE";

describe("invalidateForEvent", () => {
  it("invalidates escrituras, detail and libros on escritura.updated", () => {
    const invalidateQueries = vi.fn();
    const queryClient = { invalidateQueries } as never;

    invalidateForEvent(queryClient, "escritura.updated", {
      escritura_id: "esc-1",
    });

    expect(invalidateQueries).toHaveBeenCalledWith({ queryKey: ["escrituras"] });
    expect(invalidateQueries).toHaveBeenCalledWith({ queryKey: ["escritura", "esc-1"] });
    expect(invalidateQueries).toHaveBeenCalledWith({ queryKey: ["impuestos", "esc-1"] });
    expect(invalidateQueries).toHaveBeenCalledWith({ queryKey: ["libros"] });
    expect(invalidateQueries).toHaveBeenCalledWith({ queryKey: ["liquidacion"] });
  });
});
