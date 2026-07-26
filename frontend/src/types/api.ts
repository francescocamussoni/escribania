// Types derived from specs/001-plataforma-contaduria/contracts/openapi.yaml

export type EstadoEscritura = "abierta" | "cerrada";
export type Escribano = "costanza" | "gabriel" | "monica";
export type DireccionGasto = "entrada" | "salida";

export type SseEventType =
  | "escritura.created"
  | "escritura.updated"
  | "escritura.closed"
  | "gasto.created"
  | "pago_cliente.created"
  | "pago_colegio.created"
  | "impuesto.pago_cliente.changed"
  | "impuesto.pago_escribania.changed"
  | "impuesto.updated"
  | "impuesto.deleted"
  | "gasto_extraordinario.created"
  | "gasto_extraordinario.updated"
  | "gasto_extraordinario.deleted"
  | "liquidacion.updated"
  | "libros_updated"
  | "escribano.updated";

export interface LoginInput {
  username: string;
  password: string;
}

export interface UserResponse {
  id: string;
  username: string;
  nombre_display: string | null;
}

export interface EscrituraInput {
  nombre: string;
  escribano_id: string;
  usd_value: string;
  dolar_mep: string;
  dolar_nacion: string;
}

export interface EscrituraUpdate {
  nombre?: string;
  escribano_id?: string;
  usd_value?: string;
  dolar_mep?: string;
  dolar_nacion?: string;
}

export interface FacturaPrincipalResponse {
  id: string;
  monto_base_mep: string;
  precio_base_nacion: string;
  honorario_principal: string;
  certificacion: string;
  suma_hon_cert: string;
  aporte_12pct: string;
  cinco_pct_hon: string;
  firma_honorarios: string;
  subtotal_honorarios: string;
  art2_a: string;
  art12_a: string;
  art12_c: string;
  art12_f: string;
  total_leyes_notariales: string;
  tasa_3pm: string;
  sellos: string;
  tasa_75pm: string;
  firma_impuestos: string;
  total_impuestos: string;
  inscripcion: string;
  protocolo: string;
  ii_certificados: string;
  municipio: string;
  fotocopias_urgentes: string;
  certificaciones_extra: string;
  catastro: string;
  testimonio: string;
  concuerda: string;
  informes_notariales: string;
  extracto: string;
  fotocopias_simples: string;
  tasas_minimas: string;
  total_gastos_admin: string;
  dif_honorarios: string;
  total_parcial: string;
  total_sin_iva: string;
  iva: string;
  total_factura: string;
  updated_at: string;
}

/** @deprecated Replaced by PagoCliente / PagoColegio in feature 003 */
export interface GastoAdicionalResponse {
  id: string;
  escritura_id: string;
  concepto: string;
  monto: string;
  direccion: DireccionGasto;
  fecha: string;
  created_at: string;
}

/** @deprecated Replaced by PagoClienteInput */
export interface GastoAdicionalInput {
  concepto: string;
  monto: string;
  direccion: DireccionGasto;
  fecha: string;
}

export interface PagoClienteInput {
  monto: string;
  fecha: string;
  concepto?: string;
}

export interface PagoClienteResponse {
  id: string;
  escritura_id: string;
  monto: string;
  fecha: string;
  concepto: string;
  created_at: string;
}

export type ImputacionPagoColegio = "total_impuestos" | "honorarios_varios" | "otro";

export type PlazoColegioEstado = "no_aplica" | "pendiente" | "vencido" | "pagado";

export type PlazoColegioUrgencia = "verde" | "amarillo" | "rojo";

export interface PlazoColegioResponse {
  estado: PlazoColegioEstado;
  fecha_vencimiento: string | null;
  dias_restantes: number | null;
  urgencia: PlazoColegioUrgencia | null;
  monto_referencia: string;
  monto_pagado: string;
  monto_pendiente: string;
}

export interface PagoColegioInput {
  monto: string;
  fecha: string;
  concepto?: string;
  imputacion: ImputacionPagoColegio;
}

export interface PagoColegioResponse {
  id: string;
  escritura_id: string;
  monto: string;
  fecha: string;
  concepto: string;
  imputacion: ImputacionPagoColegio;
  created_at: string;
}

export interface EscrituraResponse {
  id: string;
  nombre: string;
  estado: EstadoEscritura;
  escribano_id: string;
  escribano_nombre: string;
  usd_value: string;
  dolar_mep: string;
  dolar_nacion: string;
  config_version_id: string;
  created_at: string;
  closed_at: string | null;
  updated_at: string;
  factura: FacturaPrincipalResponse;
  costo_total: string;
  total_pagado: string;
  saldo_pendiente: string;
  pagada_al_100: boolean;
  sobrepago: boolean;
  total_leyes_notariales_proyectadas: string;
  balance_impuestos: BalanceImpuestosResponse | null;
  plazo_colegio: PlazoColegioResponse | null;
  pagos_cliente: PagoClienteResponse[];
  pagos_colegio: PagoColegioResponse[];
}

export interface EscrituraListItem {
  id: string;
  nombre: string;
  estado: EstadoEscritura;
  escribano_id: string;
  escribano_nombre: string;
  usd_value: string;
  created_at: string;
  costo_total: string;
  total_pagado: string;
  saldo_pendiente: string;
  pagada_al_100: boolean;
  sobrepago: boolean;
  plazo_colegio: PlazoColegioResponse | null;
}

export interface LiquidacionEscrituraItem {
  escritura_id: string;
  nombre: string;
  estado: EstadoEscritura;
  monto_cobrado: string;
  neto_impuestos: string;
}

export interface LiquidacionEscribano {
  escribano_id: string;
  escribano_nombre: string;
  total: string;
  escrituras: LiquidacionEscrituraItem[];
}

export interface LiquidacionResumen {
  anio: number;
  mes: number;
  total_costanza: string;
  total_gabriel: string;
  total_monica: string;
  total_global: string;
  por_escribano: LiquidacionEscribano[];
}

export interface PagoEscribano {
  nombre: string;
  monto_total: string;
  deduccion_gastos_extraordinarios: string;
  monto_neto: string;
  escrituras: LiquidacionEscrituraItem[];
}

export interface PagoSecretaria {
  nombre: string;
  monto: string;
  base_total: string;
}

export interface PagoSalariosResumen {
  anio: number;
  mes: number;
  escribanos: PagoEscribano[];
  secretarias: PagoSecretaria[];
  total_gastos_extraordinarios: string;
  advertencia_reparto: string | null;
}

export interface GastoExtraordinarioInput {
  concepto: string;
  monto: string;
  fecha: string;
}

export interface GastoExtraordinarioUpdate {
  concepto?: string;
  monto?: string;
  fecha?: string;
}

export interface GastoExtraordinarioResponse {
  id: string;
  concepto: string;
  monto: string;
  fecha: string;
  created_at: string;
  updated_at: string;
}

export interface GastosExtraordinariosListResponse {
  anio: number;
  mes: number;
  gastos: GastoExtraordinarioResponse[];
  total: string;
}

export interface ConfiguracionInput {
  descripcion?: string | null;
  honorario_pct?: string;
  honorario_min: string;
  certificacion_pct?: string;
  aporte_pct?: string;
  cinco_pct_hon_pct?: string;
  cinco_pct_hon_min: string;
  firma_honorarios: string;
  art2_a_pct?: string;
  art12_a_pct?: string;
  art12_a_min: string;
  art12_c_pct?: string;
  art12_f: string;
  tasa_3pm_pct?: string;
  sellos_pct?: string;
  sellos_ajuste_fijo?: string;
  tasa_75pm_pct?: string;
  firma_impuestos: string;
  inscripcion: string;
  protocolo: string;
  ii_certificados: string;
  municipio: string;
  fotocopias_urgentes: string;
  certificaciones_extra: string;
  catastro: string;
  testimonio: string;
  concuerda: string;
  informes_notariales: string;
  extracto: string;
  fotocopias_simples: string;
  tasas_minimas: string;
  salario_secretarias_total: string;
}

export interface ConfiguracionResponse extends ConfiguracionInput {
  id: string;
  version: number;
  created_at: string;
  created_by: string | null;
}

export interface ApiError {
  detail: string | Record<string, unknown>;
  code?: string;
}

export type CasaCotizacion = "bolsa" | "oficial";

export interface CotizacionResponse {
  casa: CasaCotizacion;
  fecha: string;
  compra: string;
  venta: string;
  source: string;
}

export interface EscribanoResponse {
  id: string;
  nombre: string;
  activo: boolean;
  monotributista: boolean;
  created_at: string;
}

export interface EscribanoUpdateRequest {
  monotributista: boolean;
}

export interface EmpleadoResponse {
  id: string;
  nombre: string;
  sueldo: string;
  activo: boolean;
  created_at: string;
  updated_at: string;
}

export type LibroOrigen = "honorario" | "impuesto" | "extraordinario";

export interface LibroLineaResponse {
  escritura_id: string | null;
  escritura_nombre: string | null;
  concepto: string;
  monto: string;
  fecha_pago: string;
  origen?: LibroOrigen;
  tipo_impuesto?: TipoImpuesto | null;
  gasto_extraordinario_id?: string | null;
}

export interface DeudaResumenItem {
  escritura_id: string;
  escritura_nombre: string;
  costo_total: string;
  total_pagado: string;
  saldo_pendiente: string;
}

export interface LibroSalidaResponse {
  anio: number;
  mes: number;
  lineas: LibroLineaResponse[];
  total: string;
}

export interface LibroEntradaResponse extends LibroSalidaResponse {
  resumen_deudas: DeudaResumenItem[];
}

export type TipoImpuesto =
  | "API"
  | "TGI"
  | "AGUAS_SANTAFESINAS"
  | "EPE"
  | "EXPENSAS"
  | "LITORAL_GAS";

export type DireccionProrrateo = "hacia_atras" | "hacia_adelante";

export type EstadoPagos = "sin_pagos" | "solo_cliente" | "solo_escribania" | "completos";

export interface ImpuestoInput {
  tipo: TipoImpuesto;
  monto_total: string;
  periodo_inicio: string;
  periodo_fin: string;
  fecha_corte: string;
  direccion_prorrateo: DireccionProrrateo;
}

export interface ImpuestoUpdate {
  tipo?: TipoImpuesto;
  monto_total?: string;
  periodo_inicio?: string;
  periodo_fin?: string;
  fecha_corte?: string;
  direccion_prorrateo?: DireccionProrrateo;
}

export interface PagoImpuestoInput {
  monto: string;
  fecha: string;
}

export interface PagoImpuestoClienteResponse {
  id: string;
  impuesto_id: string;
  escritura_id: string;
  monto: string;
  fecha: string;
  created_at: string;
  updated_at: string;
}

export type PagoImpuestoEscribaniaResponse = PagoImpuestoClienteResponse;

export interface ImpuestoResponse {
  id: string;
  escritura_id: string;
  tipo: TipoImpuesto;
  monto_total: string;
  periodo_inicio: string;
  periodo_fin: string;
  fecha_corte: string;
  direccion_prorrateo: DireccionProrrateo;
  monto_prorrateado_sugerido: string;
  estado_pagos: EstadoPagos;
  pago_cliente: PagoImpuestoClienteResponse | null;
  pago_escribania: PagoImpuestoEscribaniaResponse | null;
  created_at: string;
  updated_at: string;
}

export interface ImpuestoPendienteItem {
  impuesto_id: string;
  tipo: TipoImpuesto;
  falta_cliente: boolean;
  falta_escribania: boolean;
}

export interface BalanceImpuestosResponse {
  total_cliente: string;
  total_escribania: string;
  balance: string;
  impuestos_pendientes: ImpuestoPendienteItem[];
  puede_cerrar: boolean;
}

export interface ImpuestosListResponse {
  impuestos: ImpuestoResponse[];
  balance: BalanceImpuestosResponse;
}

/** @deprecated Use LibroSalidaResponse or LibroEntradaResponse */
export type LibroResponse = LibroSalidaResponse;
