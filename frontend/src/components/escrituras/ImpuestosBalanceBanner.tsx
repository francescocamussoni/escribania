import type { BalanceImpuestosResponse } from "@/types/api";
import { formatMoney } from "@/utils/format";

interface ImpuestosBalanceBannerProps {
  balance: BalanceImpuestosResponse | null | undefined;
}

function balanceClass(balance: string): string | undefined {
  const value = Number(balance);
  if (Number.isNaN(value) || value === 0) {
    return undefined;
  }
  return value > 0 ? "impuestos-balance__value--positive" : "impuestos-balance__value--negative";
}

export function ImpuestosBalanceBanner({ balance }: ImpuestosBalanceBannerProps) {
  if (!balance) {
    return null;
  }

  return (
    <div className="impuestos-balance">
      <h3 className="impuestos-balance__title">Balance de impuestos</h3>
      <dl className="impuestos-balance__grid">
        <div>
          <dt>Total cobrado (cliente)</dt>
          <dd>{formatMoney(balance.total_cliente)}</dd>
        </div>
        <div>
          <dt>Total pagado (escribanía)</dt>
          <dd>{formatMoney(balance.total_escribania)}</dd>
        </div>
        <div>
          <dt>Diferencia</dt>
          <dd className={balanceClass(balance.balance)}>{formatMoney(balance.balance)}</dd>
        </div>
      </dl>
      {!balance.puede_cerrar && balance.impuestos_pendientes.length > 0 ? (
        <ul className="impuestos-balance__pendientes">
          {balance.impuestos_pendientes.map((item) => (
            <li key={item.impuesto_id}>
              {item.tipo}:{" "}
              {item.falta_cliente && item.falta_escribania
                ? "falta pago cliente y escribanía"
                : item.falta_cliente
                  ? "falta pago del cliente"
                  : "falta pago de la escribanía"}
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
