import { useEffect, useState } from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { getMe } from "@/api/auth";
import { ApiRequestError } from "@/api/client";
import { Navbar } from "@/components/layout/Navbar";
import { useSSE } from "@/hooks/useSSE";
import type { UserResponse } from "@/types/api";

export function Layout() {
  const location = useLocation();
  const [user, setUser] = useState<UserResponse | null>(null);
  const [checking, setChecking] = useState(true);
  const [authenticated, setAuthenticated] = useState(false);

  useSSE(authenticated);

  useEffect(() => {
    let active = true;

    const verify = async () => {
      try {
        const me = await getMe();
        if (active) {
          setUser(me);
          setAuthenticated(true);
        }
      } catch (error) {
        if (active) {
          setUser(null);
          setAuthenticated(false);
          if (!(error instanceof ApiRequestError) || error.status !== 401) {
            console.error("Error verificando sesión", error);
          }
        }
      } finally {
        if (active) {
          setChecking(false);
        }
      }
    };

    void verify();

    return () => {
      active = false;
    };
  }, [location.pathname]);

  if (checking) {
    return (
      <div className="app-shell app-shell--loading">
        <p>Cargando…</p>
      </div>
    );
  }

  if (!authenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  return (
    <div className="app-shell">
      <Navbar username={user?.nombre_display ?? user?.username} />
      <main className="app-main">
        <Outlet />
      </main>
    </div>
  );
}
