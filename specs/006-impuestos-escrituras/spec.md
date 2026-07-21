# Feature Specification: Impuestos por Escritura

**Feature Branch**: `006-impuestos-escrituras`  
**Created**: 2026-07-20  
**Status**: Draft  
**Input**: User description: "Solapa impuestos en detalle de escritura para cargar gastos de API, TGI, Aguas Santafesinas, EPE, Expensas y Litoral Gas con período, prorrateo y botones de pago cliente y pago escribanía que registran en libro de entrada y libro de salida; una escritura no puede cerrarse si el balance de impuestos (pagado por cliente menos pagado por escribanía) no es cero"

## Clarifications

### Session 2026-07-20

- Q: ¿Aplicar TDD y/o unit tests estrictos para esta feature? → A: **TDD completo** — tests escritos antes de la implementación en todo el scope.
- Q: ¿Qué pasa al cerrar con impuestos cargados sin pagos completos? → A: **Bloquear cierre** — cada impuesto cargado debe tener pago cliente y pago escribanía registrados.
- Q: ¿Política de modificación de impuestos y pagos? → A: **Todo editable** — impuestos y pagos se pueden editar en cualquier momento mientras la escritura esté abierta.
- Q: ¿Impacto en Liquidación y Pago de Salarios? → A: **Corregido** — sí impactan Liquidación y Pago de Salarios del escribano asignado según movimientos reales del mes; el balance = $0 solo se exige al **cerrar la escritura**, no al cerrar el mes.
- Q: ¿Rol de la fecha de prorrateo? → A: **Fecha de corte** con prorrateo **lineal por días** sobre el período; la dirección (hacia atrás / hacia adelante) determina el tramo y el **monto sugerido** que debe abonar el cliente; es control independiente del ciclo de la escritura.
- Q: ¿Cómo se reparte la fecha de corte entre tramos? → A: **Sin solapamiento** — hacia atrás: inicio → corte (incl.); hacia adelante: (corte + 1 día) → fin (incl.).

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Cargar Impuestos en el Detalle de una Escritura (Priority: P1)

La secretaria abre el detalle de una escritura y, en la columna derecha (debajo de "Pagos del
cliente" y "Pagos de la escribanía"), encuentra la nueva sección **Impuestos**. Desde allí
registra gastos impositivos y de servicios del **inmueble** vinculado a esa escritura. Es un
módulo de **control de caja** independiente del ciclo de honorarios: el período del impuesto
puede no coincidir con la fecha de apertura de la escritura (ej. escritura abierta en junio,
impuesto con período mayo–junio).

**Why this priority**: Sin el alta de impuestos no hay base para registrar los pagos ni
reflejarlos en los libros contables. Es el punto de entrada de toda la feature.

**Independent Test**: Se puede probar abriendo una escritura abierta, cargando un impuesto
de cualquier tipo con período y prorrateo, y verificando que aparece en el listado de la
sección Impuestos — sin registrar aún pagos del cliente ni de la escribanía.

**Acceptance Scenarios**:

1. **Given** el detalle de una escritura en viewport de escritorio, **When** la secretaria
   visualiza la columna derecha, **Then** ve en orden vertical: "Pagos del cliente", "Pagos de
   la escribanía" e "Impuestos" (esta última debajo de las dos anteriores).

2. **Given** la sección Impuestos de una escritura abierta, **When** la secretaria registra
   un impuesto, **Then** debe elegir obligatoriamente: tipo de impuesto, monto total del
   período, fecha de inicio del período, fecha de fin del período, fecha de corte para
   prorrateo y dirección (hacia atrás o hacia adelante).

3. **Given** el formulario de alta de impuesto, **When** la secretaria despliega el selector
   de tipo, **Then** las opciones disponibles son exactamente: API, TGI, Aguas Santafesinas,
   EPE, Expensas y Litoral Gas.

4. **Given** un impuesto registrado, **When** la secretaria revisa el listado de Impuestos,
   **Then** ve el tipo, monto total, período (inicio–fin), fecha de corte, dirección, monto
   prorrateado sugerido para el cliente y estado de pagos (cliente y/o escribanía).

5. **Given** un intento de registro con fecha de fin anterior a fecha de inicio, monto cero
   o negativo, o campos obligatorios vacíos, **When** la secretaria confirma, **Then** el
   sistema rechaza el registro con mensaje de validación claro.

6. **Given** una escritura cerrada, **When** la secretaria intenta registrar o modificar
   impuestos, **Then** el sistema bloquea la operación de la misma forma que bloquea otros
   movimientos en escrituras cerradas.

---

### User Story 2 — Prorratear el Monto según Período, Fecha de Corte y Dirección (Priority: P1)

Para cada impuesto cargado, la secretaria define el período de facturación del servicio
(fecha de inicio y fin), el **monto total** del impuesto y una **fecha de corte** para
prorratear. Con dirección **hacia atrás**, el tramo va desde el inicio del período hasta la
fecha de corte (inclusive). Con **hacia adelante**, desde el día **siguiente** a la fecha de
corte hasta el fin del período (inclusive). Los tramos no se solapan y, para un mismo
período, suman el 100% de los días. El sistema calcula de forma **lineal por días** el monto
que corresponde al cliente sobre el monto total del período y lo muestra como referencia al
registrar el pago.

**Why this priority**: El prorrateo determina cuánto debe abonar el cliente a la escribanía
antes de que la escribanía pague el servicio; es la regla de negocio central del módulo.

**Independent Test**: Se puede probar con un impuesto de $10.000, período 01/05–30/06 (61 días)
y fecha de corte 15/06: hacia atrás debe sugerir ≈ $8.197 (46/61 del total); hacia adelante
≈ $1.803 (15/61).

**Acceptance Scenarios**:

1. **Given** un impuesto de $10.000 con período 01/05/2026–30/06/2026 (61 días) y fecha de
   corte 15/06/2026 con dirección "hacia atrás", **When** la secretaria visualiza el
   impuesto, **Then** el monto prorrateado sugerido para el cliente es $10.000 × (46/61)
   (tramo del 01/05 al 15/06 inclusive).

2. **Given** el mismo impuesto con dirección "hacia adelante", **When** la secretaria
   visualiza el impuesto, **Then** el monto sugerido es $10.000 × (15/61) (tramo del
   16/06 al 30/06 inclusive, sin incluir el día de corte).

3. **Given** un impuesto cargado, **When** la secretaria visualiza su detalle, **Then** ve
   claramente período, fecha de corte, dirección y monto prorrateado sugerido.

4. **Given** un impuesto sin pagos registrados, **When** la secretaria cambia período, fecha
   de corte o dirección, **Then** el monto prorrateado sugerido se recalcula al instante.

5. **Given** un intento de registro con fecha de corte fuera del rango del período,
   **When** la secretaria confirma, **Then** el sistema rechaza el registro con mensaje claro.

---

### User Story 3 — Registrar Pago del Cliente a la Escribanía (Priority: P1)

Desde cada impuesto cargado, la secretaria puede registrar el **pago del cliente** a la
escribanía por ese concepto. El sistema sugiere el monto prorrateado pero permite editarlo.
Al confirmar, genera una línea en el **Libro de Entrada** del mes calendario de la **fecha de
pago**, vinculada a la escritura y al tipo de impuesto.

**Why this priority**: El cobro al cliente es mitad del flujo de caja y alimenta el Libro de
Entrada, pieza central del control financiero.

**Independent Test**: Se puede probar registrando solo el pago del cliente sobre un impuesto
y verificando la línea en Libro de Entrada del mes correcto, sin registrar pago de la
escribanía.

**Acceptance Scenarios**:

1. **Given** un impuesto cargado sin pago del cliente, **When** la secretaria pulsa "Pago
   cliente", **Then** el formulario precarga el monto prorrateado sugerido y permite editarlo
   antes de confirmar con fecha de pago.

2. **Given** un pago del cliente registrado con fecha en julio 2026, **When** la secretaria
   consulta el Libro de Entrada de julio 2026, **Then** ve una línea con monto, fecha de
   pago, referencia a la escritura, tipo de impuesto e identificación como pago de impuesto.

3. **Given** un pago del cliente registrado en julio, **When** la secretaria consulta el
   Libro de Entrada de agosto, **Then** esa línea no aparece en agosto.

4. **Given** un intento de pago del cliente con monto cero o negativo, **When** confirma,
   **Then** el sistema rechaza el registro.

5. **Given** un pago del cliente ya registrado para un impuesto, **When** la secretaria edita
   su monto o fecha de pago, **Then** el sistema actualiza el registro, el Libro de Entrada y
   el balance de impuestos en tiempo real (no se crea un segundo pago).

---

### User Story 4 — Registrar Pago de la Escribanía al Servicio (Priority: P1)

Desde cada impuesto cargado, la secretaria puede registrar el **pago de la escribanía** al
organismo o proveedor del servicio. El sistema genera una línea en el **Libro de Salida** del
mes calendario de la **fecha de pago**, vinculada a la escritura y al tipo de impuesto.

**Why this priority**: El egreso de la escribanía completa el flujo de caja y alimenta el
Libro de Salida con la misma lógica que los pagos de escribanía existentes.

**Independent Test**: Se puede probar registrando solo el pago de la escribanía y
verificando la línea en Libro de Salida del mes correcto, sin que el cliente haya pagado.

**Acceptance Scenarios**:

1. **Given** un impuesto cargado sin pago de la escribanía, **When** la secretaria pulsa
   "Pago escribanía" e ingresa monto positivo y fecha de pago, **Then** el impuesto queda
   marcado con pago de la escribanía registrado.

2. **Given** un pago de la escribanía registrado con fecha en julio 2026, **When** la
   secretaria consulta el Libro de Salida de julio 2026, **Then** ve una línea con monto,
   fecha de pago, referencia a la escritura, tipo de impuesto e identificación como pago de
   impuesto.

3. **Given** un impuesto con pago del cliente en julio pero sin pago de la escribanía,
   **When** la secretaria consulta Liquidación de julio, **Then** el neto de impuestos de
   esa escritura es positivo; el balance acumulado de la escritura puede ser ≠ $0 mientras
   permanezca abierta.

4. **Given** un impuesto con pago de la escribanía pero sin pago del cliente, **When** la
   secretaria registra el pago del cliente posteriormente, **Then** ambos quedan registrados
   en cualquier orden; el balance acumulado debe ser $0 para cerrar la escritura.

5. **Given** un pago de la escribanía ya registrado, **When** la secretaria edita su monto
   o fecha de pago, **Then** el sistema actualiza el registro, el Libro de Salida y el balance
   de impuestos en tiempo real (no se crea un segundo pago).

---

### User Story 5 — Cerrar Escritura Solo con Balance de Impuestos en Cero (Priority: P1)

La secretaria solo puede cerrar una escritura cuando el **balance de impuestos** de esa
escritura es cero: la suma de todos los pagos del cliente por impuestos menos la suma de
todos los pagos de la escribanía por impuestos debe ser exactamente $0. Si el balance es
distinto de cero, el cierre se bloquea con un mensaje que indica el monto desbalanceado.

**Why this priority**: Garantiza que no queden impuestos con cobros o egresos pendientes de
compensar antes de archivar la escritura.

**Independent Test**: Se puede probar con una escritura que cumple el saldo de honorarios
pero tiene distintos niveles de pago en impuestos, verificando que solo permite el cierre
cuando ambos totales coinciden.

**Acceptance Scenarios**:

1. **Given** una escritura con impuestos cuyos pagos del cliente suman $150.000 y cuyos pagos
   de la escribanía suman $150.000, **When** la secretaria solicita cerrar la escritura
   (y el saldo de honorarios es $0), **Then** el cierre se permite.

2. **Given** una escritura con pagos del cliente por impuestos de $150.000 y pagos de la
   escribanía de $100.000, **When** la secretaria intenta cerrarla, **Then** el sistema
   bloquea el cierre e informa que el balance de impuestos es $50.000 (a favor del cliente
   o pendiente de egreso de la escribanía).

3. **Given** una escritura con pagos de la escribanía por impuestos mayores que los pagos del
   cliente, **When** la secretaria intenta cerrarla, **Then** el sistema bloquea el cierre e
   informa el balance negativo (exceso de egreso sobre cobro).

4. **Given** una escritura sin registros de impuestos, **When** la secretaria solicita
   cerrarla, **Then** el balance de impuestos se considera $0 y no bloquea el cierre por
   este concepto.

5. **Given** una escritura con un impuesto cargado pero sin ambos pagos registrados (falta
   pago del cliente, pago de la escribanía, o ambos), **When** la secretaria intenta
   cerrarla, **Then** el sistema bloquea el cierre e informa qué impuestos tienen pagos
   pendientes.

6. **Given** una escritura con balance de impuestos en cero y todos los impuestos cargados
   con pago cliente y pago escribanía registrados, **When** la secretaria registra un nuevo
   pago que desbalancea los totales, **Then** el sistema muestra el nuevo balance distinto
   de cero y bloquea el cierre hasta regularizar.

7. **Given** el detalle de una escritura abierta con impuestos, **When** la secretaria
   visualiza la sección Impuestos o el encabezado de la escritura, **Then** ve el balance
   de impuestos actual (total pagado por cliente, total pagado por escribanía y diferencia).

8. **Given** una escritura abierta con pagos de impuestos desbalanceados en un mes,
   **When** la secretaria consulta Liquidación o Pago de Salarios de ese mes, **Then** el
   cierre mensual **no** se bloquea por impuestos; solo el cierre de la escritura exige
   balance = $0.

---

### User Story 6 — Impacto de Impuestos en Liquidación y Pago de Salarios (Priority: P1)

Al cerrar un **mes**, la Liquidación y el Pago de Salarios **no exigen** que el balance de
impuestos de cada escritura sea cero. Los movimientos reales de impuestos del mes impactan al
**escribano asignado** a cada escritura: cobros del cliente sin egreso correspondiente en el
mes representan plata a favor de la escribanía; egresos de la escribanía sin cobro del
cliente representan pérdida en ese mes.

**Why this priority**: Refleja la caja real mensual del escribano mientras la escritura sigue
abierta; es distinto del control de cierre de escritura.

**Independent Test**: Con una escritura donde el cliente pagó un impuesto en julio pero la
escribanía aún no pagó el servicio, verificar que julio muestra el ingreso en Liquidación y
Pago de Salarios del escribano, sin bloquear el cierre del mes.

**Acceptance Scenarios**:

1. **Given** un pago del cliente por impuesto de $50.000 en julio sin pago de la escribanía
   en julio, **When** la secretaria consulta Liquidación de julio del escribano asignado,
   **Then** el neto de impuestos de esa escritura aporta +$50.000 al mes (plata a favor de
   la escribanía).

2. **Given** un pago de la escribanía por impuesto de $50.000 en julio sin cobro del cliente
   en julio, **When** la secretaria consulta Liquidación de julio, **Then** el neto aporta
   −$50.000 (pérdida de la escribanía en el mes).

3. **Given** pagos del cliente y de la escribanía por el mismo monto en el mismo mes,
   **When** la secretaria consulta Liquidación de ese mes, **Then** el neto de impuestos de
   esa escritura es $0 para ese mes (se compensan).

4. **Given** movimientos de impuestos en julio, **When** la secretaria consulta Pago de
   Salarios de julio del escribano asignado, **Then** el importe del escribano incorpora el
   neto de impuestos (Σ cobros cliente − Σ egresos escribanía por impuestos) de sus
   escrituras en ese mes, además de los honorarios por caja real.

5. **Given** una escritura con balance de impuestos ≠ $0, **When** la secretaria cierra el
   mes en Liquidación, **Then** el cierre mensual se permite; el desbalance solo impide
   **cerrar la escritura**.

---

### User Story 7 — Editar y Eliminar Impuestos y Pagos (Priority: P2)

Mientras la escritura permanezca abierta, la secretaria puede corregir cualquier dato de
impuestos cargados y de sus pagos asociados. Los cambios se reflejan de inmediato en libros
contables, balance de impuestos y elegibilidad de cierre.

**Why this priority**: Permite corregir errores operativos sin flujos de anulación separados;
complementa el registro inicial sin bloquear el cierre diario.

**Independent Test**: Se puede probar editando monto de un pago ya registrado y verificando
que el Libro de Entrada/Salida y el balance se actualizan sin duplicar líneas.

**Acceptance Scenarios**:

1. **Given** un impuesto sin pagos registrados, **When** la secretaria edita tipo, monto
   total, período, fecha de corte o dirección, **Then** el listado y el monto prorrateado
   sugerido reflejan los nuevos valores.

2. **Given** un impuesto sin pagos registrados, **When** la secretaria lo elimina, **Then**
   desaparece del listado y deja de exigirse para el cierre.

3. **Given** un impuesto con pagos registrados, **When** la secretaria edita un pago del
   cliente o de la escribanía, **Then** la línea en el libro contable, Liquidación y Pago de
   Salarios se actualizan (mismo registro, sin duplicar) y el balance se recalcula.

4. **Given** un impuesto con ambos pagos registrados, **When** la secretaria elimina uno de
   los pagos, **Then** el libro contable deja de mostrar esa línea, el impuesto queda con
   pago pendiente y el cierre se bloquea hasta completar nuevamente.

5. **Given** una escritura cerrada, **When** la secretaria intenta editar o eliminar
   impuestos o pagos, **Then** el sistema bloquea la operación.

---

### User Story 8 — Consultar Impuestos en Layout Responsive (Priority: P2)

En viewports estrechos, la sección Impuestos se apila debajo de pagos del cliente y pagos de
la escribanía, manteniendo toda la funcionalidad accesible.

**Why this priority**: Asegura usabilidad sin bloquear los flujos contables principales.

**Independent Test**: Se puede probar reduciendo el ancho de ventana y verificando el orden
de apilamiento y la accesibilidad de formularios y botones de pago.

**Acceptance Scenarios**:

1. **Given** un viewport estrecho, **When** la secretaria visualiza el detalle de escritura,
   **Then** el orden de secciones es: saldo y datos, factura principal, pagos del cliente,
   pagos de la escribanía, impuestos.

2. **Given** viewport estrecho con sección Impuestos visible, **When** la secretaria registra
   un impuesto o un pago, **Then** los formularios y botones "Pago cliente" y "Pago
   escribanía" permanecen usables sin solapamiento.

---

### Edge Cases

- ¿Período del impuesto vs. fecha de apertura de la escritura? Independientes; una escritura
  abierta en junio puede tener impuestos con período mayo–junio.
- ¿Período que cruza años? El prorrateo lineal por días aplica igual; los libros filtran por
  mes de la fecha de pago de cada movimiento.
- ¿Fecha de corte en el límite del período? Si la fecha de corte es el último día del período,
  "hacia adelante" tiene tramo de 0 días y monto sugerido $0; si es el primer día, "hacia
  atrás" tiene un solo día. La fecha de corte debe estar dentro del período (FR-005).
- ¿Múltiples impuestos del mismo tipo en una escritura? Permitido si corresponden a períodos
  distintos; el listado los diferencia por período y fecha de corte.
- ¿Monto del pago distinto al monto prorrateado sugerido? Permitido (editable); el balance
  global cliente − escribanía debe ser $0 para cerrar la escritura.
- ¿Cierre de mes con balance impuestos ≠ 0? Permitido; Liquidación y Salarios reflejan el
  neto del mes; solo el **cierre de escritura** exige balance = $0.
- ¿Cliente pagó pero escribanía no (o viceversa) en un mes? Impacta Liquidación y Salarios del
  escribano asignado; genera línea en Libro de Entrada o Salida según corresponda.
- ¿Puede cerrarse la escritura con impuestos cargados sin pagos completos? No; cada impuesto
  cargado debe tener pago del cliente y pago de la escribanía registrados, además de balance
  global = $0 y saldo de honorarios = $0.
- ¿Impuesto cargado en escritura cerrada antes del cierre? Los pagos ya registrados
  permanecen en libros; no se permiten nuevas altas ni modificaciones tras el cierre.
- ¿Actualización en tiempo real? Al registrar, editar o eliminar pagos e impuestos, libros,
  Liquidación, Pago de Salarios, balance y elegibilidad de cierre deben actualizarse sin
  recargar la página.
- ¿Se pueden editar impuestos y pagos? Sí, mientras la escritura esté abierta; en escrituras
  cerradas todo queda en solo lectura.

---

## Requirements *(mandatory)*

### Functional Requirements

**Ubicación y tipos**

- **FR-001**: El detalle de escritura DEBE incluir la sección "Impuestos" en la columna
  derecha, debajo de "Pagos del cliente" y "Pagos de la escribanía".
- **FR-002**: El sistema DEBE permitir registrar impuestos con tipo elegido entre: API, TGI,
  Aguas Santafesinas, EPE, Expensas y Litoral Gas.
- **FR-003**: Cada registro de impuesto DEBE estar vinculado a una única escritura.

**Datos del impuesto**

- **FR-004**: Cada impuesto DEBE incluir: tipo, monto total del período, fecha de inicio del
  período, fecha de fin del período, fecha de corte para prorrateo y dirección (hacia atrás |
  hacia adelante).
- **FR-005**: El sistema DEBE validar que la fecha de fin del período no sea anterior a la
  fecha de inicio y que la fecha de corte esté dentro del período (inclusive).
- **FR-006**: El sistema DEBE rechazar montos cero o negativos y campos obligatorios vacíos.
- **FR-007**: En escrituras cerradas, el sistema DEBE impedir alta, edición y eliminación de
  impuestos y sus pagos, con el mismo criterio que el resto de movimientos de la escritura.

**Prorrateo lineal**

- **FR-008**: El sistema DEBE calcular el monto prorrateado sugerido para el cliente como:
  `monto_total × (días_del_tramo / días_del_período)`, donde los días se cuentan de forma
  inclusiva en ambos extremos del tramo.
- **FR-009**: Con dirección "hacia atrás", el tramo DEBE ir desde la fecha de inicio del
  período hasta la fecha de corte (ambas inclusive).
- **FR-010**: Con dirección "hacia adelante", el tramo DEBE ir desde el día **siguiente** a
  la fecha de corte hasta la fecha de fin del período (inclusive); la fecha de corte NO debe
  contarse en este tramo.
- **FR-010a**: Los tramos hacia atrás y hacia adelante del mismo período NO deben solaparse;
  juntos deben cubrir el 100% de los días del período.
- **FR-010b**: El sistema DEBE mostrar el monto prorrateado sugerido al cargar el impuesto y
  al abrir el formulario "Pago cliente"; el monto efectivo del pago DEBE ser editable.

**Libros contables (fecha de pago)**

- **FR-010c**: Las líneas de Libro de Entrada y Libro de Salida por impuestos DEBEN filtrarse
  por mes calendario según la **fecha de pago** del movimiento (criterio de caja real, alineado
  con feature 003).

**Pago del cliente**

- **FR-011**: Cada impuesto DEBE ofrecer la acción "Pago cliente" para registrar el cobro del
  cliente a la escribanía por ese concepto.
- **FR-012**: Al registrar pago del cliente, el sistema DEBE crear una línea en el Libro de
  Entrada del mes calendario de la fecha de pago.
- **FR-013**: Cada línea de Libro de Entrada por impuesto DEBE incluir: monto, fecha de pago,
  referencia a la escritura, tipo de impuesto e identificación como pago de impuesto.
- **FR-014**: Solo DEBE existir un pago del cliente por registro de impuesto; ese pago DEBE
  ser editable (monto y fecha) mientras la escritura esté abierta.

**Pago de la escribanía**

- **FR-015**: Cada impuesto DEBE ofrecer la acción "Pago escribanía" para registrar el egreso
  de la escribanía al servicio u organismo correspondiente.
- **FR-016**: Al registrar pago de la escribanía, el sistema DEBE crear una línea en el Libro
  de Salida del mes calendario de la fecha de pago.
- **FR-017**: Cada línea de Libro de Salida por impuesto DEBE incluir: monto, fecha de pago,
  referencia a la escritura, tipo de impuesto e identificación como pago de impuesto.
- **FR-018**: Solo DEBE existir un pago de la escribanía por registro de impuesto; ese pago
  DEBE ser editable (monto y fecha) mientras la escritura esté abierta.

**Edición y eliminación**

- **FR-027**: Mientras la escritura esté abierta, el sistema DEBE permitir editar todos los
  campos de un impuesto cargado (tipo, monto total, período, fecha de corte, dirección).
- **FR-028**: Mientras la escritura esté abierta, el sistema DEBE permitir eliminar un
  impuesto que no tenga pagos registrados.
- **FR-029**: Mientras la escritura esté abierta, el sistema DEBE permitir editar y eliminar
  pagos del cliente y de la escribanía asociados a un impuesto.
- **FR-030**: Al editar un pago, el sistema DEBE actualizar la línea existente en el libro
  contable correspondiente sin crear duplicados.
- **FR-031**: Al eliminar un pago, el sistema DEBE quitar la línea del libro contable y
  recalcular balance y elegibilidad de cierre.
- **FR-032**: Al editar período, fecha de corte o dirección de un impuesto, el sistema DEBE
  recalcular el monto prorrateado sugerido; si hay pagos registrados, DEBE actualizar libros
  y Liquidación si cambia la fecha de pago editada.

**Liquidación, honorarios y cierre de escritura**

- **FR-019**: Los pagos del cliente y de la escribanía por impuestos DEBEN poder registrarse
  en cualquier orden; el monto efectivo de cada pago es editable.
- **FR-020**: Los pagos de impuestos NO DEBEN modificar el saldo pendiente de honorarios de la
  factura principal (son movimientos de caja separados del cobro de honorarios).
- **FR-020b**: La Liquidación Mensual y el Pago de Salarios DEBEN incorporar, por cada
  escritura y mes, el neto de impuestos: Σ pagos del cliente por impuestos del mes − Σ pagos
  de la escribanía por impuestos del mes, imputado al **escribano asignado** a esa escritura.
- **FR-020c**: El cierre de un **mes** en Liquidación NO DEBE exigir balance de impuestos = $0
  por escritura; las asimetrías mensuales (cobro sin egreso o egreso sin cobro) DEBEN
  reflejarse en el neto del escribano.
- **FR-023**: El sistema DEBE calcular el balance de impuestos de una escritura (acumulado) como:
  Σ pagos del cliente por impuestos − Σ pagos de la escribanía por impuestos.
- **FR-024**: El sistema DEBE mostrar en el detalle de la escritura el balance de impuestos
  (totales y diferencia) de forma visible mientras la escritura esté abierta.
- **FR-025**: El sistema DEBE bloquear el cierre de una escritura si su balance de impuestos
  es distinto de cero, informando el monto desbalanceado.
- **FR-025b**: El sistema DEBE bloquear el cierre si existe al menos un impuesto cargado
  sin pago del cliente registrado o sin pago de la escribanía registrado, informando cuáles
  impuestos tienen pagos pendientes.
- **FR-026**: El balance de impuestos DEBE recalcularse en tiempo real ante registro,
  edición o eliminación de impuestos y pagos.

**Actualización y consistencia**

- **FR-021**: Libro de Entrada, Libro de Salida, Liquidación, Pago de Salarios y la sección
  Impuestos DEBEN actualizarse en tiempo real ante registro, edición o eliminación de
  impuestos y pagos.
- **FR-022**: El listado de Impuestos DEBE mostrar el estado de cada registro: sin pagos,
  con pago del cliente, con pago de la escribanía, o con ambos.

### Key Entities

- **ImpuestoEscritura**: gasto impositivo o de servicio del inmueble vinculado a una escritura;
  contiene tipo, monto total del período, período (fecha inicio, fecha fin), fecha de corte,
  dirección de prorrateo y monto prorrateado sugerido (calculado linealmente por días).
- **PagoImpuestoCliente**: pago real del cliente a la escribanía por un ImpuestoEscritura;
  genera línea en Libro de Entrada.
- **PagoImpuestoEscribania**: pago real de la escribanía al servicio por un ImpuestoEscritura;
  genera línea en Libro de Salida.
- **EntradaLibro** (ampliada): puede representar un PagoImpuestoCliente además de pagos del
  cliente por honorarios.
- **SalidaLibro** (ampliada): puede representar un PagoImpuestoEscribania además de pagos de
  la escribanía por escritura.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: La secretaria puede cargar un impuesto con período y prorrateo y verlo listado
  en la sección Impuestos en menos de 3 segundos.
- **SC-002**: El 100% de los pagos del cliente por impuestos generan exactamente una línea en
  el Libro de Entrada del mes de su fecha de pago.
- **SC-003**: El 100% de los pagos de la escribanía por impuestos generan exactamente una
  línea en el Libro de Salida del mes de su fecha de pago.
- **SC-004**: En pruebas de prorrateo lineal con el mismo monto y período, hacia atrás y hacia
  adelante producen montos sugeridos complementarios que suman el monto total del período
  cuando los tramos cubren el período completo sin solapamiento.
- **SC-005**: El 100% de los intentos de cierre con balance de impuestos distinto de cero
  o con impuestos sin ambos pagos registrados son bloqueados con mensaje claro.
- **SC-006**: Libros y sección Impuestos se actualizan en menos de 2 segundos tras registrar
  un pago.
- **SC-007**: La sección Impuestos aparece debajo de pagos del cliente y de la escribanía en
  el 100% de las vistas de detalle de escritura (escritorio y móvil).
- **SC-008**: El balance de impuestos mostrado en detalle coincide con la diferencia entre
  sumas de pagos cliente y escribanía en el 100% de los casos de prueba.
- **SC-009**: Liquidación y Pago de Salarios del escribano reflejan el neto mensual de
  impuestos (cobros − egresos) en el 100% de escenarios con pagos asimétricos o compensados.
- **SC-010**: El cierre mensual de Liquidación no se bloquea por balance de impuestos ≠ $0 en
  escrituras abiertas; el cierre de escritura sí lo hace en el 100% de los casos de prueba.

---

## Assumptions

- Los seis tipos de impuesto listados son un catálogo fijo en esta feature; no se requiere
  administración dinámica de tipos desde Configuración.
- El monto total del período es la base del prorrateo lineal; el monto efectivo de cada pago
  puede diferir del sugerido (editable).
- Los impuestos no alteran el saldo pendiente de honorarios de la factura principal.
- Los impuestos **sí** impactan Liquidación Mensual y Pago de Salarios del escribano asignado,
  según el neto de movimientos reales por mes (fecha de pago); el balance acumulado = $0 solo
  se exige al **cerrar la escritura**, no al cerrar el mes.
- El período del impuesto es independiente de la fecha de creación o apertura de la escritura.
- Los libros contables filtran movimientos de impuestos por mes calendario de la fecha de pago.
- Una escritura puede tener múltiples registros de impuesto (incluso del mismo tipo si los
  períodos difieren).
- El cierre de escritura exige tres condiciones independientes: saldo de honorarios = $0
  (regla existente), balance de impuestos = $0, y cada impuesto cargado con pago del cliente
  y pago de la escribanía registrados.
- Impuestos cargados sin ambos pagos registrados bloquean el cierre aunque el balance global
  sea $0 (sin movimientos de caja).
- Impuestos y pagos son editables y eliminables mientras la escritura esté abierta; en
  escrituras cerradas permanecen en solo lectura.
- Tramos de prorrateo sin solapamiento: hacia atrás incluye la fecha de corte; hacia adelante
  comienza el día siguiente al corte.
- No se utiliza Figma para el diseño de UI de esta feature; se reutilizan patrones del
  detalle de escritura existente (feature 004).

---

## Testing Strategy

**Approach**: TDD — Test-Driven Development completo.

**Rationale**: La feature modifica libros contables, reglas de prorrateo, balance de impuestos
y bloqueo de cierre — superficies críticas de integridad financiera donde los tests deben
escribirse antes de la implementación.

**Scope note**: Esta decisión DEBE ser respetada por `/spec-kitti.plan` (contratos de test)
y `/spec-kitti.tasks` (tareas TDD / unit-test generadas en consecuencia).

**Scope específico de esta feature**:

- **Alta de impuestos**: tests de validación (período, montos, tipos, escritura cerrada).
- **Prorrateo**: tests de cálculo lineal por días (hacia atrás, hacia adelante, sin
  solapamiento en fecha de corte, fecha de corte fuera de período rechazada, límites en
  primer/último día del período, redondeo determinístico).
- **Pagos cliente / escribanía**: tests de registro, prefill del monto sugerido, edición,
  eliminación y derivación a libros por fecha de pago.
- **Liquidación y Salarios**: tests de neto mensual por escribano (cobro sin egreso, egreso
  sin cobro, compensados), sin bloqueo de cierre mensual.
- **Balance y cierre de escritura**: tests de balance acumulado, bloqueo con balance ≠ $0,
  bloqueo con impuestos sin ambos pagos, permiso solo con balance = $0 y pagos completos.
- **Tiempo real**: tests de integración/SSE para libros, Liquidación, Salarios, balance y
  sección Impuestos ante cambios.
- **Edición y eliminación**: tests de actualización de libros sin duplicar líneas y bloqueo
  en escrituras cerradas.

---

## Dependencies

- **Feature 004 (layout detalle escritura)**: la columna derecha con pagos del cliente y
  pagos de la escribanía debe existir para ubicar la sección Impuestos en la posición
  indicada. Si 004 no está desplegada, Impuestos debe igualmente ubicarse debajo de ambas
  secciones de pagos en el detalle de escritura.
