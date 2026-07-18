// Types derived from specs/001-plataforma-contaduria/contracts/openapi.yaml

export type EstadoEscritura = "abierta" | "cerrada";
export type Escribano = "costanza" | "gabriel" | "victoria";
export type DireccionGasto = "entrada" | "salida";

export type SseEventType =
  | "escritura.created"
  | "escritura.updated"
  | "escritura.closed"
  | "gasto.created"
  | "liquidacion.updated";

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
  escribano: Escribano;
  usd_value: string;
  dolar_mep: string;
  dolar_nacion: string;
}

export interface EscrituraUpdate {
  nombre?: string;
  escribano?: Escribano;
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
  total_factura: string;
  updated_at: string;
}

export interface GastoAdicionalResponse {
  id: string;
  escritura_id: string;
  concepto: string;
  monto: string;
  direccion: DireccionGasto;
  fecha: string;
  created_at: string;
}

export interface GastoAdicionalInput {
  concepto: string;
  monto: string;
  direccion: DireccionGasto;
  fecha: string;
}

export interface EscrituraResponse {
  id: string;
  nombre: string;
  estado: EstadoEscritura;
  escribano: Escribano;
  usd_value: string;
  dolar_mep: string;
  dolar_nacion: string;
  config_version_id: string;
  created_at: string;
  closed_at: string | null;
  updated_at: string;
  factura: FacturaPrincipalResponse;
  gastos_adicionales: GastoAdicionalResponse[];
}

export interface EscrituraListItem {
  id: string;
  nombre: string;
  estado: EstadoEscritura;
  escribano: Escribano;
  usd_value: string;
  created_at: string;
  total_factura: string;
}

export interface LiquidacionEscrituraItem {
  escritura_id: string;
  nombre: string;
  estado: EstadoEscritura;
  honorario_principal: string;
  certificacion: string;
  subtotal: string;
}

export interface LiquidacionEscribano {
  escribano: Escribano;
  total: string;
  escrituras: LiquidacionEscrituraItem[];
}

export interface LiquidacionResumen {
  anio: number;
  mes: number;
  total_costanza: string;
  total_gabriel: string;
  total_victoria: string;
  total_global: string;
  por_escribano: LiquidacionEscribano[];
}

export interface PagoEscribano {
  nombre: string;
  monto_total: string;
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
  detail: string;
  code?: string;
}
