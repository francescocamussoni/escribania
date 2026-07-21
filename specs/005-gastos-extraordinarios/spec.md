# Feature Specification: Gastos Extraordinarios de la Escribanía

**Feature Branch**: `005-gastos-extraordinarios`  
**Created**: 2026-07-20  
**Status**: Implemented  
**Input**: User description: "Solapa gastos extraordinarios: ventana mensual para cargar gastos de la escribanía (celulares, papeles, etc.) que se registran automáticamente en el libro de salida y se deducen del pago de escribanos dividido entre todos los escribanos"

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Registrar Gastos Extraordinarios del Mes (Priority: P1)

La secretaria accede a la nueva sección **Gastos Extraordinarios** (segunda posición en la
navegación principal, inmediatamente después de Escrituras) y carga los gastos puntuales de
la escribanía del mes en curso — por ejemplo compra de celulares, papel, insumos u otros
conceptos no vinculados a una escritura particular. Cada gasto queda registrado con
concepto, monto y fecha, y el sistema lo incorpora automáticamente al Libro de Salida del mes
correspondiente.

**Why this priority**: Sin el registro de gastos no existe trazabilidad contable ni base para
descontarlos del pago de escribanos. Es el núcleo operativo de la feature.

**Independent Test**: Se puede probar navegando a Gastos Extraordinarios, cargando uno o más
gastos con distintas fechas dentro de un mes, y verificando que aparecen en el listado del
mes y generan líneas en el Libro de Salida — sin abrir Pago de Salarios ni modificar
escrituras.

**Acceptance Scenarios**:

1. **Given** la secretaria está autenticada, **When** visualiza la barra de navegación
   principal, **Then** ve la solapa "Gastos Extraordinarios" en segunda posición, entre
   "Escrituras" y "Liquidación".

2. **Given** la sección Gastos Extraordinarios, **When** la secretaria selecciona un mes y
   año, **Then** ve el listado de gastos extraordinarios registrados en ese período junto
   con el total del mes.

3. **Given** la sección Gastos Extraordinarios con un mes seleccionado, **When** la
   secretaria registra un gasto con concepto, monto positivo y fecha dentro del mes,
   **Then** el gasto aparece en el listado del mes con esos datos y el total del mes se
   actualiza.

4. **Given** un gasto extraordinario registrado con fecha en julio 2026, **When** la
   secretaria consulta el Libro de Salida de julio 2026, **Then** ve una línea por ese
   gasto con monto, fecha, concepto e identificación como gasto extraordinario (sin
   referencia a escritura).

5. **Given** un gasto extraordinario registrado, **When** la secretaria lo elimina o corrige
   desde Gastos Extraordinarios, **Then** el listado del mes, el Libro de Salida y los
   totales asociados se actualizan en consecuencia.

6. **Given** un intento de registro con monto cero, negativo o sin concepto, **When** la
   secretaria confirma el alta, **Then** el sistema rechaza el registro y muestra un mensaje
   claro de validación.

---

### User Story 2 — Descontar Gastos del Pago de Escribanos (Priority: P1)

Al consultar el **Pago de Salarios** de un mes, cada escribano ve una deducción por su
parte proporcional de los gastos extraordinarios del mismo mes. El monto total de gastos del
mes se divide en partes iguales entre todos los escribanos activos de la escribanía, y esa
cuota se resta del importe a cobrar de cada uno.

**Why this priority**: El reparto entre escribanos es el objetivo de negocio principal;
sin él, los gastos quedarían solo como egreso sin impacto en la liquidación interna.

**Independent Test**: Con tres escribanos activos y $300.000 en gastos extraordinarios en un
mes, el Pago de Salarios de ese mes muestra $100.000 de deducción por escribano,
independientemente de cuántas escrituras haya trabajado cada uno.

**Acceptance Scenarios**:

1. **Given** gastos extraordinarios por un total de $300.000 en julio 2026 y tres escribanos
   activos, **When** la secretaria consulta Pago de Salarios de julio 2026, **Then** cada
   escribano muestra una línea de deducción por gastos extraordinarios de $100.000.

2. **Given** un escribano con ingresos por escrituras en el mes y deducción por gastos
   extraordinarios, **When** la secretaria revisa su card en Pago de Salarios, **Then** el
   importe neto a cobrar es la suma de pagos de sus escrituras menos su cuota de gastos
   extraordinarios.

3. **Given** un mes sin gastos extraordinarios registrados, **When** la secretaria consulta
   Pago de Salarios de ese mes, **Then** no aparece deducción por gastos extraordinarios
   (o aparece en $0) y el importe de cada escribano no se ve afectado.

4. **Given** un nuevo gasto extraordinario registrado en un mes ya consultado, **When** la
   secretaria vuelve a Pago de Salarios del mismo mes, **Then** las deducciones y el neto
   de cada escribano reflejan el nuevo total sin recargar manualmente la página.

5. **Given** gastos extraordinarios en julio y la secretaria consulta Pago de Salarios de
   agosto, **When** revisa las deducciones, **Then** los gastos de julio no impactan el
   cálculo de agosto.

---

### User Story 3 — Consultar y Filtrar Gastos por Período (Priority: P2)

La secretaria navega entre meses y años para revisar el historial de gastos extraordinarios,
comparar totales mensuales y verificar que coinciden con el Libro de Salida del mismo
período.

**Why this priority**: Facilita el control y la auditoría mensual sin bloquear el flujo
principal de carga y descuento.

**Independent Test**: Se puede probar cambiando el selector de mes/año y verificando que
solo se muestran gastos del período elegido y que el total coincide con la suma de líneas
del Libro de Salida filtrado por ese mes.

**Acceptance Scenarios**:

1. **Given** gastos registrados en distintos meses, **When** la secretaria cambia el mes
   en el selector de Gastos Extraordinarios, **Then** el listado y el total muestran
   únicamente los gastos cuya fecha cae en ese mes calendario.

2. **Given** el total mostrado en Gastos Extraordinarios de un mes, **When** la secretaria
   compara con el Libro de Salida del mismo mes, **Then** la suma de líneas de gastos
   extraordinarios coincide con ese total.

3. **Given** un mes sin gastos, **When** la secretaria lo selecciona, **Then** el sistema
   muestra un estado vacío con mensaje claro y total $0.

---

### Edge Cases

- ¿Qué ocurre si no hay escribanos activos configurados? El sistema permite registrar el
  gasto y reflejarlo en el Libro de Salida, pero muestra advertencia en Pago de Salarios
  indicando que no puede calcularse el reparto hasta que exista al menos un escribano activo.
- ¿Cómo se maneja el redondeo al dividir entre escribanos? La suma de las cuotas individuales
  debe igualar exactamente el total de gastos del mes; cualquier diferencia por centavos se
  asigna de forma determinística (por ejemplo al último escribano en orden alfabético).
- ¿Un gasto con fecha en un mes distinto al mes visualizado en el selector? El gasto aparece
  en el mes de su fecha, no en el mes del selector si difieren al registrar.
- ¿Se pueden registrar gastos en meses pasados? Sí; la fecha del gasto determina el mes
  contable para Libro de Salida y deducción en Pago de Salarios.
- ¿Los gastos extraordinarios afectan Liquidación o Libro de Entrada? No; solo impactan
  Libro de Salida y Pago de Salarios de escribanos.

---

## Requirements *(mandatory)*

### Functional Requirements

**Navegación y acceso**

- **FR-001**: El sistema DEBE exponer una sección "Gastos Extraordinarios" en la navegación
  principal, en segunda posición (inmediatamente después de "Escrituras").
- **FR-002**: Solo usuarios autenticados DEBEN poder acceder a Gastos Extraordinarios.

**Registro de gastos**

- **FR-003**: El sistema DEBE permitir registrar gastos extraordinarios con concepto
  obligatorio, monto positivo y fecha.
- **FR-004**: El sistema DEBE mostrar los gastos agrupados por mes calendario según la fecha
  del gasto, con selector de mes y año.
- **FR-005**: El sistema DEBE permitir editar y eliminar gastos extraordinarios existentes;
  los cambios DEBEN reflejarse de inmediato en listados y cálculos dependientes.
- **FR-006**: El sistema DEBE rechazar registros con monto cero, negativo o concepto vacío.

**Libro de Salida**

- **FR-007**: Cada gasto extraordinario registrado DEBE generar automáticamente una línea en
  el Libro de Salida del mes calendario de su fecha.
- **FR-008**: Cada línea de gasto extraordinario en el Libro de Salida DEBE incluir: monto,
  fecha, concepto e indicación de que es un gasto extraordinario (sin escritura asociada).
- **FR-009**: El Libro de Salida DEBE incluir tanto los pagos de escribanía por escritura
  como los gastos extraordinarios del período, diferenciados visualmente.
- **FR-010**: Al editar o eliminar un gasto extraordinario, el Libro de Salida DEBE
  actualizarse en tiempo real.

**Pago de Salarios — deducción**

- **FR-011**: El total de gastos extraordinarios de un mes DEBE dividirse en partes iguales
  entre todos los escribanos activos de la escribanía.
- **FR-012**: La cuota de cada escribano DEBE descontarse de su importe neto en Pago de
  Salarios del mismo mes calendario que la fecha de los gastos.
- **FR-013**: Pago de Salarios DEBE mostrar por escribano el detalle de la deducción por
  gastos extraordinarios (monto de cuota y total de gastos del mes repartido).
- **FR-014**: La deducción y el neto DEBEN recalcularse en tiempo real ante alta, edición o
  baja de gastos extraordinarios del mes.

**Consistencia**

- **FR-015**: El total de gastos extraordinarios mostrado en la sección del mes DEBE coincidir
  con la suma de sus líneas en el Libro de Salida del mismo mes.
- **FR-016**: Los gastos extraordinarios NO DEBEN vincularse a una escritura ni modificar el
  saldo pendiente de escrituras.

### Key Entities

- **GastoExtraordinario**: gasto puntual de la escribanía no asociado a una escritura;
  contiene concepto, monto, fecha y referencia al mes contable derivado de la fecha.
- **DeduccionGastoExtraordinario**: cuota mensual calculada por escribano (total del mes ÷
  cantidad de escribanos activos); se aplica en Pago de Salarios.
- **SalidaLibro** (ampliada): además de pagos de escribanía por escritura, puede representar
  un GastoExtraordinario con los mismos campos visibles (monto, fecha, concepto) y sin
  escritura asociada.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: La secretaria puede registrar un gasto extraordinario y verlo reflejado en el
  listado del mes y en el Libro de Salida en menos de 3 segundos, sin recargar la página.
- **SC-002**: El 100% de los gastos extraordinarios registrados generan exactamente una línea
  correspondiente en el Libro de Salida del mes de su fecha.
- **SC-003**: La suma de las cuotas de deducción por escribano en un mes iguala siempre el
  total de gastos extraordinarios de ese mes (sin pérdida ni exceso por redondeo).
- **SC-004**: El Pago de Salarios muestra la deducción correcta para cada escribano en el
  100% de los casos de prueba con 1 a N escribanos activos y montos divisibles e
  indivisibles.
- **SC-005**: Editar o eliminar un gasto actualiza Libro de Salida y Pago de Salarios en
  menos de 2 segundos.
- **SC-006**: La sección Gastos Extraordinarios aparece en segunda posición en la navegación
  en el 100% de las vistas autenticadas de la aplicación.

---

## Assumptions

- "Escribanos activos" son los escribanos configurados y habilitados en la escribanía al
  momento del cálculo mensual (misma fuente que usa Pago de Salarios hoy).
- La fecha del gasto determina el mes contable para Libro de Salida y deducción en Pago de
  Salarios, alineado con el criterio de mes calendario ya usado en libros contables.
- Los gastos extraordinarios son independientes de escrituras, liquidación mensual por
  escritura y pagos del cliente.
- El reparto es equitativo (misma cuota para cada escribano activo), sin ponderación por
  cantidad de escrituras trabajadas.
- La sección de Configuración (escribanos, empleados) no se modifica en esta feature; se
  consume la lista existente de escribanos.
- No se utiliza Figma para el diseño de UI de esta feature; se reutilizan patrones y estilos
  del frontend existente.
