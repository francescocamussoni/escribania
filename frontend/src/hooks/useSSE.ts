import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import type { SseEventType } from "@/types/api";
import { API_BASE } from "@/api/client";

const RECONNECT_MS = 3000;

function invalidateForEvent(
  queryClient: ReturnType<typeof useQueryClient>,
  eventType: SseEventType,
  data: Record<string, string>,
): void {
  const escrituraRelated =
    eventType.startsWith("escritura.") ||
    eventType === "gasto.created" ||
    eventType === "pago_cliente.created" ||
    eventType === "pago_colegio.created";

  if (escrituraRelated) {
    void queryClient.invalidateQueries({ queryKey: ["escrituras"] });
    const escrituraId = data.escritura_id;
    if (escrituraId) {
      void queryClient.invalidateQueries({ queryKey: ["escritura", escrituraId] });
    }
  }
  if (
    eventType === "liquidacion.updated" ||
    eventType.startsWith("escritura.") ||
    eventType === "gasto.created" ||
    eventType === "pago_cliente.created"
  ) {
    void queryClient.invalidateQueries({ queryKey: ["liquidacion"] });
    void queryClient.invalidateQueries({ queryKey: ["salarios"] });
  }
  if (
    eventType === "libros_updated" ||
    eventType.startsWith("escritura.") ||
    eventType === "gasto.created" ||
    eventType === "pago_cliente.created" ||
    eventType === "pago_colegio.created"
  ) {
    void queryClient.invalidateQueries({ queryKey: ["libros"] });
  }
}

export function useSSE(enabled = true): void {
  const queryClient = useQueryClient();

  useEffect(() => {
    if (!enabled) {
      return;
    }

    let source: EventSource | null = null;
    let reconnectTimer: number | null = null;
    let closed = false;

    const connect = () => {
      source = new EventSource(`${API_BASE}/events`, { withCredentials: true });

      const handleEvent = (event: MessageEvent<string>) => {
        const eventType = event.type as SseEventType;
        let data: Record<string, string> = {};
        try {
          data = JSON.parse(event.data) as Record<string, string>;
        } catch {
          data = {};
        }
        invalidateForEvent(queryClient, eventType, data);
      };

      const eventTypes: SseEventType[] = [
        "escritura.created",
        "escritura.updated",
        "escritura.closed",
        "gasto.created",
        "pago_cliente.created",
        "pago_colegio.created",
        "liquidacion.updated",
        "libros_updated",
      ];

      for (const type of eventTypes) {
        source.addEventListener(type, handleEvent as EventListener);
      }

      source.onerror = () => {
        source?.close();
        if (!closed) {
          reconnectTimer = window.setTimeout(connect, RECONNECT_MS);
        }
      };
    };

    connect();

    return () => {
      closed = true;
      if (reconnectTimer !== null) {
        window.clearTimeout(reconnectTimer);
      }
      source?.close();
    };
  }, [enabled, queryClient]);
}
