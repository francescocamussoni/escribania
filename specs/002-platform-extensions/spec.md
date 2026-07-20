# Feature Specification: Extensiones de Plataforma — Cotizaciones, Configuración y Libros Contables

**Feature Branch**: `002-platform-extensions`  
**Created**: 2026-07-18  
**Status**: Draft  

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Cotización de Dólar via API Oficial (Priority: P1)

La secretaria, al crear o editar una escritura, puede obtener el valor del dólar MEP y del
dólar Banco Nación directamente desde una fuente oficial seleccionando la fecha deseada.
Si la consulta falla o prefiere ingresarlo manualmente, el campo sigue siendo editable
con teclado como en la versión anterior.

**Why this priority**: Elimina el error humano en la carga de tipos de cambio, que son la
base de todos los cálculos financieros de la plataforma. Un tipo de cambio incorrecto
contamina la factura completa. La integración automática reduce fricciones en el flujo
de creación de escrituras.

**Independent Test**: Se puede probar completamente abriendo el formulario de una
escritura, seleccionando una fecha, consultando la API, y verificando que los campos
MEP y Banco Nación se completan con los valores devueltos — sin necesidad de completar
la escritura ni revisar liquidaciones.

**Acceptance Scenarios**:

1. **Given** que la secretaria está en el formulario de nueva escritura, **When** selecciona
   una fecha y presiona "Consultar cotización", **Then** los campos de dólar MEP y dólar
   Banco Nación se completan automáticamente con los valores oficiales de esa fecha.

2. **Given** que la secretaria consultó la API y obtuvo valores automáticos, **When** desea
   ajustar el valor manualmente, **Then** puede editar directamente los campos de tipo de
   cambio sin restricciones.

3. **Given** que la API de cotizaciones no responde o devuelve error, **When** la secretaria
   presiona "Consultar cotización", **Then** recibe un mensaje claro indicando que la
   consulta falló y los campos permanecen editables para ingreso manual.

4. **Given** que la secretaria selecciona una fecha futura o una fecha sin cotización
   disponible, **When** consulta la API, **Then** el sistema informa que no hay cotización
   disponible para esa fecha y no modifica los campos.

5. **Given** que la secretaria edita una escritura abierta, **When** consulta la cotización
   para una fecha diferente a la original, **Then** puede actualizar los tipos de cambio
   y el sistema recalcula la factura automáticamente.

---

### User Story 2 — Configuración de Escribanos (Priority: P2)

Un usuario administrador puede agregar nuevos escribanos a la plataforma o eliminar
escribanos existentes. Los escribanos configurados aparecen como opciones válidas al
crear o editar escrituras.

**Why this priority**: La constitución actual hardcodea tres escribanos (Costanza, Gabriel,
Victoria). La incorporación o salida de un escribano requeriría cambios de código sin
esta feature. La configuración dinámica desacopla el negocio del código.

**Independent Test**: Se puede probar añadiendo un nuevo escribano desde la sección de
configuración y verificando que aparece como opción en el selector de escribano al
crear una escritura, sin necesidad de revisar liquidaciones ni libros.

**Acceptance Scenarios**:

1. **Given** que el usuario está en la sección de Configuración > Escribanos, **When**
   ingresa el nombre de un nuevo escribano y confirma, **Then** el escribano aparece en
   la lista y queda disponible como opción al asignar escrituras.

2. **Given** que existe un escribano en la lista, **When** el usuario lo desactiva,
   **Then** el escribano ya no aparece como opción para nuevas escrituras.

3. **Given** que un escribano tiene escrituras asignadas, **When** el usuario intenta
   desactivarlo, **Then** el sistema muestra una advertencia indicando que existen
   escrituras asociadas y solicita confirmación explícita antes de proceder.

4. **Given** que el usuario desactiva un escribano con escrituras históricas, **When** la
   desactivación se confirma, **Then** las escrituras existentes conservan la referencia al
   escribano mostrando su nombre con la etiqueta "(inactivo)"; el escribano desactivado
   no puede ser asignado a nuevas escrituras.

5. **Given** la lista de escribanos configurados, **When** la secretaria abre el formulario
   de nueva escritura, **Then** el selector de escribano muestra únicamente los escribanos
   activos en el sistema.

---

### User Story 3 — Configuración de Empleados y Sueldos (Priority: P3)

Un usuario administrador puede ver la lista de empleados (secretarias) y modificar el
sueldo de cada una. También puede agregar o eliminar empleadas. Los sueldos configurados
se usan en el cálculo de Pago de Salarios del mes correspondiente.

**Why this priority**: La constitución hardcodea el salario de Graciela y Guadalupe en
$2.000.000 ARS total. Cuando ese monto cambia (algo que ocurre regularmente por
inflación), actualmente requeriría intervención técnica. Esta feature lo hace
autoservicio para el usuario.

**Independent Test**: Se puede probar modificando el sueldo de una empleada desde
Configuración > Empleados y verificando que la sección Pago de Salarios refleja el
nuevo monto — sin necesidad de crear escrituras adicionales.

**Acceptance Scenarios**:

1. **Given** que el usuario está en Configuración > Empleados, **When** selecciona una
   empleada y modifica su sueldo, **Then** el nuevo monto queda guardado y se refleja en
   la próxima vista de Pago de Salarios.

2. **Given** que el usuario modifica el sueldo de una empleada durante el mes en curso,
   **When** visualiza la sección Pago de Salarios, **Then** el nuevo monto aplica a ese
   mes y los meses futuros; los cierres de meses anteriores conservan los valores históricos.

3. **Given** que el usuario está en Configuración > Empleados, **When** agrega una nueva
   empleada con su nombre y sueldo, **Then** la empleada aparece en la sección Pago de
   Salarios del mes en curso.

4. **Given** que existe una empleada en la lista, **When** el usuario la elimina,
   **Then** la empleada ya no aparece en los cálculos futuros de Pago de Salarios; los
   registros históricos previos conservan su información.

5. **Given** que el usuario intenta guardar un sueldo con valor cero o negativo, **When**
   confirma, **Then** el sistema rechaza la operación con un mensaje de validación claro.

---

### User Story 4 — Libro de Entrada (Priority: P4)

La secretaria puede ver el Libro de Entrada: un registro consolidado de todos los montos
de dinero que ingresan a la escribanía y se destinan a la liquidación final. Cada entrada
explicita el monto, el concepto (honorarios, sellos, etc.), y desde qué escritura proviene,
con un enlace directo a esa escritura.

**Why this priority**: Proporciona trazabilidad financiera completa de todos los ingresos.
Es la herramienta de control que permite a la escribanía saber exactamente cuánto dinero
tiene disponible para distribuir al final del mes.

**Independent Test**: Con al menos dos escrituras con datos cargados, el Libro de Entrada
muestra las entradas correspondientes con sus montos, conceptos y vínculos a las
escrituras de origen — verificable sin necesidad de realizar una liquidación mensual.

**Acceptance Scenarios**:

1. **Given** que existen escrituras con facturas calculadas, **When** la secretaria abre
   el Libro de Entrada, **Then** ve una lista de entradas con: monto, concepto (ej.
   "Honorarios Profesionales", "Certificación"), nombre de escritura de origen, y un
   hipervínculo a esa escritura.

2. **Given** el Libro de Entrada, **When** la secretaria hace clic en el hipervínculo
   de una entrada, **Then** navega directamente al detalle de la escritura correspondiente.

3. **Given** que se crea una nueva escritura o se modifica una existente, **When** la
   secretaria visualiza el Libro de Entrada, **Then** los cambios se reflejan en tiempo
   real sin recargar la página.

4. **Given** el Libro de Entrada, **When** la secretaria aplica un filtro por mes,
   **Then** solo se muestran las entradas correspondientes a ese mes calendario.

5. **Given** el Libro de Entrada del mes, **When** la secretaria visualiza el total
   acumulado, **Then** el sistema muestra un resumen con el total de entradas del período
   seleccionado.

---

### User Story 5 — Libro de Salida (Priority: P5)

La secretaria puede ver el Libro de Salida: un registro de todos los montos que salen
de la escribanía (impuestos pagados, aportes al Colegio, otros egresos). Cada salida
explicita el monto, el concepto, y desde qué escritura proviene, con enlace directo.

**Why this priority**: Complementa el Libro de Entrada para el cuadre contable del mes.
Sin él, no es posible calcular el resultado neto del período. Es de menor prioridad que
el de Entrada porque los ingresos son más urgentes para la liquidación.

**Independent Test**: Con al menos dos escrituras, el Libro de Salida muestra los egresos
(impuestos, aportes) con sus montos, conceptos y vínculos — verificable de forma
independiente al Libro de Entrada.

**Acceptance Scenarios**:

1. **Given** que existen escrituras con facturas calculadas, **When** la secretaria abre
   el Libro de Salida, **Then** ve una lista de salidas con: monto, concepto (ej.
   "Impuesto Sellos", "Aporte Leyes Notariales"), nombre de escritura de origen, y un
   hipervínculo a esa escritura.

2. **Given** el Libro de Salida, **When** la secretaria hace clic en el hipervínculo,
   **Then** navega directamente al detalle de la escritura correspondiente.

3. **Given** que se modifica una escritura, **When** la secretaria visualiza el Libro
   de Salida, **Then** los cambios se reflejan en tiempo real sin recargar la página.

4. **Given** el Libro de Salida, **When** la secretaria filtra por mes,
   **Then** solo se muestran las salidas del mes seleccionado con su total acumulado.

---

### Edge Cases

- ¿Qué sucede si la API de cotizaciones devuelve un valor de cero o negativo? El sistema
  debe ignorar ese valor, mostrar un error, y dejar los campos en su estado anterior.
- ¿Qué pasa si se elimina un escribano que tiene escrituras abiertas en el mes en curso?
  Las escrituras abiertas deben mantener la referencia histórica; el escribano eliminado
  no puede recibir nuevas escrituras.
- ¿Qué sucede si se modifica el sueldo de una empleada retroactivamente (en un mes ya
  cerrado)? El sistema no permite modificar cierres históricos; el cambio aplica solo
  desde el mes en curso.
- ¿Qué pasa si la secretaria no selecciona una fecha antes de consultar la cotización?
  El sistema usa la fecha del día como valor predeterminado.
- ¿Qué sucede si hay entradas del Libro de Entrada que provienen de gastos adicionales
  manuales (no de la factura principal)? Deben aparecer igualmente con su concepto
  explicitado y referencia a la escritura de origen.
- ¿Qué pasa si se intenta agregar un escribano con el mismo nombre que uno ya existente?
  El sistema debe detectar el duplicado y rechazar la operación con mensaje claro.
- ¿Qué sucede si la fuente oficial de cotizaciones cambia de URL o formato? El módulo de
  integración debe ser configurable sin cambios de código (URL/endpoint parametrizable).

---

## Requirements *(mandatory)*

### Functional Requirements

**Cotización de Dólar via API**

- **FR-001**: El sistema DEBE ofrecer un botón "Consultar cotización" en el formulario de
  escritura (creación y edición) que, dado una fecha seleccionable, consulte una fuente
  oficial y complete automáticamente los campos de dólar MEP y dólar Banco Nación.
- **FR-002**: La fecha de consulta DEBE ser seleccionable por la secretaria; el valor por
  defecto es la fecha del día.
- **FR-003**: Si la consulta a la API falla (timeout, error de red, fecha sin cotización),
  el sistema DEBE mostrar un mensaje de error descriptivo y dejar los campos de tipo de
  cambio en su valor anterior, permitiendo el ingreso manual.
- **FR-004**: Los campos de dólar MEP y dólar Banco Nación DEBEN seguir siendo editables
  manualmente en todo momento, independientemente de si se usó la consulta automática.
- **FR-005**: La URL/endpoint de la fuente oficial de cotizaciones DEBE ser configurable
  mediante una variable de entorno, sin requerir cambios de código.
- **FR-006**: La consulta a la API de cotizaciones DEBE realizarse desde el backend (nunca
  desde el frontend) para evitar problemas de CORS y ocultar la fuente de datos.
- **FR-006b**: El backend DEBE cachear el resultado de cada consulta de cotización por
  fecha con un TTL de **8 horas**. Consultas repetidas a la misma fecha dentro de ese
  período DEBEN devolver el valor cacheado sin llamar nuevamente a la API externa.

**Configuración de Escribanos**

- **FR-007**: El sistema DEBE exponer una sección de Configuración > Escribanos donde
  se listen todos los escribanos activos.
- **FR-008**: El sistema DEBE permitir agregar un nuevo escribano con un nombre único.
- **FR-009**: El sistema DEBE permitir desactivar (soft delete) un escribano; si el escribano
  tiene escrituras asociadas, debe requerir confirmación explícita antes de proceder.
- **FR-010**: Un escribano desactivado NO DEBE aparecer como opción al crear o editar
  escrituras; las escrituras históricas existentes DEBEN conservar la referencia al
  escribano, mostrando su nombre con la etiqueta "(inactivo)" en la UI.
- **FR-011**: El selector de escribano en el formulario de escritura DEBE reflejar en
  tiempo real los escribanos activos configurados en el sistema.

**Configuración de Empleados y Sueldos**

- **FR-012**: El sistema DEBE exponer una sección de Configuración > Empleados donde se
  listen todos los empleados con su nombre y sueldo actual.
- **FR-013**: El sistema DEBE permitir modificar el sueldo de un empleado existente;
  el nuevo valor aplica **desde el momento del cambio** usando el monto completo para el
  mes en curso (sin prorrateo). Los meses ya cerrados conservan su valor histórico.
- **FR-014**: El sistema DEBE permitir agregar un nuevo empleado con nombre y sueldo.
- **FR-015**: El sistema DEBE permitir eliminar un empleado; los registros históricos
  de meses cerrados DEBEN conservar la información del empleado eliminado.
- **FR-016**: El sistema DEBE rechazar sueldos con valor cero o negativo con un mensaje
  de validación claro.
- **FR-017**: Los cambios en sueldos NO DEBEN modificar registros de meses ya cerrados.

**Libro de Entrada**

- **FR-018**: El sistema DEBE derivar el Libro de Entrada directamente de los datos de
  escrituras y gastos adicionales; no se requiere carga manual duplicada.
- **FR-018b**: El Libro de Entrada DEBE incluir exclusivamente los ítems que representan
  dinero que queda en la escribanía para distribuir: **honorarios profesionales**,
  **certificación**, y gastos adicionales marcados como "entrada". Los impuestos, sellos
  y aportes notariales NO se incluyen en el Libro de Entrada.
- **FR-018c**: El Libro de Entrada DEBE incluir todas las escrituras del mes filtrado,
  tanto abiertas como cerradas. Criterio idéntico al de la Liquidación Mensual.
- **FR-019**: Cada entrada del Libro de Entrada DEBE incluir: monto, concepto (ej.
  "Honorarios Profesionales", "Certificación"), nombre de la escritura de origen, y
  un hipervínculo navegable a esa escritura.
- **FR-020**: El concepto de cada entrada DEBE coincidir con el ítem de la factura
  principal o del gasto adicional que lo originó (trazabilidad a nivel de ítem).
- **FR-021**: El Libro de Entrada DEBE ser filtrable por mes calendario.
- **FR-022**: El Libro de Entrada DEBE mostrar el total acumulado del período seleccionado.
- **FR-023**: El Libro de Entrada DEBE actualizarse en tiempo real ante cualquier cambio
  en las escrituras del mes.

**Libro de Salida**

- **FR-024**: El sistema DEBE derivar el Libro de Salida directamente de los datos de
  escrituras y gastos adicionales; no se requiere carga manual duplicada.
- **FR-024b**: El Libro de Salida DEBE incluir los ítems que representan dinero que la
  escribanía transfiere a terceros: **impuestos y sellos fiscales**, **aportes a leyes
  notariales**, y gastos adicionales marcados como "salida". Los honorarios y
  certificación NO se incluyen en el Libro de Salida.
- **FR-024c**: El Libro de Salida DEBE incluir todas las escrituras del mes filtrado,
  tanto abiertas como cerradas. Criterio idéntico al de la Liquidación Mensual.
- **FR-025**: Cada salida del Libro de Salida DEBE incluir: monto, concepto (ej.
  "Impuesto Sellos", "Aporte Leyes Notariales", "Pago a Banco"), nombre de la escritura
  de origen, y un hipervínculo navegable a esa escritura.
- **FR-026**: El Libro de Salida DEBE ser filtrable por mes calendario.
- **FR-027**: El Libro de Salida DEBE mostrar el total acumulado del período seleccionado.
- **FR-028**: El Libro de Salida DEBE actualizarse en tiempo real ante cualquier cambio
  en las escrituras del mes.

### Key Entities

- **CotizacionDolar**: valor puntual del dólar MEP y dólar Banco Nación para una fecha
  dada; obtenido de la API oficial o ingresado manualmente. No se persiste como entidad
  independiente — forma parte de la `FacturaPrincipal` de cada `Escritura`.
- **Escribano**: entidad de configuración con nombre único y estado `activo`/`inactivo`
  (soft delete); referenciada por cada `Escritura`. Un escribano inactivo conserva su
  registro en la base de datos para preservar integridad referencial histórica; no puede
  ser asignado a nuevas escrituras.
- **Empleado**: entidad de configuración con nombre y sueldo vigente; usado en el cálculo
  de Pago de Salarios. El historial de cambios de sueldo debe preservarse para conservar
  la trazabilidad de meses cerrados.
- **SueldoHistorico**: registro del sueldo de un empleado para un mes/año específico;
  generado automáticamente al cerrar un período. Al modificar el sueldo a mitad de mes,
  el mes en curso adopta el nuevo valor completo (sin prorrateo); el snapshot histórico
  se genera al cierre del período con el valor vigente en ese momento.
- **EntradaLibro**: línea derivada del Libro de Entrada; contiene monto, concepto, y
  referencia a la `Escritura` y al ítem de factura de origen.
- **SalidaLibro**: línea derivada del Libro de Salida; contiene monto, concepto, y
  referencia a la `Escritura` y al ítem de factura o gasto adicional de origen.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: La secretaria puede obtener la cotización oficial del día para una escritura
  en menos de 5 segundos desde que presiona "Consultar cotización", en condiciones normales
  de red.
- **SC-002**: El 100% de las entradas del Libro de Entrada tienen un hipervínculo funcional
  a la escritura de origen y explicitan el concepto del ítem (honorarios, sellos, etc.).
- **SC-003**: El 100% de las salidas del Libro de Salida tienen un hipervínculo funcional
  a la escritura de origen y explicitan el concepto del ítem.
- **SC-004**: Un usuario puede agregar o eliminar un escribano o empleado en menos de
  60 segundos desde que accede a la sección de Configuración.
- **SC-005**: La modificación de un sueldo se refleja en la sección Pago de Salarios
  del mes en curso en menos de 2 segundos, sin recargar la página.
- **SC-006**: Si la API de cotizaciones falla, la secretaria puede continuar ingresando
  los valores manualmente sin pérdida de datos ni bloqueo del flujo de trabajo.
- **SC-007**: Los Libros de Entrada y Salida se actualizan en tiempo real (menos de
  2 segundos) ante cualquier creación, edición, o cierre de escritura.
- **SC-008**: Los registros históricos de meses cerrados no se ven afectados por cambios
  en la configuración de escribanos, empleados o sueldos realizados posteriormente.

---

## Testing Strategy

**Approach**: TDD — Test-Driven Development completo (heredado de la feature 001).

**Scope específico de esta feature**:

- **Cotización API**: mock del cliente HTTP externo para cubrir escenarios de éxito,
  error de red, fecha sin cotización, y valor inválido (cero/negativo).
- **Configuración Escribanos/Empleados**: tests de creación, eliminación con confirmación,
  y validación de duplicados.
- **Libros Contables**: tests que verifican la derivación correcta de entradas y salidas
  desde datos de escrituras; tests de trazabilidad (cada línea referencia la escritura
  correcta); tests de totales por período.
- **Tiempo real**: los mismos SSE/WebSocket existentes de la feature 001 deben cubrir
  las actualizaciones de los Libros.

---

## Clarifications

### Session 2026-07-18

- Q: ¿Qué ítems de la factura principal pertenecen al Libro de Entrada y cuáles al Libro de Salida? → A: **Libro de Entrada** = honorarios profesionales + certificación + gastos adicionales marcados como "entrada" (dinero que queda en la escribanía para distribuir). **Libro de Salida** = impuestos y sellos fiscales + aportes a leyes notariales + gastos adicionales marcados como "salida" (dinero que la escribanía transfiere a terceros).
- Q: ¿El backend debe cachear las cotizaciones consultadas a la API externa? → A: Sí — caché en backend por fecha con TTL de **8 horas** (duración de la jornada laboral). Consultas a la misma fecha dentro de ese período devuelven el valor cacheado sin llamar a la API externa.
- Q: ¿Cuándo se incluye una escritura en los Libros de Entrada y Salida según su estado? → A: Ambos libros incluyen **todas las escrituras del mes filtrado** (abiertas y cerradas), derivando los valores desde la factura principal actual. Criterio idéntico al de la Liquidación Mensual de la feature 001.
- Q: ¿Cómo se elimina un escribano — soft delete o hard delete? → A: **Soft delete** — el escribano se marca como `inactivo` en la base de datos pero el registro persiste. Las escrituras históricas conservan la referencia por ID; la UI muestra el nombre con etiqueta "(inactivo)" donde corresponda. No se permite asignar un escribano inactivo a nuevas escrituras.
- Q: ¿Cuándo aplica el nuevo sueldo al modificarlo a mitad de mes? → A: El nuevo sueldo aplica **desde el momento del cambio**; el mes en curso usa el nuevo valor completo para el cálculo de Pago de Salarios (sin prorrateo). Los meses ya cerrados conservan sus valores históricos sin alteración.

---

## Assumptions

- La fuente oficial de cotizaciones es una API pública argentina (ej. dolarapi.com u
  otra con endpoint de tipo de cambio MEP y Banco Nación por fecha). El endpoint exacto
  se configura via variable de entorno y puede cambiarse sin despliegue de código.
- El **Libro de Entrada** representa el dinero que **queda en la escribanía para distribuir**:
  incluye exclusivamente **honorarios profesionales y certificación** de cada escritura,
  más cualquier gasto adicional marcado como "entrada" en la escritura. NO incluye
  impuestos ni sellos (ese dinero no pertenece a la escribanía).
- El **Libro de Salida** representa el dinero que **la escribanía transfiere a terceros**:
  incluye impuestos y sellos fiscales, aportes a leyes notariales, y cualquier gasto
  adicional marcado como "salida" en la escritura.
- La sección de Configuración es accesible para todos los usuarios autenticados (perfil
  único sin roles diferenciados, heredado de la feature 001).
- La eliminación de un escribano con escrituras abiertas es una operación poco frecuente
  y de alto impacto; el doble paso de confirmación es suficiente salvaguarda.
- Los Libros de Entrada y Salida son vistas derivadas en tiempo real; no se persisten
  como tablas independientes en la base de datos (se calculan desde las escrituras).
- El historial de sueldos se registra automáticamente al momento del **cierre mensual**,
  capturando el valor vigente en ese instante para garantizar trazabilidad de pagos históricos.
- La navegación principal se amplía con dos nuevas secciones: **Libro de Entrada** y
  **Libro de Salida** (además de las existentes: Escrituras, Liquidación, Pago de Salarios).
  La sección **Configuración** agrupa los sub-menús de Escribanos y Empleados.
