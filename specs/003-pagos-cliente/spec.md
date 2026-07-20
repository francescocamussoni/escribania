# Feature Specification: Pagos del Cliente y Libros Contables Basados en Caja Real

**Feature Branch**: `003-pagos-cliente`  
**Created**: 2026-07-20  
**Status**: Draft  
**Input**: User description: "Refactorizar gastos adicionales a pagos del cliente con saldo pendiente por escritura, simplificación del libro de entrada y libro de salida solo para pagos al colegio de escribanos"

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Registrar Pagos del Cliente y Ver Saldo Pendiente (Priority: P1)

La secretaria registra los pagos reales que efectúa el cliente contra una escritura.
Cada pago tiene un monto y una fecha. El sistema muestra en todo momento el costo total
de la escritura, el total pagado y el saldo pendiente. El concepto de "gastos adicionales"
con dirección entrada/salida deja de existir; en su lugar, solo hay **pagos del cliente**
que reducen la deuda de la escritura.

**Why this priority**: Corrige el supuesto ficticio de que todo el dinero de la factura
ingresa automáticamente. Sin pagos reales registrados, no hay caja. Este es el cambio
conceptual central que habilita el resto de la feature.

**Independent Test**: Se puede probar creando una escritura, registrando uno o más pagos
parciales, y verificando que el saldo pendiente se actualiza correctamente — sin necesidad
de revisar libros ni liquidación.

**Acceptance Scenarios**:

1. **Given** una escritura abierta con costo total de $1.000.000, **When** la secretaria
   registra un pago del cliente de $400.000 con fecha y concepto opcional, **Then** el
   sistema muestra total pagado $400.000, saldo pendiente $600.000, y el pago aparece
   en el historial de pagos de la escritura.

2. **Given** una escritura con saldo pendiente de $600.000, **When** la secretaria registra
   un segundo pago de $600.000, **Then** el saldo pendiente pasa a $0 y el sistema
   indica que la escritura está pagada al 100%.

3. **Given** una escritura abierta, **When** la secretaria intenta registrar un pago con
   monto cero, negativo, o mayor al saldo pendiente, **Then** el sistema rechaza el pago
   con un mensaje de validación claro.

4. **Given** una escritura abierta con pagos registrados, **When** se modifican los valores
   de entrada (USD, tipos de cambio) y el costo total se recalcula, **Then** el saldo
   pendiente se actualiza automáticamente como `costo_total − total_pagado`.

5. **Given** una escritura cerrada, **When** la secretaria intenta registrar un nuevo pago,
   **Then** el sistema rechaza la operación indicando que la escritura está cerrada.

---

### User Story 2 — Cierre de Escritura Condicionado al Pago Completo (Priority: P1)

La secretaria solo puede cerrar una escritura cuando el cliente la pagó al 100%
(saldo pendiente = $0). Una escritura con saldo pendiente mayor a cero no puede cerrarse.

**Why this priority**: Garantiza integridad operativa: una escritura cerrada representa
un trámite finalizado y cobrado en su totalidad. Es la regla de negocio que conecta
los pagos con el ciclo de vida de la escritura.

**Independent Test**: Se puede probar intentando cerrar escrituras con distintos niveles
de pago y verificando que solo las pagadas al 100% permiten el cierre.

**Acceptance Scenarios**:

1. **Given** una escritura con saldo pendiente $0, **When** la secretaria solicita cerrar
   la escritura, **Then** el cierre se completa y la escritura queda en modo solo lectura.

2. **Given** una escritura con saldo pendiente mayor a $0, **When** la secretaria intenta
   cerrarla, **Then** el sistema bloquea el cierre e informa el monto pendiente de cobro.

3. **Given** una escritura cerrada, **When** cualquier usuario intenta editarla o agregar
   pagos, **Then** el sistema mantiene la inmutabilidad existente de escrituras cerradas.

---

### User Story 3 — Libro de Entrada Basado en Pagos Reales (Priority: P2)

El Libro de Entrada refleja únicamente los pagos del cliente recibidos. Cada línea
corresponde a un pago con su monto, fecha, y referencia a la escritura. El libro muestra
cómo se reduce la deuda pendiente de cada escritura a medida que ingresan pagos.

**Why this priority**: El libro de entrada es el registro de caja real. Reemplaza el
modelo anterior que derivaba automáticamente honorarios y certificación como si ya
hubieran ingresado.

**Independent Test**: Se puede probar registrando pagos en distintas escrituras de un mes
y verificando que el Libro de Entrada del mes muestra solo esos pagos con sus referencias
y el resumen de deuda pendiente por escritura.

**Acceptance Scenarios**:

1. **Given** pagos del cliente registrados en julio 2026, **When** la secretaria consulta
   el Libro de Entrada de julio 2026, **Then** ve una línea por cada pago con: monto,
   fecha del pago, nombre de la escritura, y enlace navegable al detalle de la escritura.

2. **Given** una escritura con costo total $1.000.000 y dos pagos de $300.000 y $200.000
   en el mes, **When** se consulta el Libro de Entrada, **Then** aparecen las dos líneas
   de pago y un resumen de la escritura indicando: costo total $1.000.000, pagado $500.000,
   pendiente $500.000.

3. **Given** una escritura creada en julio sin pagos registrados, **When** se consulta
   el Libro de Entrada de julio, **Then** la escritura NO genera líneas de ingreso, pero
   puede aparecer en el resumen de deudas pendientes del período si tiene saldo > 0.

4. **Given** un pago registrado en una escritura, **When** la secretaria consulta el Libro
   de Entrada del mes del pago, **Then** el total del período refleja la suma de todos
   los pagos del mes (no el costo total de las escrituras).

5. **Given** que se registra un nuevo pago, **When** otra pestaña tiene abierto el Libro
   de Entrada del mes, **Then** el libro se actualiza en tiempo real con la nueva línea
   y el resumen de deuda actualizado.

---

### User Story 4 — Registrar Pagos al Colegio de Escribanos por Escritura (Priority: P2)

Cada escritura expone una sección **"Pagos al Colegio"** donde la secretaria registra
manualmente los pagos que la escribanía efectúa al Colegio de Escribanos. Estos pagos son
**independientes** del estado de cobro del cliente: la escribanía puede pagar al Colegio
aunque el cliente aún no haya saldado la escritura, y viceversa.

**Why this priority**: Los pagos al Colegio y los pagos del cliente son flujos de caja
disconexos en la operación real. Automatizar el Libro de Salida desde la factura o el
cierre de escritura no refleja cuándo la escribanía efectivamente transfiere al Colegio.

**Independent Test**: Se puede probar registrando pagos al Colegio en una escritura con
saldo pendiente del cliente y verificando que aparecen en el historial de la escritura
y en el Libro de Salida del mes — sin necesidad de que el cliente haya pagado.

**Acceptance Scenarios**:

1. **Given** una escritura abierta con saldo pendiente del cliente, **When** la secretaria
   registra un pago al Colegio de $150.000 con fecha, **Then** el pago aparece en la
   sección "Pagos al Colegio" de la escritura.

2. **Given** una escritura sin pagos del cliente, **When** la secretaria registra un pago
   al Colegio, **Then** el sistema lo acepta sin restricción por saldo pendiente del cliente.

3. **Given** una escritura abierta, **When** la secretaria intenta registrar un pago al
   Colegio con monto cero o negativo, **Then** el sistema rechaza el pago con mensaje claro.

4. **Given** una escritura cerrada, **When** la secretaria intenta registrar un nuevo pago
   al Colegio, **Then** el sistema rechaza la operación (escritura en solo lectura).

5. **Given** pagos al Colegio registrados, **When** la secretaria consulta el detalle de
   la escritura, **Then** ve el historial completo de pagos al Colegio separado de los
   pagos del cliente, junto con el **total de leyes notariales proyectadas** de la factura
   como referencia informativa (sin validación ni bloqueo del monto ingresado).

---

### User Story 5 — Libro de Salida Basado en Pagos Reales al Colegio (Priority: P2)

El Libro de Salida refleja únicamente los **pagos al Colegio de Escribanos** registrados
manualmente por la secretaria. Cada línea corresponde a un pago con monto, fecha y
referencia a la escritura. Ya no se derivan automáticamente ítems de la factura principal
(leyes notariales, impuestos, sellos, gastos administrativos).

**Why this priority**: El libro de salida es el registro de egresos reales hacia el Colegio.
Debe reflejar transferencias efectivas, no obligaciones proyectadas de la factura.

**Independent Test**: Se puede probar registrando pagos al Colegio en distintas escrituras
de un mes y verificando que el Libro de Salida del mes muestra solo esos pagos.

**Acceptance Scenarios**:

1. **Given** pagos al Colegio registrados en julio 2026, **When** la secretaria consulta
   el Libro de Salida de julio 2026, **Then** ve una línea por cada pago con: monto,
   fecha del pago, nombre de la escritura, y enlace navegable al detalle.

2. **Given** una escritura con leyes notariales calculadas en la factura pero sin pagos
   al Colegio registrados, **When** se consulta el Libro de Salida, **Then** esa escritura
   NO genera líneas de salida.

3. **Given** una escritura con saldo pendiente del cliente, **When** la secretaria registró
   un pago al Colegio en julio, **Then** ese pago SÍ aparece en el Libro de Salida de julio.

4. **Given** que se registra un nuevo pago al Colegio, **When** otra pestaña tiene abierto
   el Libro de Salida del mes, **Then** el libro se actualiza en tiempo real.

5. **Given** el Libro de Salida de un mes, **When** la secretaria lo consulta, **Then** el
   total del período es la suma de todos los pagos al Colegio registrados en ese mes (no
   totales proyectados de facturas).

---

### User Story 6 — Liquidación y Pago de Salarios Basados en Caja Real (Priority: P2)

La secretaria consulta la Liquidación Mensual y el Pago de Salarios del mes y ve montos
derivados exclusivamente de los **pagos reales** que ingresaron de clientes en ese período,
no de los totales proyectados de las facturas. Cada escritura con pagos en el mes aparece
como **una línea única** con el total cobrado, sin desglose por sección de factura
(honorarios, leyes, impuestos, etc.). Una escritura sin pagos en el mes no aporta a la
liquidación de ese mes, aunque exista en el sistema.

**Why this priority**: Sin este cambio, la plataforma seguiría mostrando dinero ficticio
en liquidación y salarios mientras los libros reflejan caja real. Alinear las tres vistas
es coherente con el principio de que solo hay plata cuando el cliente paga.

**Independent Test**: Se puede probar registrando pagos parciales en distintas escrituras
de un mes y verificando que Liquidación y Pago de Salarios reflejan solo esos montos
cobrados — no el total de la factura.

**Acceptance Scenarios**:

1. **Given** una escritura con costo total $1.000.000 y un pago de $400.000 en julio,
   **When** la secretaria consulta la Liquidación de julio, **Then** la escritura aparece
   como una línea única de $400.000 (sin desglose por honorarios, leyes ni impuestos).

2. **Given** una escritura con dos pagos en julio ($300.000 y $200.000), **When** la
   secretaria consulta la Liquidación de julio, **Then** la escritura aparece como una
   línea única de $500.000 (suma de pagos del mes).

3. **Given** una escritura sin pagos registrados en julio, **When** la secretaria consulta
   la Liquidación de julio, **Then** esa escritura NO aparece en el resumen del mes.

4. **Given** pagos registrados en julio en escrituras de un escribano, **When** la
   secretaria consulta Pago de Salarios de julio, **Then** ve las escrituras con sus
   montos cobrados en el mes (línea única por escritura) y el total del escribano es la
   suma de esos pagos.

5. **Given** que se registra un nuevo pago, **When** la secretaria tiene abierta la
   Liquidación del mes, **Then** los totales se actualizan en tiempo real.

---

### User Story 7 — Visualización de Saldo en Listado y Detalle de Escrituras (Priority: P3)

La secretaria puede ver el estado de cobro de cada escritura desde el listado general
y desde el detalle, sin necesidad de abrir el Libro de Entrada.

**Why this priority**: Mejora la operación diaria al dar visibilidad inmediata de qué
escrituras tienen deuda pendiente y cuáles están listas para cerrar.

**Independent Test**: Se puede probar abriendo el listado de escrituras y verificando
que cada fila muestra costo total, pagado y pendiente de forma consistente con el detalle.

**Acceptance Scenarios**:

1. **Given** el listado de escrituras, **When** la secretaria lo visualiza, **Then** cada
   escritura muestra: costo total, total pagado, saldo pendiente, e indicador visual de
   si está pagada al 100% o no.

2. **Given** el detalle de una escritura, **When** la secretaria lo abre, **Then** ve
   secciones separadas de "Pagos del Cliente" y "Pagos al Colegio", cada una con su
   historial y formulario de registro, más el resumen de saldo del cliente en la parte superior.

3. **Given** que se registra un pago en una escritura, **When** la secretaria está en el
   listado de escrituras, **Then** los montos de saldo se actualizan en tiempo real.

---

### Edge Cases

- ¿Cómo se distribuye un pago parcial en Liquidación? Como **montón único**: una línea
  por escritura con el total de pagos del mes, sin reparto proporcional ni por sección.
- ¿Qué sucede si se recalcula la factura y el nuevo costo total es menor que lo ya pagado?
  El sistema debe mostrar saldo pendiente $0 (sobrepago) y permitir cerrar la escritura,
  indicando visualmente que el cliente pagó de más.
- ¿Qué pasa con los gastos adicionales existentes en escrituras abiertas? Deben migrarse
  o eliminarse según política de migración; los nuevos registros solo aceptan pagos del
  cliente (sin campo dirección entrada/salida).
- ¿Se puede eliminar o editar un pago ya registrado? Los pagos son un registro append-only
  (sin edición ni eliminación) para preservar trazabilidad contable.
- ¿Qué ocurre si una escritura del mes anterior sigue abierta con deuda? Aparece en el
  resumen de deudas pendientes del Libro de Entrada del mes actual si se consulta, pero
  sus pagos se registran en el mes en que efectivamente ingresan.
- ¿Cómo se filtra el Libro de Entrada? Por mes calendario según la **fecha del pago**
  (no la fecha de creación de la escritura).
- ¿Cómo se filtra el Libro de Salida? Por mes calendario según la **fecha del pago al
  Colegio** (no la fecha de cierre de la escritura ni la fecha de creación).
- ¿Los pagos al Colegio dependen del cobro al cliente? **No** — son flujos disconexos;
  la escribanía puede pagar al Colegio aunque el cliente no haya saldado la escritura.
- ¿Se valida el monto del pago al Colegio contra las leyes notariales proyectadas? **No**
  — el total proyectado se muestra solo como referencia informativa; la secretaria registra
  el monto real sin restricciones.
- ¿Qué sucede con escrituras cerradas antes de esta feature que no tienen pagos registrados?
  Requieren migración de datos: o se asume pago completo implícito al cerrar, o se bloquea
  la visualización hasta completar la migración.

---

## Requirements *(mandatory)*

### Functional Requirements

**Pagos del Cliente**

- **FR-001**: El sistema DEBE reemplazar el concepto de "gasto adicional" (con dirección
  entrada/salida) por "pago del cliente", asociado exclusivamente a una escritura.
- **FR-002**: Cada pago del cliente DEBE registrar como mínimo: monto (positivo), fecha,
  y referencia a la escritura. El concepto/nota es opcional.
- **FR-003**: El sistema DEBE calcular y mostrar en todo momento para cada escritura:
  `costo_total` (total de la factura principal), `total_pagado` (suma de pagos), y
  `saldo_pendiente` (`costo_total − total_pagado`, mínimo $0).
- **FR-004**: El sistema DEBE rechazar pagos con monto ≤ 0 o monto mayor al saldo pendiente
  vigente al momento del registro.
- **FR-005**: Los pagos del cliente SOLO pueden registrarse en escrituras abiertas.
- **FR-006**: Los pagos del cliente DEBEN ser inmutables una vez registrados (sin edición
  ni eliminación).

**Cierre de Escritura**

- **FR-007**: El sistema DEBE permitir cerrar una escritura únicamente cuando
  `saldo_pendiente = 0`.
- **FR-008**: Al intentar cerrar una escritura con saldo pendiente > 0, el sistema DEBE
  bloquear la operación e informar el monto pendiente.
- **FR-009**: Las escrituras cerradas DEBEN conservar el comportamiento de inmutabilidad
  existente (solo lectura, sin nuevos pagos).

**Libro de Entrada**

- **FR-010**: El Libro de Entrada DEBE contener exclusivamente pagos del cliente recibidos;
  NO debe derivar automáticamente honorarios, certificación ni otros ítems de la factura.
- **FR-011**: Cada línea del Libro de Entrada DEBE incluir: monto del pago, fecha del pago,
  nombre de la escritura, y enlace navegable al detalle de la escritura.
- **FR-012**: El Libro de Entrada DEBE mostrar un resumen de deuda por escritura afectada
  en el período: costo total, total pagado acumulado, y saldo pendiente actual.
- **FR-013**: El Libro de Entrada DEBE filtrarse por mes calendario según la fecha del pago.
- **FR-014**: El Libro de Entrada DEBE mostrar el total de pagos recibidos en el período.
- **FR-015**: El Libro de Entrada DEBE actualizarse en tiempo real ante registro de nuevos
  pagos.

**Pagos al Colegio de Escribanos**

- **FR-016**: Cada escritura DEBE exponer una sección "Pagos al Colegio" para registrar
  manualmente los pagos que la escribanía efectúa al Colegio de Escribanos.
- **FR-017**: Cada pago al Colegio DEBE registrar como mínimo: monto (positivo), fecha,
  y referencia a la escritura. El concepto/nota es opcional.
- **FR-018**: Los pagos al Colegio DEBEN ser independientes del estado de cobro del cliente
  (saldo pendiente); NO deben validarse contra el saldo del cliente ni contra montos
  proyectados de leyes notariales en la factura.
- **FR-018b**: La sección "Pagos al Colegio" DEBE mostrar el **total de leyes notariales
  proyectadas** de la factura principal como referencia informativa, sin validar ni bloquear
  el monto ingresado por la secretaria.
- **FR-019**: Los pagos al Colegio SOLO pueden registrarse en escrituras abiertas.
- **FR-020**: Los pagos al Colegio DEBEN ser inmutables una vez registrados (sin edición
  ni eliminación).

**Libro de Salida**

- **FR-021**: El Libro de Salida DEBE contener exclusivamente pagos al Colegio registrados
  manualmente; NO debe derivar automáticamente ítems de la factura principal (leyes
  notariales, impuestos, sellos, gastos administrativos).
- **FR-022**: Cada línea del Libro de Salida DEBE incluir: monto del pago, fecha del pago,
  nombre de la escritura, y enlace navegable al detalle de la escritura.
- **FR-023**: El Libro de Salida DEBE filtrarse por mes calendario según la fecha del
  pago al Colegio.
- **FR-024**: El Libro de Salida DEBE mostrar el total de pagos al Colegio en el período.
- **FR-025**: El Libro de Salida DEBE actualizarse en tiempo real ante registro de nuevos
  pagos al Colegio.

**Liquidación y Pago de Salarios**

- **FR-026**: La Liquidación Mensual DEBE calcularse exclusivamente a partir de los pagos
  reales del cliente recibidos en el mes calendario (fecha del pago), no a partir de los
  totales proyectados de la factura principal.
- **FR-026b**: Cada escritura con pagos en el mes DEBE aparecer en la Liquidación como
  **una línea única** con el total de pagos recibidos en ese mes, sin desglose por sección
  de factura (honorarios, leyes notariales, impuestos, gastos administrativos).
- **FR-027**: Una escritura sin pagos en el mes filtrado NO DEBE aparecer en la Liquidación
  de ese mes.
- **FR-028**: El Pago de Salarios DEBE mostrar por escribano las escrituras con pagos en
  el mes, cada una como línea única con el total cobrado; el importe del escribano es la
  suma de los pagos del mes de sus escrituras asignadas.
- **FR-029**: La Liquidación y el Pago de Salarios DEBEN actualizarse en tiempo real ante
  registro de nuevos pagos del cliente.

**Visualización**

- **FR-030**: El listado de escrituras DEBE mostrar costo total, total pagado y saldo
  pendiente para cada escritura.
- **FR-031**: El detalle de escritura DEBE reemplazar la sección "Gastos Adicionales" por
  secciones separadas "Pagos del Cliente" y "Pagos al Colegio", cada una con historial
  y formulario de registro; la sección "Pagos al Colegio" incluye referencia informativa
  al total de leyes notariales proyectadas de la factura.
- **FR-032**: El detalle de escritura DEBE mostrar un indicador claro de si la escritura
  está pagada al 100% y puede cerrarse.

**Migración y Compatibilidad**

- **FR-033**: El sistema DEBE migrar o convertir los gastos adicionales existentes con
  dirección "entrada" a pagos del cliente, preservando monto, fecha y concepto.
- **FR-034**: Los gastos adicionales existentes con dirección "salida" DEBEN migrarse a
  pagos al Colegio, preservando monto, fecha y concepto.
- **FR-035**: Las escrituras cerradas antes de la migración DEBEN tratarse como pagadas
  al 100% por el cliente (pago implícito por el monto total de la factura al momento del
  cierre) para no bloquear operaciones históricas.

### Key Entities

- **PagoCliente**: registro de un pago real efectuado por el cliente contra una Escritura;
  contiene monto, fecha, concepto opcional, y referencia a la escritura. Reemplaza a
  GastoAdicional con dirección "entrada".
- **PagoColegio**: registro manual de un pago que la escribanía efectúa al Colegio de
  Escribanos por una Escritura; contiene monto, fecha, concepto opcional, y referencia a
  la escritura. Independiente del estado de cobro del cliente. Reemplaza a GastoAdicional
  con dirección "salida".
- **Escritura** (modificada): además de sus atributos actuales, expone costo total,
  total pagado (cliente) y saldo pendiente como valores calculados derivados de la factura
  y los pagos del cliente.
- **EntradaLibro** (redefinida): línea del Libro de Entrada que representa un PagoCliente
  con referencia a la escritura y contexto de deuda pendiente.
- **SalidaLibro** (redefinida): línea del Libro de Salida que representa un PagoColegio
  registrado manualmente con referencia a la escritura.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: La secretaria puede registrar un pago del cliente y ver el saldo pendiente
  actualizado en menos de 3 segundos, sin recargar la página.
- **SC-002**: El 100% de los intentos de cierre de escrituras con saldo pendiente > 0
  son bloqueados con un mensaje que indica el monto faltante.
- **SC-003**: El 100% de las líneas del Libro de Entrada corresponden a pagos reales del
  cliente (ninguna línea derivada automáticamente de honorarios o certificación).
- **SC-004**: El 100% de las líneas del Libro de Salida corresponden a pagos al Colegio
  registrados manualmente (ninguna línea derivada automáticamente de la factura).
- **SC-005**: El saldo pendiente mostrado en listado, detalle y Libro de Entrada es
  consistente (mismo valor) para la misma escritura en todo momento.
- **SC-006**: Los Libros de Entrada y Salida se actualizan en tiempo real (menos de
  2 segundos) ante registro de pagos del cliente o pagos al Colegio.
- **SC-007**: Las escrituras migradas desde la versión anterior conservan su historial
  financiero sin pérdida de datos ni bloqueo operativo.
- **SC-008**: El 100% de los montos en Liquidación y Pago de Salarios corresponden a
  pagos reales del cliente del período, nunca a totales proyectados de facturas sin cobrar.

---

## Testing Strategy

**Approach**: TDD — Test-Driven Development completo.

**Rationale**: La feature modifica cálculos de saldo, reglas de cierre, liquidación y
libros contables — superficies críticas de integridad financiera donde los tests deben
escribirse antes de la implementación.

**Scope note**: Esta decisión DEBE ser respetada por `/spec-kitti.plan` (contratos de test)
y `/spec-kitti.tasks` (tareas TDD / unit-test generadas en consecuencia).

**Scope específico de esta feature**:

- **Pagos del Cliente**: tests de registro, validación de montos (cero, negativo,
  exceso sobre saldo), inmutabilidad, y recálculo de saldo ante cambio de factura.
- **Cierre condicionado**: tests que verifican bloqueo con saldo pendiente > 0 y éxito
  con saldo = 0.
- **Liquidación y Pago de Salarios**: tests de montón único por escritura, exclusión de
  escrituras sin pagos en el mes, y totales por escribano basados en caja real.
- **Pagos al Colegio**: tests de registro independiente del saldo del cliente, validación
  de montos, inmutabilidad, rechazo en escrituras cerradas, y presencia de referencia
  informativa de leyes notariales proyectadas sin efecto de validación.
- **Libros Contables**: tests de derivación del Libro de Entrada (solo pagos del cliente +
  resumen de deuda) y Libro de Salida (solo pagos al Colegio registrados manualmente).
- **Migración**: tests de conversión de gastos adicionales "entrada" → pagos del cliente
  y "salida" → pagos al Colegio; pago implícito al 100% para escrituras cerradas pre-migración.
- **Tiempo real**: tests de integración/SSE para actualización de saldos, libros y
  liquidación ante registro de pagos o cierre de escrituras.

---

## Assumptions

- El **costo total** de una escritura es el `total_factura` de la factura principal
  (incluye honorarios, leyes notariales, impuestos, gastos administrativos y todo concepto
  facturado al cliente).
- Los **pagos al Colegio de Escribanos** se registran manualmente por la secretaria en cada
  escritura, de forma independiente del cobro al cliente. El Libro de Salida refleja
  exclusivamente estos pagos reales (fecha del pago al Colegio).
- La **Liquidación Mensual** y el **Pago de Salarios** se recalculan en esta feature para
  basarse exclusivamente en pagos reales del cliente recibidos en el mes (fecha del pago),
  alineados con el principio de caja real.
- La sección de Configuración, cotizaciones, escribanos y empleados no se modifica en
  esta feature.
- Los pagos del cliente y los pagos al Colegio son flujos de caja **disconexos**: no hay
  validación cruzada entre ambos. El total de leyes notariales proyectadas en la factura
  se muestra en la sección "Pagos al Colegio" únicamente como **referencia informativa**.
- La migración de datos existentes es responsabilidad de esta feature y debe ejecutarse
  de forma idempotente al desplegar.
- **No se utiliza Figma** para el diseño de UI de esta feature; se reutilizan patrones y
  estilos del frontend existente (features 001 y 002).

---

## Clarifications

### Session 2026-07-20

- Q: ¿Cómo debe comportarse la Liquidación Mensual y el Pago de Salarios respecto a los pagos reales del cliente? → A: Liquidación y Pago de Salarios basados en **pagos reales** recibidos (no en totales proyectados de la factura).
- Q: Con pagos parciales, ¿cómo se distribuye el monto cobrado en la Liquidación? → A: **Montón único** — cada escritura aparece como una línea con el total de pagos del mes, sin desglose por sección de factura.
- Q: ¿Qué estrategia de testing aplica a esta feature? → A: **TDD completo** — tests escritos antes de la implementación en todo el scope de la feature.
- Q: ¿Cuándo deben aparecer los ítems del Colegio de Escribanos en el Libro de Salida? → A: **Registro manual** — cada escritura tiene una sección "Pagos al Colegio" donde la secretaria registra los pagos que hace la escribanía, independientemente de si el cliente pagó o no (flujos disconexos).
- Q: Al registrar un pago al Colegio, ¿el sistema debe mostrar el total de leyes notariales proyectadas en la factura como referencia? → A: **Referencia informativa** — mostrar el total proyectado como guía, sin validar ni bloquear el monto ingresado.
- Q: ¿Se usa Figma para las tareas de UI de esta feature? → A: **No** — UI implementada según spec y design system existente del proyecto; sin referencias Figma ni campo `figma:` en tasks.
