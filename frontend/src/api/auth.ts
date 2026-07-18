import { apiFetch } from "@/api/client";
import type { LoginInput, UserResponse } from "@/types/api";

export function login(payload: LoginInput): Promise<{ status: string }> {
  return apiFetch("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function logout(): Promise<void> {
  return apiFetch("/auth/logout", { method: "POST" });
}

export function getMe(): Promise<UserResponse> {
  return apiFetch("/auth/me");
}
