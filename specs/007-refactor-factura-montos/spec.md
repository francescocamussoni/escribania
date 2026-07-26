# Feature Specification: Refactorización de montos de Factura Principal

**Feature Branch**: `007-refactor-factura-montos`  
**Created**: 2026-07-26  
**Status**: Draft  
**Input**: User description: "Refactorizar montos de la factura de cada escritura: reorganizar secciones (Bases de cálculo, Honorarios, Honorarios varios, Corresponde, Totales) y nuevas fórmulas de totales"

---

## Clarifications

### Session 2026-07-26

- Q: ¿Qué monto debe usar el sistema como costo total de la escritura (saldo del cliente, libro de entrada y reemplazo de total_factura)? → A: **Total + IVA** — el cliente debe cubrir honorarios, impuestos e IVA.
- Q: ¿Aplicar TDD y/o unit tests estrictos para esta feature? → A: **Sí — TDD-first** (tests antes de implementación).
- Q: Al desplegar, ¿qué escrituras deben recalcularse con las nuevas fórmulas? → A: **Deprecar el dataset mock/demo actual** y reemplazarlo (o actualizarlo) con uno nuevo consistente con las nuevas fórmulas y Total + IVA.
- Q: ¿Los montos de Totales deben persistirse en la factura almacenada? → A: **Igual que el resto de las secciones** — almacenados en la factura principal, recalculados automáticamente al crear o editar la escritura (sin comportamiento especial).

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Ver factura reorganizada por secciones (Priority: P1)

Una secretaria abre el detalle de una escritura y visualiza la Factura Principal
organizada en cinco bloques claros: **Bases de cálculo**, **Honorarios**, **Honorarios
varios**, **Corresponde** y **Totales**. Cada bloque muestra los mismos ítems de línea
que hoy, pero agrupados según la nueva estructura operativa de la escribanía. Los ítems
que representan aportes al Colegio de Escribanos dentro de Honorarios se distinguen
visualmente del resto.

**Why this priority**: Es el cambio visible más inmediato y la base sobre la que se
apoyan los nuevos totales. Sin la reorganización correcta, la secretaria no puede
validar montos ni explicar la factura al cliente.

**Independent Test**: Crear o abrir una escritura con datos canónicos y verificar que
las cinco secciones aparecen con los ítems y subtotales esperados, sin depender de
liquidación ni libros.

**Acceptance Scenarios**:

1. **Given** una escritura con factura calculada, **When** la secretaria abre el detalle
   de la factura, **Then** ve las secciones en este orden: Bases de cálculo, Honorarios,
   Honorarios varios, Corresponde, Totales.

2. **Given** la sección Bases de cálculo, **When** se muestra, **Then** incluye
   "Monto base MEP" y "Precio base Valor" con los mismos valores que hoy derivan de
   USD × dólar MEP y USD × dólar Banco Nación respectivamente.

3. **Given** la sección Honorarios, **When** se muestra, **Then** incluye Honorario
   principal, Certificación, Suma hon. + cert., Aporte 12%, 5% honorarios, Firma
   honorarios y el subtotal "Subtotal honorarios", y los ítems Aporte 12%, 5%
   honorarios, Firma honorarios y Subtotal honorarios se distinguen visualmente del
   resto de la sección.

4. **Given** la sección Honorarios varios, **When** se muestra, **Then** contiene los
   mismos ítems y subtotal que hoy aparecen en "Leyes notariales" (Art. 2 a), Art. 12
   a), Art. 12 c), Art. 12 f) y Total honorarios varios).

5. **Given** la sección Corresponde, **When** se muestra, **Then** agrupa en un solo
   bloque todos los ítems de "Impuestos y sellos" y "Gastos administrativos fijos",
   manteniendo dos subtotales visibles: "Total impuestos" y "Total gastos admin.".

---

### User Story 2 — Totales recalculados automáticamente (Priority: P1)

Al crear o actualizar una escritura, el sistema calcula y muestra en la sección
**Totales** los nuevos montos resumen (Dif Honorarios, Total parcial, Total, IVA y
Total + IVA) según las fórmulas acordadas, sin requerir carga manual.

**Why this priority**: Los totales definen cuánto debe pagar el cliente y cómo se
distribuyen honorarios, impuestos e IVA. Es el núcleo del cambio funcional.

**Independent Test**: Con el fixture canónico (USD 105.000, MEP 1.450,34, Nación
1.425,00), verificar que cada línea de Totales coincide con el resultado de aplicar
las fórmulas sobre los ítems de línea existentes.

**Acceptance Scenarios**:

1. **Given** una factura con ítems calculados, **When** el sistema deriva Totales,
   **Then** "Dif Honorarios" = (Suma hon. + cert.) − (Aporte 12%).

2. **Given** una factura con ítems calculados, **When** el sistema deriva Totales,
   **Then** "Total parcial" = Dif Honorarios + (Total gastos admin. − Fotocopias
   urgentes − Informes notariales − Municipio − II Certificados − Catastro).

3. **Given** una factura con ítems calculados, **When** el sistema deriva Totales,
   **Then** "Total" = Total parcial + Subtotal honorarios + Total impuestos.

4. **Given** una factura con ítems calculados, **When** el sistema deriva Totales,
   **Then** "IVA" = (Dif Honorarios + Total impuestos) × 21%.

5. **Given** una factura con ítems calculados, **When** el sistema deriva Totales,
   **Then** "Total + IVA" = Total + IVA.

6. **Given** que la secretaria modifica USD o tipos de cambio en una escritura abierta,
   **When** guarda, **Then** todos los ítems de línea y la sección Totales se
   recalculan de forma consistente.

---

### User Story 3 — Consistencia con pagos y libros (Priority: P2)

La secretaria registra pagos del cliente y consulta libros de entrada/salida usando
montos coherentes con la nueva estructura de factura, sin discrepancias entre lo que ve
en la factura y lo que usa el resto del sistema.

**Why this priority**: La factura alimenta pagos, saldos y libros contables. Un
desalineamiento generaría errores operativos al cierre de mes.

**Independent Test**: Tras refactorizar una escritura de prueba, verificar que el monto
usado para saldo del cliente y libro de entrada coincide con el total acordado, y que
Honorarios varios sigue disponible como referencia para pagos al Colegio.

**Acceptance Scenarios**:

1. **Given** una escritura con factura recalculada, **When** la secretaria consulta
   saldo pendiente del cliente, **Then** el costo total refleja **Total + IVA** de la
   sección Totales (reemplaza el actual `total_factura`).

2. **Given** la sección Honorarios varios, **When** la secretaria registra un pago al
   Colegio, **Then** puede seguir usando el subtotal de Honorarios varios como
   referencia informativa (equivalente al actual total de leyes notariales).

3. **Given** el libro de entrada del mes, **When** se lista una escritura, **Then** el
   monto total mostrado coincide con **Total + IVA** de la sección Totales.

---

### Edge Cases

- Escritura con valores mínimos aplicados (honorario mínimo, 5% honorarios mínimo,
  Art. 12 a) mínimo): los totales deben respetar los mismos mínimos que hoy en los
  ítems de línea.
- Ítems excluidos del Total parcial con valor cero: Total parcial no debe restar más
  de lo que aporta Total gastos admin.
- Redondeo: todos los montos derivados se expresan con dos decimales; el redondeo debe
  ser consistente en cada paso intermedio de Totales.
- Escritura cerrada: la factura reorganizada es de solo lectura; los totales no cambian
  salvo migración explícita.
- Escrituras existentes al desplegar el cambio: el seed demo `[DEMO]` MUST deprecarse y
  regenerarse con montos consistentes; fixtures de tests MUST actualizarse al mismo
  criterio.

---

## Requirements *(mandatory)*

### Functional Requirements

#### Estructura de la factura

- **FR-001**: El sistema MUST mostrar la Factura Principal en exactamente cinco
  secciones: Bases de cálculo, Honorarios, Honorarios varios, Corresponde y Totales.

- **FR-002**: La sección Bases de cálculo MUST incluir "Monto base MEP" y "Precio base
  Valor", calculados igual que hoy (USD × dólar MEP y USD × dólar Banco Nación).

- **FR-003**: La sección Honorarios MUST contener los mismos ítems que hoy en
  "Honorarios profesionales", renombrando el título de la sección a "Honorarios".

- **FR-004**: El sistema MUST resaltar visualmente (color o estilo diferenciado) los
  ítems Aporte 12%, 5% honorarios, Firma honorarios y el subtotal Subtotal honorarios,
  indicando que son montos destinados al Colegio de Escribanos.

- **FR-005**: La sección "Leyes notariales" MUST renombrarse a "Honorarios varios"; los
  ítems de línea, tasas y subtotal MUST permanecer sin cambio de lógica (el subtotal
  MUST mostrarse como "Total honorarios varios").

- **FR-006**: Las secciones "Impuestos y sellos" y "Gastos administrativos fijos" MUST
  fusionarse en una sola sección llamada "Corresponde".

- **FR-007**: Dentro de Corresponde, el sistema MUST conservar la lógica y el subtotal
  "Total impuestos" (suma de Tasa 3‰, Sellos, Tasa 7,5‰ y Firma impuestos).

- **FR-008**: Dentro de Corresponde, el sistema MUST conservar la lógica y el subtotal
  "Total gastos admin." (suma de todos los gastos administrativos fijos actuales).

#### Cálculo de ítems de línea (sin cambio de tasas)

- **FR-009**: Todos los ítems de línea individuales (honorarios, artículos, impuestos,
  gastos fijos) MUST calcularse con las mismas fórmulas, tasas y mínimos vigentes en la
  constitución del proyecto, salvo los totales resumen descritos en FR-010 a FR-014.

#### Sección Totales (nuevas fórmulas)

- **FR-010**: El sistema MUST calcular y mostrar **Dif Honorarios** =
  (Suma hon. + cert.) − (Aporte 12%).

- **FR-011**: El sistema MUST calcular y mostrar **Total parcial** = Dif Honorarios +
  (Total gastos admin. − Fotocopias urgentes − Informes notariales − Municipio − II
  Certificados − Catastro).

- **FR-012**: El sistema MUST calcular y mostrar **Total** = Total parcial + Subtotal
  honorarios + Total impuestos.

- **FR-013**: El sistema MUST calcular y mostrar **IVA** = (Dif Honorarios + Total
  impuestos) × 0,21.

- **FR-014**: El sistema MUST calcular y mostrar **Total + IVA** = Total + IVA.

- **FR-014a**: Los cinco montos de Totales (Dif Honorarios, Total parcial, Total, IVA,
  Total + IVA) MUST almacenarse en la Factura Principal y recalcularse automáticamente
  con el mismo ciclo de vida que los ítems de Honorarios, Honorarios varios y
  Corresponde — sin carga manual ni cálculo solo en pantalla.

- **FR-015**: La sección Totales MUST mostrarse al final de la factura, reemplazando el
  único renglón "Total factura" actual.

#### Integración con el resto del sistema

- **FR-016**: El monto usado como costo total de la escritura (saldo del cliente, libro
  de entrada y reemplazo de `total_factura`) MUST ser **Total + IVA** de la sección
  Totales.

- **FR-017**: El subtotal de Honorarios varios MUST seguir expuesto como referencia para
  pagos al Colegio (equivalente funcional al actual total de leyes notariales
  proyectadas).

- **FR-018**: Liquidación mensual, libro de salida y demás vistas que desglosan montos
  de factura MUST actualizar etiquetas de sección (Honorarios varios, Corresponde,
  Totales) sin perder trazabilidad a ítems individuales.

- **FR-019**: Al modificar inputs de una escritura abierta, el sistema MUST recalcular
  automáticamente ítems de línea y Totales sin intervención manual.

- **FR-020**: El script de seed demo (`SEED_DEMO_DATA`) MUST incrementar su versión,
  detectar datasets demo inconsistentes con las nuevas fórmulas y **reemplazarlos**
  (borrar y re-crear) en lugar de conservar montos obsoletos.

- **FR-021**: Los fixtures de tests (unitarios e integración) que assertan montos de
  factura MUST actualizarse o deprecarse; ningún test MUST depender del dataset mock
  anterior.

### Key Entities

- **Factura Principal**: Documento calculado de una escritura; contiene ítems de línea
  por sección, subtotales intermedios (Subtotal honorarios, Total honorarios varios,
  Total impuestos, Total gastos admin.) y totales resumen (Dif Honorarios, Total
  parcial, Total, IVA, Total + IVA). Todos los montos — incluidos los de Totales —
  se almacenan en la factura y se recalculan al modificar inputs de la escritura,
  igual que el resto de las secciones.

- **Ítem de línea de factura**: Monto individual con etiqueta (ej. Honorario principal,
  Art. 2 a), Inscripción); su fórmula no cambia en este refactor.

- **Totales de factura**: Conjunto de cinco montos derivados que resumen la factura;
  **Total + IVA** es el monto canónico de cobro al cliente.

---

## Assumptions

- "Precio base Valor" es el renombre de "Precio base Nación"; el cálculo subyacente no
  cambia.
- En la fórmula de Total parcial, "Corresponde" se interpreta como el subtotal **Total
  gastos admin.** de la sección homónima (los ítems excluidos pertenecen solo a gastos
  administrativos, no a impuestos).
- Los ítems excluidos del Total parcial (Fotocopias urgentes, Informes notariales,
  Municipio, II Certificados, Catastro) se restan una sola vez cada uno de Total gastos
  admin.
- El subtotal de Honorarios varios NO forma parte de las fórmulas de Total ni Total +
  IVA; se liquida por separado al Colegio (coherente con el flujo actual de pagos al
  Colegio).
- El tipo de IVA es 21% fijo sobre (Dif Honorarios + Total impuestos).
- Las escrituras existentes se migran recalculando Totales con las nuevas fórmulas; no
  se alteran tasas ni configuración global.
- El entorno local/demo usa únicamente el nuevo dataset mock consistente; el seed demo
  previo se considera obsoleto y se reemplaza en el despliegue de esta feature.

---

## Dependencies

- Feature 001 (Plataforma Contaduría): modelo Escritura y Factura Principal.
- Feature 003 (Pagos Cliente): `costo_total` y saldo pendiente dependen del total
  acordado.
- Feature 002 (Libros): libro de entrada usa monto total; libro de salida desglosa
  ítems individuales.
- Constitución §2.2: tasas y mínimos de ítems de línea permanecen vigentes.

---

## Non-Functional Requirements

### Testing Strategy

- **Chosen approach**: TDD — generate tasks with a TDD-first approach (tests authored before implementation).
- **Rationale**: La feature modifica fórmulas monetarias, saldos del cliente y libros; los tests deben definir el comportamiento esperado antes de cambiar `calculo_factura` y vistas dependientes.
- **Scope**: Tests unitarios obligatorios para nuevas fórmulas de Totales, persistencia de `total_factura` (= Total + IVA), y regresión del fixture canónico; tests de integración para saldo pendiente y libro de entrada.
- **Downstream**: Esta decisión MUST ser honrada por `/spec-kitti.plan` (contratos de test) y `/spec-kitti.tasks` (tareas TDD / unit-test generadas antes de implementación).

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El 100% de las escrituras de prueba con fixture canónico muestran las
  cinco secciones con ítems y subtotales correctos en la primera visualización tras
  crear o editar.

- **SC-002**: Los cinco totales resumen (Dif Honorarios, Total parcial, Total, IVA,
  Total + IVA) coinciden con cálculo manual independiente en el 100% de los casos del
  fixture canónico y al menos tres escrituras con valores distintos.

- **SC-003**: La secretaria puede identificar en menos de 5 segundos, sin capacitación
  adicional, qué ítems de Honorarios van al Colegio gracias al resaltado visual.

- **SC-004**: Tras el cambio, el saldo pendiente del cliente y el monto en libro de
  entrada coinciden con **Total + IVA** en el 100% de escrituras de prueba revisadas.

- **SC-005**: Cero discrepancias entre ítems de línea individuales y la versión
  anterior del sistema (mismos montos por concepto antes de aplicar nuevas fórmulas de
  Totales).
