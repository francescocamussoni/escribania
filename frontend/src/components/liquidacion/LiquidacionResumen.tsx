import type { LiquidacionResumen as LiquidacionResumenData } from "@/types/api";
import { formatMoney, labelEscribano } from "@/utils/format";

interface LiquidacionResumenProps {
  data: LiquidacionResumenData;
}

export function LiquidacionResumen({ data }: LiquidacionResumenProps) {
  return (
    <div className="liquidacion-resumen">
      <div className="liquidacion-resumen__total">
        <span className="liquidacion-resumen__label">Total global (honorarios + neto impuestos)</span>
        <span className="liquidacion-resumen__value">{formatMoney(data.total_global)}</span>
      </div>
      <div className="liquidacion-resumen__grid">
        <div className="liquidacion-resumen__card">
          <span className="liquidacion-resumen__label">{labelEscribano("costanza")}</span>
          <span className="liquidacion-resumen__value">{formatMoney(data.total_costanza)}</span>
        </div>
        <div className="liquidacion-resumen__card">
          <span className="liquidacion-resumen__label">{labelEscribano("gabriel")}</span>
          <span className="liquidacion-resumen__value">{formatMoney(data.total_gabriel)}</span>
        </div>
        <div className="liquidacion-resumen__card">
          <span className="liquidacion-resumen__label">{labelEscribano("monica")}</span>
          <span className="liquidacion-resumen__value">{formatMoney(data.total_monica)}</span>
        </div>
      </div>
    </div>
  );
}
