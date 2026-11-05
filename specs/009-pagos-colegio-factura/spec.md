# Feature Specification: Pagos al Colegio, Libro de Salida y Montos Opcionales en Factura

**Feature Branch**: `009-pagos-colegio-factura`  
**Created**: 2026-07-26  
**Status**: Draft  
**Input**: User description: "Revisar gastos de escribanía en libro de salida: solo pagos al colegio de escribanos. Opciones Pago al colegio vs Otros. Pago masivo multi-escritura desde facturas. Casilleros para habilitar/deshabilitar montos en factura al crear escritura."

## Clarifications

### Session 2026-07-26

- Q: ¿Aplicar TDD y/o unit tests estrictos para esta feature? → A: **Sí — TDD-first** (tests escritos antes de la implementación en todo el scope).
- Q: ¿Cómo conviven el tipo Colegio/Otros y la imputación de la feature 008? → A: **Sin imputación**. En la solapa Pagos de la escribanía solo existen dos tipos: **Pago al colegio de escribanos** (siempre por **Total impuestos**; no honorarios varios ni otros conceptos) y **Otros** (comodín con detalle obligatorio). **Honorarios varios no es opción** de pago ni imputación. **Otros** también genera línea en el Libro de Salida mostrando el detalle.
- Q: ¿A qué nivel se habilitan/deshabilitan montos en la factura? → A: **Por ítem de línea** — cada concepto individual de la Factura Principal tiene su propio casillero (ej. Municipio sí, Catastro no).
- Q: ¿Qué fecha usa el pago masivo al Colegio? → A: **Fecha única** para todo el lote (una transferencia, misma fecha registrada en todas las escrituras seleccionadas).
- Q: ¿Ítems deshabilitados y Total impuestos al Colegio? → A: **Una sola lectura** — si se deshabilitan ítems de impuestos, el **Total impuestos** (cobro al cliente, pendiente al Colegio y vencimiento a 30 días) se recalcula solo con ítems de impuestos **habilitados**.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Registrar Pagos de la Escribanía y Reflejarlos en el Libro de Salida (Priority: P1)

La secretaria registra un egreso desde la sección **Pagos de la escribanía** en el detalle de
una escritura. El sistema ofrece **únicamente** dos tipos de pago:

- **Pago al colegio de escribanos** (opción por defecto): siempre imputado a **Total
  impuestos** de la factura. No existe selector de honorarios varios, Corresponde u otros
  conceptos; el pago al Colegio es exclusivamente por impuestos.
- **Otros**: comodín para imprevistos; requiere un **detalle obligatorio** que describa qué
  se abonó.

Ambos tipos generan línea en el **Libro de Salida** del mes de la fecha del pago. En líneas
tipo **Otros**, el detalle ingresado debe mostrarse en el libro junto al monto y la
referencia a la escritura.

El Libro de Salida deja de incluir pagos de impuestos de servicios del inmueble (API, TGI,
etc.) ni gastos extraordinarios; solo refleja pagos registrados en la solapa Pagos de la
escribanía (Colegio u Otros).

**Why this priority**: Alinea el registro operativo con la práctica real: el Colegio se paga
por Total impuestos con vencimiento a 30 días; los imprevistos se registran como Otros sin
perder trazabilidad en el Libro de Salida.

**Independent Test**: Registrar un pago de cada tipo en escrituras distintas del mismo mes y
verificar que ambos aparecen en el Libro de Salida (Colegio sin detalle adicional; Otros con
detalle visible), mientras pagos de otros módulos no aparecen.

**Acceptance Scenarios**:

1. **Given** el formulario de Pagos de la escribanía en una escritura abierta, **When** la
   secretaria lo despliega, **Then** ve solo dos opciones: **Pago al colegio de escribanos**
   (preseleccionado) y **Otros**; no aparece selector de honorarios varios ni imputación.

2. **Given** un pago tipo **Pago al colegio de escribanos**, monto positivo y fecha,
   **When** la secretaria confirma, **Then** el pago se registra, reduce el pendiente de
   Total impuestos y aparece en el Libro de Salida del mes.

3. **Given** un pago tipo **Otros** sin texto de detalle, **When** la secretaria intenta
   confirmar, **Then** el sistema rechaza el registro con mensaje claro.

4. **Given** un pago tipo **Otros** con detalle completado, monto positivo y fecha,
   **When** la secretaria confirma, **Then** el pago se registra en la escritura y aparece
   en el Libro de Salida mostrando monto, fecha, escritura y el detalle ingresado.

5. **Given** el Libro de Salida de un mes, **When** la secretaria lo consulta, **Then** solo
   aparecen pagos de la solapa Pagos de la escribanía (Colegio u Otros); no aparecen pagos
   de impuestos de servicios ni gastos extraordinarios.

6. **Given** un pago registrado en Pagos de la escribanía, **When** la secretaria consulta
   el Libro de Salida en otra pestaña, **Then** el libro se actualiza en tiempo real.

---

### User Story 2 — Habilitar o Deshabilitar Montos en la Factura de una Escritura (Priority: P1)

Al crear o editar una escritura abierta, la secretaria visualiza la Factura Principal con un
**casillero por cada ítem de línea** cobrable al cliente (honorario, certificación, cada
impuesto, cada gasto administrativo, etc.) que permite incluirlo o excluirlo del cobro. Por
defecto, todos los ítems están **habilitados**. Al deshabilitar un ítem, ese monto deja de sumar al
**costo total cobrable al cliente**, pero permanece visible en el desglose (marcado como no
cobrado). El **Total impuestos** (mostrado en factura, pendiente al Colegio y vencimiento a
30 días) se recalcula **solo con los ítems de impuestos habilitados** — una única lectura
coherente para cliente y obligación al Colegio.

**Why this priority**: Permite no cobrar íntegro a ciertos clientes y alinear la obligación al
Colegio con lo que efectivamente aplica en esa escritura.

**Independent Test**: Crear una escritura, deshabilitar ítems, guardar y verificar costo al
cliente vs pendiente de Total impuestos al Colegio.

**Acceptance Scenarios**:

1. **Given** una escritura nueva, **When** se genera la Factura Principal, **Then** todos los
   ítems cobrables aparecen habilitados por defecto.

2. **Given** la factura de una escritura abierta, **When** la secretaria deshabilita un ítem
   y guarda, **Then** el costo total al cliente se recalcula sin ese ítem; el ítem
   deshabilitado permanece visible como no cobrado.

3. **Given** ítems deshabilitados, **When** se registran pagos del cliente, **Then** el saldo
   pendiente se calcula solo sobre ítems habilitados.

4. **Given** ítems de impuestos deshabilitados, **When** se consulta Total impuestos en
   factura, pendiente al Colegio y vencimiento, **Then** los tres usan el mismo Total
   impuestos recalculado solo con ítems de impuestos habilitados.

4b. **Given** todos los ítems de impuestos deshabilitados, **When** se consulta vencimiento al
   Colegio, **Then** no aplica plazo (Total impuestos = $0).

5. **Given** una escritura cerrada, **When** la secretaria intenta cambiar habilitación de
   ítems, **Then** el sistema bloquea la modificación.

6. **Given** pagos del cliente ya registrados, **When** deshabilitar ítems deja el total
   cobrable menor que lo pagado, **Then** saldo pendiente = $0 con indicador visual de
   sobrepago.

---

### User Story 3 — Pago Masivo al Colegio desde el Listado de Escrituras (Priority: P2)

Desde el **listado de Escrituras**, la secretaria selecciona múltiples escrituras y ejecuta
**Pago al colegio de escribanos**. El sistema propone por cada escritura el **pendiente de
Total impuestos** (Total impuestos menos pagos previos tipo Colegio). La secretaria indica
**una fecha de pago única** para todo el lote y confirma; el sistema registra un pago Colegio
en cada escritura con esa misma fecha y genera las líneas en el Libro de Salida.

**Why this priority**: Agiliza transferencias al Colegio por varias escrituras en un solo acto.

**Independent Test**: Seleccionar escrituras con pendiente de Total impuestos, ejecutar pago
masivo y verificar pagos y líneas en Libro de Salida.

**Acceptance Scenarios**:

1. **Given** el listado de Escrituras, **When** la secretaria lo visualiza, **Then** cada fila
   tiene casillero de selección y la acción **Pago al colegio de escribanos** se habilita con
   al menos una escritura elegible seleccionada.

2. **Given** dos escrituras con pendiente de Total impuestos de $80.000 y $120.000, **When**
   ejecuta pago masivo, **Then** el resumen muestra $80.000, $120.000 y total $200.000 antes
   de confirmar.

3. **Given** confirmación con una **fecha única** válida para todo el lote, **When** se
   procesa, **Then** cada escritura recibe un pago tipo Colegio por el monto confirmado con
   esa misma fecha y aparece en el Libro de Salida del mes correspondiente.

4. **Given** una escritura con pendiente de Total impuestos $0, **When** se incluye en el
   lote, **Then** se excluye o marca sin monto a pagar.

5. **Given** una escritura cerrada, **When** se intenta seleccionar, **Then** el casillero
   está deshabilitado o la acción la rechaza.

6. **Given** pago masivo confirmado, **When** se consulta el listado, **Then** indicadores de
   vencimiento de Total impuestos reflejan estado actualizado (Pagado o días restantes).

---

### Edge Cases

- ¿Pago masivo con monto ajustado manualmente? Permitido por escritura; sin validación
  estricta contra pendiente proyectado.
- ¿Escrituras de distintos escribanos en un lote? Permitido; cada pago queda en su escritura.
- ¿Pagos Colegio existentes con imputación honorarios varios (feature 008)? Migrar como
  **Pago al colegio de escribanos** aplicados a Total impuestos para Libro de Salida e
  indicadores de vencimiento.
- ¿Honorarios varios en la factura? Permanecen en el desglose de factura pero **no** son
  registrables ni imputables desde Pagos de la escribanía.
- ¿Se puede deshabilitar todos los ítems cobrables? No; al menos uno debe permanecer habilitado.
- ¿Todos los ítems de impuestos deshabilitados? Total impuestos = $0; sin vencimiento al
  Colegio ni propuesta en pago masivo por ese concepto.
- ¿Deshabilitar honorarios o gastos admin? No afecta Total impuestos ni pendiente al Colegio
  (solo afectan el costo cobrable al cliente).
- ¿Filtro del Libro de Salida? Por mes calendario según **fecha del pago**.

---

## Requirements *(mandatory)*

### Functional Requirements

**Pagos de la escribanía (solapa única)**

- **FR-001**: La solapa Pagos de la escribanía DEBE ofrecer únicamente dos tipos: **Pago al
  colegio de escribanos** y **Otros**.
- **FR-002**: El valor por defecto DEBE ser **Pago al colegio de escribanos**.
- **FR-003**: Los pagos tipo **Pago al colegio de escribanos** DEBEN imputarse siempre a
  **Total impuestos**; NO DEBE existir opción de honorarios varios, Corresponde separado ni
  selector de imputación adicional.
- **FR-004**: Los pagos tipo **Otros** DEBEN exigir detalle obligatorio (texto no vacío).
- **FR-005**: Ambos tipos (Colegio y Otros) DEBEN generar línea en el Libro de Salida del
  mes de la fecha del pago; las líneas **Otros** DEBEN mostrar el detalle ingresado.
- **FR-006**: El selector de imputación de la feature 008 (Total impuestos / Honorarios varios
  / Otro) DEBE eliminarse de Pagos de la escribanía; esta feature lo reemplaza.

**Libro de Salida**

- **FR-007**: El Libro de Salida DEBE contener exclusivamente pagos registrados en Pagos de
  la escribanía (tipos Colegio y Otros); NO DEBE incluir pagos de impuestos de servicios ni
  gastos extraordinarios.
- **FR-008**: Cada línea DEBE incluir: monto, fecha, referencia a escritura, tipo de pago y
  enlace navegable; si el tipo es Otros, también el detalle.
- **FR-009**: El total del período DEBE ser la suma de todos los pagos Colegio y Otros del mes.
- **FR-010**: El Libro de Salida DEBE actualizarse en tiempo real.

**Vencimiento Total impuestos (simplificación sobre feature 008)**

- **FR-011**: Todo pago tipo **Pago al colegio de escribanos** DEBE reducir el pendiente de
  **Total impuestos** y contar para el countdown de 30 días y estado Pagado.
- **FR-012**: Los pagos tipo **Otros** NO DEBEN afectar el pendiente ni el vencimiento de
  Total impuestos.

**Montos opcionales en factura**

- **FR-013**: La Factura Principal DEBE permitir habilitar/deshabilitar **cada ítem de línea**
  cobrable al cliente mediante casillero individual (no solo por sección).
- **FR-014**: Por defecto, todos los ítems cobrables DEBEN estar habilitados al crear.
- **FR-015**: Ítems deshabilitados NO suman al costo cobrable al cliente; permanecen visibles
  como no cobrados.
- **FR-016**: Saldo del cliente, cierre y Libro de Entrada DEBEN basarse solo en ítems
  habilitados.
- **FR-017**: **Total impuestos** (factura, pendiente al Colegio y vencimiento a 30 días) DEBE
  calcularse como la suma de **solo los ítems de impuestos habilitados**; deshabilitar un ítem
  de impuestos DEBE reducir Total impuestos y el pendiente al Colegio en la misma magnitud.
- **FR-017b**: Deshabilitar ítems que no son de impuestos (honorarios, gastos admin, etc.) NO
  DEBE alterar Total impuestos ni el vencimiento al Colegio.
- **FR-018**: El sistema DEBE impedir guardar con cero ítems habilitados.
- **FR-019**: La habilitación NO DEBE modificarse en escrituras cerradas.

**Pago masivo al Colegio**

- **FR-020**: El listado de Escrituras DEBE permitir selección múltiple y acción **Pago al
  colegio de escribanos**.
- **FR-021**: El importe propuesto por escritura DEBE ser el pendiente de **Total impuestos**
  (Total impuestos − pagos Colegio previos de esa escritura).
- **FR-022**: Antes de confirmar, DEBE mostrarse resumen por escritura con monto editable y
  un único campo de **fecha de pago** aplicado a todo el lote.
- **FR-023**: Al confirmar, DEBE registrarse un pago tipo Colegio por escritura incluida con
  la **misma fecha** para todas.
- **FR-024**: Escrituras cerradas o sin pendiente de Total impuestos NO DEBEN ser elegibles.

**Trazabilidad**

- **FR-025**: Pagos individuales en Pagos de la escribanía DEBEN seguir disponibles además del
  flujo masivo.
- **FR-026**: Toda cifra del Libro de Salida DEBE ser trazable a escritura y pago origen.

### Key Entities

- **Pago de la escribanía**: Egreso en solapa Pagos de la escribanía; atributos: monto, fecha,
  tipo (Colegio | Otros), detalle (obligatorio si Otros). Tipo Colegio siempre imputado a
  Total impuestos.
- **Ítem de factura cobrable**: Línea con monto calculado y flag habilitado/deshabilitado para
  cobro al cliente.
- **Pendiente Total impuestos**: Total impuestos vigente (solo ítems de impuestos habilitados)
  menos suma de pagos Colegio de la escritura.
- **Línea de Libro de Salida**: Pago Colegio u Otros del período, con trazabilidad a escritura.

### Assumptions

- El listado de Escrituras integra selección múltiple y pago masivo (feature 008 aporta
  vencimiento y ordenamiento; la imputación de 008 queda reemplazada por esta feature).
- Los ítems habilitables son **cada línea individual** de la Factura Principal que contribuye
  al total cobrable al cliente (honorarios, leyes, impuestos, gastos administrativos por
  concepto); no casilleros solo a nivel de sección.
- Pagos Colegio legacy sin tipo se migran como **Pago al colegio de escribanos**; los que
  tenían imputación honorarios varios se reclasifican como Colegio aplicado a Total impuestos.
- Impuestos de servicios (006) y gastos extraordinarios (005) permanecen en sus módulos pero
  fuera del Libro de Salida.

### Dependencies

- **Feature 003**: base de pagos y Libro de Salida por caja real.
- **Feature 007**: estructura de factura y Total impuestos.
- **Feature 008**: vencimiento a 30 días y UI de listado; **imputación de 008 queda
  superseded** por los tipos Colegio/Otros de esta feature.
- **Features 005 y 006**: egresos retirados del Libro de Salida.

---

## Non-Functional Requirements

### Testing Strategy

- **Approach**: TDD — tests escritos antes de la implementación en todo el scope.
- **Rationale**: La feature modifica reglas contables, cálculo de pendientes al Colegio,
  clasificación de egresos y visibilidad en el Libro de Salida; TDD-first reduce regresiones
  en lógica financiera crítica.
- **Scope note**: Esta decisión DEBE ser honrada por `/spec-kitti.plan` (contratos de test) y
  `/spec-kitti.tasks` (tareas TDD / unit-test generadas en consecuencia).

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: La secretaria registra un pago Colegio u Otros en menos de 30 segundos desde
  Pagos de la escribanía.
- **SC-002**: El 100 % de las líneas del Libro de Salida provienen de Pagos de la escribanía
  (Colegio u Otros); ninguna de impuestos de servicios ni gastos extraordinarios.
- **SC-003**: Pago masivo a tres o más escrituras con pendiente de Total impuestos toma menos
  de 2 minutos desde selección hasta confirmación.
- **SC-004**: Al deshabilitar ítems, el costo al cliente disminuye exactamente la suma de los
  ítems deshabilitados; al deshabilitar ítems de impuestos, Total impuestos y pendiente al
  Colegio disminuyen en la misma magnitud (fixture canónico).
- **SC-005**: Tras pago Colegio que cubre Total impuestos, el indicador de vencimiento muestra
  **Pagado** sin recargar la página.
- **SC-006**: Las líneas **Otros** en Libro de Salida muestran el detalle ingresado en el
  100 % de los casos de prueba.
