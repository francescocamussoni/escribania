# Feature Specification: Vencimiento de pago al Colegio y régimen Monotributo

**Feature Branch**: `008-factura-vencimiento-monotributo`  
**Created**: 2026-07-26  
**Status**: Draft  
**Input**: User description: "Total impuestos (de corresponde) es un monto que debe pagarse desde la escribanía al colegio de escribanos. Una vez que se carga una factura solo se disponen de 30 días de corrido para hacer este pago, de lo contrario, se vence. Visualizar en el menú de Escrituras los días restantes para pagar la factura, con mapa de color (30-20 verde, 20-10 amarillo, 10-0 rojo). Ordenar facturas por fecha de vencimiento. Información en encabezado al entrar en una factura. Escribanos monotributistas: IVA=0, Total+IVA=Total. Configurable desde solapa escribanos. Actualizar mock DB y Costanza como monotributista."

## Clarifications

### Session 2026-07-26

- Q: ¿Aplicar TDD y/o unit tests estrictos para esta feature? → A: **Sí — TDD-first** (tests escritos antes de la implementación en todo el scope).
- Q: ¿Qué pagos al Colegio cubren el plazo de Total impuestos? → A: **Imputación explícita** — solo cuentan pagos imputados a Total impuestos / Corresponde; pagos de honorarios varios no afectan este plazo.
- Q: ¿Al cambiar el flag monotributista, qué escrituras se recalculan? → A: **Inmediato** — al guardar el flag, se recalculan todas las escrituras abiertas de ese escribano.
- Q: ¿Cómo tratar pagos al Colegio existentes sin imputación? → A: **Default honorarios varios** — migrar como honorarios varios; no cuentan para el plazo de Total impuestos.
- Q: ¿Cómo indica la secretaria la imputación al registrar un pago al Colegio? → A: **Selector obligatorio** con categorías fijas: Total impuestos / Corresponde, Honorarios varios, Otro.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Ver plazo de pago al Colegio en el listado de Escrituras (Priority: P1)

La secretaria abre la sección **Escrituras** y, para cada escritura con obligación pendiente
de pago de **Total impuestos** (sección Corresponde de la factura) al Colegio de Escribanos,
ve cuántos días de corrido le quedan antes del vencimiento. El indicador usa un código de
color que refleja la urgencia: verde (30 a 20 días restantes), amarillo (20 a 10 días) y
rojo (10 a 0 días). Si el plazo ya venció, el indicador permanece en rojo y muestra que está
vencido.

**Why this priority**: Es la alerta operativa central que evita multas o inconvenientes con
el Colegio. Sin visibilidad en el listado, la secretaria debe revisar escritura por escritura.

**Independent Test**: Crear o usar escrituras de demo con distintas fechas de creación y
montos de Total impuestos, abrir el listado de Escrituras y verificar días restantes y colores
sin entrar al detalle de cada una.

**Acceptance Scenarios**:

1. **Given** una escritura abierta cuya factura tiene Total impuestos mayor a cero y cuya
   suma de pagos al Colegio **imputados a Total impuestos / Corresponde** es menor que ese
   monto, **When** la secretaria visualiza el listado de Escrituras, **Then** ve una columna
   o indicador con los días restantes calculados desde la fecha de carga de la factura
   (fecha de creación de la escritura) hasta el vencimiento a los 30 días de corrido.

2. **Given** una escritura con 25 días restantes, **When** se muestra el indicador,
   **Then** aparece en **verde**.

3. **Given** una escritura con 15 días restantes, **When** se muestra el indicador,
   **Then** aparece en **amarillo**.

4. **Given** una escritura con 5 días restantes, **When** se muestra el indicador,
   **Then** aparece en **rojo**.

5. **Given** una escritura cuyo plazo de 30 días ya venció y el pago no está cubierto,
   **When** se muestra el indicador, **Then** aparece en **rojo** con estado **Vencido**
   (0 días restantes o equivalente claro).

6. **Given** una escritura cuya suma de pagos al Colegio imputados a Total impuestos /
   Corresponde es mayor o igual a Total impuestos, **When** la secretaria visualiza el
   listado, **Then** el indicador muestra estado **Pagado** sin código de urgencia por color.

7. **Given** una escritura con pagos al Colegio imputados solo a honorarios varios (u otro
   concepto distinto de Total impuestos), **When** la secretaria visualiza el listado,
   **Then** el countdown de Total impuestos sigue activo según días restantes.

8. **Given** una escritura cuyo Total impuestos es cero, **When** la secretaria visualiza
   el listado, **Then** no se muestra plazo de vencimiento (o se indica que no aplica).

---

### User Story 2 — Ordenar Escrituras por fecha de vencimiento del pago al Colegio (Priority: P1)

La secretaria puede ordenar el listado de Escrituras por **fecha de vencimiento** del pago
de Total impuestos al Colegio, de forma similar al ordenamiento existente por fecha de
creación, para priorizar las obligaciones más próximas a vencer.

**Why this priority**: Complementa la visualización de días restantes; sin ordenamiento, la
secretaria no puede actuar rápidamente sobre las más urgentes en listas largas.

**Independent Test**: Con al menos tres escrituras con fechas de creación distintas, activar
orden por vencimiento y verificar que el orden coincide con la fecha límite de pago al Colegio.

**Acceptance Scenarios**:

1. **Given** el listado de Escrituras con varias obligaciones pendientes, **When** la
   secretaria activa ordenar por fecha de vencimiento, **Then** las escrituras se reordenan
   según la fecha límite (creación + 30 días de corrido).

2. **Given** el orden por vencimiento activo, **When** la secretaria alterna la dirección
   del orden, **Then** puede ver primero las más urgentes (ascendente, por defecto) o las
   más lejanas (descendente).

3. **Given** escrituras con pago al Colegio ya cubierto o sin Total impuestos, **When** se
   ordena por vencimiento, **Then** esas filas quedan al final del listado, manteniendo un
   orden estable entre ellas.

---

### User Story 3 — Ver plazo de pago en el encabezado del detalle de Escritura (Priority: P1)

Al abrir el detalle de una escritura (vista de factura), la secretaria ve en el **encabezado**
la misma información de plazo: días restantes, fecha de vencimiento, estado (pendiente,
vencido o pagado) y el mismo código de color que en el listado.

**Why this priority**: Cuando la secretaria trabaja sobre una escritura concreta, necesita el
contexto del vencimiento sin volver al listado.

**Independent Test**: Abrir una escritura con obligación pendiente y verificar que el
encabezado muestra días, color y fecha de vencimiento coherentes con el listado.

**Acceptance Scenarios**:

1. **Given** una escritura con pago al Colegio pendiente, **When** la secretaria abre su
   detalle, **Then** el encabezado muestra días restantes, fecha de vencimiento y color
   según las mismas reglas del listado.

2. **Given** una escritura con pago cubierto o sin Total impuestos, **When** la secretaria
   abre su detalle, **Then** el encabezado refleja **Pagado** o **No aplica** de forma
   consistente con el listado.

3. **Given** una escritura cerrada con obligación vencida no cubierta, **When** la secretaria
   abre su detalle, **Then** el encabezado sigue mostrando el estado vencido (solo lectura).

---

### User Story 4 — Configurar escribanos monotributistas (Priority: P2)

Algunos escribanos tributan bajo el régimen **Monotributo** y no facturan IVA. Desde la
solapa **Escribanos** en Configuración, la secretaria puede marcar o desmarcar si un
escribano es monotributista. Para escrituras asignadas a un escribano monotributista, el IVA
de la factura debe ser **cero** y **Total + IVA** debe coincidir con **Total** (sin
componente de IVA).

**Why this priority**: Afecta el monto que debe pagar el cliente y los totales de liquidación;
es independiente del vencimiento pero crítico para la exactitud contable.

**Independent Test**: Marcar un escribano como monotributista, crear o actualizar una
escritura a su nombre y verificar que IVA = 0 y Total + IVA = Total en la sección Totales.

**Acceptance Scenarios**:

1. **Given** la solapa Escribanos en Configuración, **When** la secretaria edita un
   escribano activo, **Then** puede activar o desactivar la opción **Monotributista**.

2. **Given** un escribano marcado como monotributista, **When** se calcula la factura de una
   escritura asignada a ese escribano, **Then** el IVA es 0 y Total + IVA es igual a Total.

3. **Given** un escribano no monotributista, **When** se calcula la factura, **Then** el
   IVA se calcula según la regla vigente (21 % sobre Dif Honorarios + Total impuestos, según
   feature 007) y Total + IVA = Total + IVA calculado.

4. **Given** un escribano cuyo flag monotributista cambia (activado o desactivado), **When**
   la secretaria guarda la configuración, **Then** el sistema recalcula de inmediato la
   factura de **todas** las escrituras abiertas asignadas a ese escribano con el régimen
   correspondiente (IVA = 0 si monotributista; fórmula 007 si no).

5. **Given** el dataset de demostración, **When** se carga el entorno mock, **Then** el
   escribano **Costanza** figura como monotributista y sus escrituras de demo reflejan IVA
   cero.

---

### User Story 5 — Imputar pagos al Colegio al registrarlos (Priority: P1)

Al registrar un pago al Colegio en el detalle de una escritura, la secretaria elige
obligatoriamente la **imputación** del pago mediante un selector con categorías fijas. Solo
los pagos imputados a **Total impuestos / Corresponde** cuentan para cerrar el plazo de 30
días; los demás no afectan ese countdown.

**Why this priority**: Sin imputación explícita no es posible distinguir pagos de impuestos
de honorarios varios; es prerequisito funcional del plazo de vencimiento.

**Independent Test**: Registrar un pago al Colegio eligiendo cada categoría del selector y
verificar que solo "Total impuestos / Corresponde" reduce el saldo pendiente del plazo.

**Acceptance Scenarios**:

1. **Given** el formulario de pago al Colegio en una escritura abierta, **When** la
   secretaria lo despliega, **Then** debe elegir obligatoriamente una imputación entre:
   **Total impuestos / Corresponde**, **Honorarios varios** u **Otro**.

2. **Given** un pago registrado con imputación **Total impuestos / Corresponde**, **When** la
   suma de pagos con esa imputación alcanza Total impuestos, **Then** el indicador de plazo
   pasa a **Pagado** en listado y encabezado.

3. **Given** un pago registrado con imputación **Honorarios varios** u **Otro**, **When** la
   secretaria revisa el plazo de Total impuestos, **Then** ese pago no reduce el saldo
   pendiente ni cierra el countdown.

4. **Given** un intento de registro sin imputación seleccionada, **When** la secretaria
   confirma, **Then** el sistema rechaza el registro con mensaje de validación claro.

---

### Edge Cases

- Escritura creada hoy: muestra 30 días restantes (verde).
- Escritura en el día exacto de vencimiento (día 30): cuenta como 0 días restantes (rojo).
- Escritura con Total impuestos > 0 pero pagos al Colegio parciales **imputados a Total
  impuestos**: sigue mostrando countdown hasta que la suma imputada cubra Total impuestos.
- Pagos al Colegio existentes sin imputación al desplegar: se migran automáticamente como
  **honorarios varios** y no cierran el plazo de Total impuestos.
- Pagos al Colegio imputados a honorarios varios u otros conceptos: no reducen ni cierran el
  plazo de Total impuestos.
- Cambio de flag monotributista en Configuración: recalcula de inmediato **todas** las
  escrituras abiertas del escribano; escrituras cerradas no se alteran.
- Cambio de escribano en escritura abierta: el régimen monotributo aplicado es el del
  escribano actualmente asignado; la factura se recalcula al guardar.
- Escribano desactivado que era monotributista: las escrituras históricas conservan el
  cálculo vigente al momento de su último recálculo; no se alteran escrituras cerradas.
- Escrituras cerradas: el indicador de vencimiento es de solo lectura; no se reinicia el plazo.
- Zona horaria / fecha de creación: el vencimiento se calcula en **días de corrido** sobre
  fechas calendario locales de la escribanía (sin fracciones de día en la UI).

---

## Requirements *(mandatory)*

### Functional Requirements

#### Plazo de pago de Total impuestos al Colegio

- **FR-001**: El sistema MUST calcular la fecha de vencimiento del pago al Colegio como la
  fecha de creación de la escritura (momento en que se carga la factura) más **30 días de
  corrido**.

- **FR-002**: El monto sujeto a este plazo MUST ser **Total impuestos** de la sección
  **Corresponde** de la Factura Principal (feature 007).

- **FR-003**: El sistema MUST considerar la obligación **cubierta** cuando la suma de
  pagos al Colegio **imputados explícitamente a Total impuestos / Corresponde** en esa
  escritura es mayor o igual a Total impuestos. Pagos imputados a honorarios varios u otros
  conceptos MUST NOT afectar este plazo ni marcar la obligación como cubierta.

- **FR-003a**: Al registrar un pago al Colegio, la secretaria MUST seleccionar
  obligatoriamente la **imputación** mediante un selector con categorías fijas:
  **Total impuestos / Corresponde**, **Honorarios varios** u **Otro**. El sistema MUST
  rechazar pagos sin imputación.

- **FR-003b**: Los pagos al Colegio existentes sin imputación al momento del despliegue MUST
  migrarse automáticamente con imputación **honorarios varios** y MUST NOT contarse hacia el
  plazo de Total impuestos.

- **FR-004**: El sistema MUST calcular **días restantes** como la diferencia en días de
  corrido entre la fecha actual y la fecha de vencimiento; si la fecha actual supera el
  vencimiento, los días restantes son 0 y el estado es **Vencido**.

- **FR-005**: El listado de Escrituras MUST mostrar, para cada fila con obligación
  pendiente, los días restantes y un indicador visual con este mapa de color:
  - **Verde**: más de 20 y hasta 30 días restantes (inclusive en el límite superior).
  - **Amarillo**: más de 10 y hasta 20 días restantes.
  - **Rojo**: de 0 a 10 días restantes, o estado **Vencido**.

- **FR-006**: El listado MUST permitir ordenar por **fecha de vencimiento** con dirección
  ascendente (por defecto: vencimientos más próximos primero) y descendente alternable.

- **FR-007**: El encabezado del detalle de Escritura MUST mostrar la misma información de
  plazo (días restantes o estado Pagado/Vencido/No aplica, fecha de vencimiento y color)
  que el listado.

- **FR-008**: Si Total impuestos es cero, el sistema MUST NOT mostrar countdown de
  vencimiento (estado **No aplica**).

- **FR-009**: Si la obligación está cubierta, el sistema MUST mostrar estado **Pagado** sin
  colores de urgencia.

#### Régimen monotributo por escribano

- **FR-010**: La entidad Escribano MUST admitir un atributo **monotributista** (sí/no)
  editable desde la solapa Escribanos en Configuración.

- **FR-011**: Para escrituras cuyo escribano asignado es monotributista, el cálculo de la
  factura MUST fijar **IVA = 0** y **Total + IVA = Total**.

- **FR-012**: Para escribanos no monotributistas, el cálculo de IVA y Total + IVA MUST
  seguir las reglas de la feature 007 sin cambios.

- **FR-013**: Al cambiar el flag monotributista de un escribano en Configuración, el sistema
  MUST recalcular de inmediato la factura de **todas** las escrituras abiertas asignadas a
  ese escribano. Al cambiar el escribano asignado en una escritura abierta, el sistema MUST
  recalcular esa escritura con el régimen del escribano correspondiente.

- **FR-014**: El dataset mock/demo MUST actualizarse para que **Costanza** sea monotributista
  y las escrituras de demo asociadas reflejen IVA cero de forma consistente.

- **FR-015**: Escrituras cerradas MUST NOT recalcularse automáticamente ante cambios de
  configuración del escribano.

### Key Entities

- **Plazo pago Colegio (derivado)**: Fecha de inicio (creación de escritura), fecha de
  vencimiento (+30 días), días restantes, estado (pendiente / vencido / pagado / no aplica),
  monto de referencia (Total impuestos), monto ya pagado **imputado a Total impuestos**.

- **Pago al Colegio**: Incluye **imputación** obligatoria (selector: Total impuestos /
  Corresponde, Honorarios varios, Otro); solo la imputación a Total impuestos cuenta para
  el plazo.

- **Escribano**: Atributo **monotributista** que condiciona el cálculo de IVA en las
  facturas de las escrituras asignadas.

- **Factura Principal**: Conserva Total impuestos (Corresponde), Total, IVA y Total + IVA;
  estos últimos dependen del régimen del escribano asignado.

---

## Assumptions

- La fecha de inicio del plazo es la **fecha de creación de la escritura**, que coincide con
  la carga automática de la Factura Principal.
- El plazo aplica solo al pago de **Total impuestos** al Colegio, no a honorarios varios ni
  a otros conceptos de pago al Colegio.
- La cobertura del plazo se determina comparando **solo** pagos al Colegio imputados a
  Total impuestos / Corresponde contra Total impuestos de la misma escritura.
- Los límites de color son inclusivos en el extremo superior de cada tramo (ej. exactamente
  20 días restantes = amarillo; exactamente 10 días = rojo).
- La feature 007 (refactor de montos de factura) está disponible o se implementa antes;
  Total impuestos proviene de la sección Corresponde.
- Solo usuarios autenticados con acceso a Configuración pueden modificar el flag
  monotributista.
- Pagos al Colegio preexistentes sin categoría de imputación se asumen como honorarios
  varios en la migración inicial.

---

## Testing Strategy

- **Enfoque elegido**: TDD — tests escritos antes de la implementación en todo el scope.
- **Rationale**: La feature combina cálculos monetarios (IVA/monotributo), fechas de
  vencimiento y estados derivados (pagado/vencido/colores); errores impactan operación y
  confianza. TDD-first alinea con la integridad de fórmulas exigida en la constitución del
  proyecto.
- **Alcance**: Tests unitarios para lógica de vencimiento, bandas de color, cobertura de
  pagos al Colegio (por imputación) e IVA monotributo; tests de integración/API para
  endpoints, listados y validación de imputación obligatoria; tests de UI para indicadores
  en listado, encabezado de detalle y selector de imputación en pagos al Colegio.
- **Nota para downstream**: Esta decisión MUST ser honrada por `/spec-kitti.plan` (contratos
  de test) y `/spec-kitti.tasks` (tareas TDD/unit-test generadas en consecuencia).

---

## Dependencies

- **007-refactor-factura-montos**: define Total impuestos en Corresponde, estructura de
  Totales (Total, IVA, Total + IVA) y fórmula de IVA para no monotributistas.
- **003-pagos-cliente**: modelo de pagos al Colegio por escritura, usado para determinar
  obligación cubierta.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El 100 % de las escrituras con Total impuestos pendiente muestran en el
  listado y en el encabezado de detalle el mismo número de días restantes y el mismo color
  para una misma fecha de consulta.

- **SC-002**: La secretaria puede identificar en menos de 5 segundos, en el listado de
  Escrituras, cuáles obligaciones vencen en los próximos 10 días (indicador rojo o
  ordenamiento por vencimiento).

- **SC-003**: Al ordenar por fecha de vencimiento ascendente, las tres escrituras con
  vencimiento más próximo aparecen siempre antes que cualquier escritura con vencimiento
  posterior o sin plazo aplicable.

- **SC-004**: El 100 % de las facturas de escribanos monotributistas muestran IVA = 0 y
  Total + IVA igual a Total, verificable con el dataset canónico y con Costanza en demo.

- **SC-005**: Tras marcar o desmarcar monotributista en un escribano, el 100 % de sus
  escrituras abiertas muestran totales recalculados (IVA = 0 o según fórmula 007) de
  inmediato al guardar la configuración, sin requerir editar cada escritura.

- **SC-006**: Cero discrepancias entre el estado Pagado en listado y en encabezado de detalle
  para escrituras con pagos al Colegio **imputados a Total impuestos** que cubren ese monto.
