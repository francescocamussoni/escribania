import { NavLink } from "react-router-dom";
import { logout } from "@/api/auth";
import { ApiRequestError } from "@/api/client";

const links = [
  { to: "/escrituras", label: "Escrituras" },
  { to: "/gastos-extraordinarios", label: "Gastos Extraordinarios" },
  { to: "/liquidacion", label: "Liquidación" },
  { to: "/salarios", label: "Pago de Salarios" },
  { to: "/libro-entrada", label: "Libro de Entrada" },
  { to: "/libro-salida", label: "Libro de Salida" },
  { to: "/configuracion", label: "Configuración" },
] as const;

interface NavbarProps {
  username?: string;
}

export function Navbar({ username }: NavbarProps) {
  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      if (!(error instanceof ApiRequestError) || error.status !== 401) {
        console.error("Error al cerrar sesión", error);
      }
    } finally {
      window.location.href = "/login";
    }
  };

  return (
    <header className="navbar">
      <div className="navbar__brand">Escribanía Barat</div>
      <nav className="navbar__links" aria-label="Secciones principales">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            className={({ isActive }) =>
              isActive ? "navbar__link navbar__link--active" : "navbar__link"
            }
          >
            {link.label}
          </NavLink>
        ))}
      </nav>
      <div className="navbar__user">
        {username ? <span>{username}</span> : null}
        <button type="button" className="navbar__logout" onClick={handleLogout}>
          Salir
        </button>
      </div>
    </header>
  );
}
