import type { ApiError } from "@/types/api";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

export class ApiRequestError extends Error {
  readonly status: number;
  readonly body: ApiError | null;

  constructor(message: string, status: number, body: ApiError | null) {
    super(message);
    this.name = "ApiRequestError";
    this.status = status;
    this.body = body;
  }
}

async function parseError(response: Response): Promise<ApiError | null> {
  try {
    return (await response.json()) as ApiError;
  } catch {
    return null;
  }
}

export async function apiFetch<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
    credentials: "include",
  });

  if (!response.ok) {
    const body = await parseError(response);
    const message = body?.detail ?? `Error HTTP ${response.status}`;
    throw new ApiRequestError(message, response.status, body);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export { API_BASE };
