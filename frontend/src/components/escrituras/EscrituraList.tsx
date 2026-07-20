import { Link } from "react-router-dom";
import type { EscrituraListItem } from "@/types/api";
import { useEscribanos } from "@/hooks/useEscribanos";
import { displayEscribanoNombre, formatMoney, labelEstado } from "@/utils/format";

interface EscrituraListProps {
  items: EscrituraListItem[];
  loading?: boolean;
}

export function EscrituraList({ items, loading }: EscrituraListProps) {
  const { data: escribanos } = useEscribanos(true);

  if (loading) {
    return <p className="page-muted">Cargando escrituras…</p>;
  }

  if (items.length === 0) {
    return <p className="page-muted">No hay escrituras para mostrar.</p>;
  }

  return (
    <div className="escritura-list">
      <div className="escritura-list__header">
        <span>Nombre</span>
        <span>Escribano</span>
        <span>Estado</span>
        <span className="escritura-list__amount">Total factura</span>
      </div>
      {items.map((item) => (
        <Link key={item.id} to={`/escrituras/${item.id}`} className="escritura-list__row">
          <span className="escritura-list__nombre">{item.nombre}</span>
          <span>
            {displayEscribanoNombre(item.escribano_id, item.escribano_nombre, escribanos)}
          </span>
          <span>
            <span className={`badge badge--${item.estado}`}>{labelEstado(item.estado)}</span>
          </span>
          <span className="escritura-list__amount">{formatMoney(item.total_factura)}</span>
        </Link>
      ))}
    </div>
  );
}
