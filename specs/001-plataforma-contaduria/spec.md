# Feature Specification: Plataforma Contable — Escribanía

**Feature Branch**: `001-plataforma-contaduria`  
**Created**: 2026-07-18  
**Status**: Draft  

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Gestión de Escrituras (Priority: P1)

Una secretaria ingresa a la plataforma, crea una nueva escritura cargando los datos
del inmueble (valor en dólares, tipos de cambio, escribano asignado) y el sistema
genera automáticamente la factura principal con todos los montos calculados. La
secretaria puede ver, filtrar, y editar escrituras abiertas, así como registrar gastos
adicionales en cualquier momento. Cuando el trabajo está terminado, cierra la escritura
y ésta deja de aparecer en los cálculos activos del mes.

**Why this priority**: Es el núcleo operativo del sistema; sin escrituras no existe
liquidación ni pago de salarios. Todo lo demás depende de este flujo.

**Independent Test**: Se puede crear una escritura completa con su factura calculada,
agregar un gasto adicional, y cerrarla — de forma completamente independiente del resto
del sistema. El resultado es verificable sin la sección de liquidación.

**Acceptance Scenarios**:

1. **Given** que la secretaria está en la sección Escrituras, **When** completa el formulario
   de nueva escritura con valor USD, dólar MEP, dólar Nación y selecciona un escribano,
   **Then** el sistema genera la factura principal con todos los montos calculados
   (honorarios, leyes notariales, impuestos, gastos fijos) visibles en pantalla.

2. **Given** una escritura existente abierta, **When** la secretaria agrega un gasto adicional
   (concepto, monto, fecha), **Then** el gasto aparece en el apartado de gastos adicionales
   de esa escritura y queda registrado con su concepto y monto.

3. **Given** la lista de escrituras, **When** la secretaria aplica el filtro "Abiertas" o
   "Cerradas", **Then** la lista muestra únicamente las escrituras del estado seleccionado.

4. **Given** una escritura abierta, **When** la secretaria la marca como cerrada,
   **Then** la escritura pasa al estado "cerrada", no puede ser modificada, y no se incluye
   en el cálculo del próximo mes.

5. **Given** que la secretaria cambia un tipo de cambio en una escritura abierta,
   **When** guarda los cambios, **Then** todos los valores derivados de la factura se
   recalculan automáticamente.

---

### User Story 2 — Liquidación Mensual (Priority: P2)

Al acercarse el fin de mes, la secretaria abre la sección de Liquidación y visualiza un
resumen consolidado de todas las escrituras **activas en ese mes**: tanto las que siguen
abiertas como las que fueron abiertas y cerradas dentro del mismo mes calendario. Puede
ver el total por escribano, el total global, y al hacer clic en cualquier monto puede ver
exactamente a qué escritura pertenece.

> **Regla de inclusión en la liquidación mensual**: una escritura pertenece al mes M si
> fue creada en el mes M — independientemente de si está abierta o ya fue cerrada dentro
> de ese mes. Una escritura creada en un mes anterior y ya cerrada NO aparece en la
> liquidación del mes M.

**Why this priority**: Es la vista de control financiero del mes. Sin ella, el
seguimiento mensual no puede completarse.

**Independent Test**: Con al menos dos escrituras abiertas asignadas a distintos
escribanos, la sección Liquidación muestra el resumen correcto y cada monto es
referenciable a su escritura de origen.

**Acceptance Scenarios**:

1. **Given** que existen escrituras abiertas en el mes en curso, **When** la secretaria
   entra a Liquidación, **Then** ve un resumen con el total de cada sección de la factura
   (honorarios, leyes notariales, impuestos, gastos fijos) agrupado por escribano.

2. **Given** una escritura creada y cerrada dentro del mismo mes, **When** la secretaria
   visualiza la Liquidación de ese mes, **Then** la escritura aparece en el resumen con
   sus montos incluidos en los totales del escribano asignado, aunque su estado sea
   "cerrada".

3. **Given** una escritura creada en un mes anterior que ya fue cerrada, **When** la
   secretaria visualiza la Liquidación del mes actual, **Then** esa escritura NO aparece
   en los totales del mes actual.

4. **Given** el resumen de liquidación, **When** la secretaria hace clic en un monto,
   **Then** puede ver el detalle de la escritura que originó ese monto.

5. **Given** que se crea una nueva escritura o se agrega un gasto, **When** la secretaria
   mira la sección de Liquidación en la misma sesión, **Then** los totales se actualizan
   en tiempo real sin necesidad de recargar la página.

6. **Given** el final de un mes, **When** la secretaria genera el cierre mensual,
   **Then** las escrituras cerradas quedan archivadas y las abiertas continúan activas
   para el mes siguiente.

---

### User Story 3 — Pago de Salarios (Priority: P3)

La secretaria entra a la sección Pago de Salarios para el mes y ve el desglose del pago
para cada escribano (Costanza, Gabriel, Victoria) basado en las escrituras que trabajó,
y el salario fijo dividido entre las dos secretarias (Graciela y Guadalupe).

**Why this priority**: Cierra el ciclo mensual. Depende de que US1 y US2 estén
operativos, pero puede ser validado de forma independiente una vez que existan
escrituras de datos de prueba.

**Independent Test**: Con datos de prueba de escrituras asignadas, la sección de Pago
de Salarios muestra importes por persona con trazabilidad a escrituras origen y los
salarios fijos de las secretarias.

**Acceptance Scenarios**:

1. **Given** escrituras del mes asignadas a distintos escribanos, **When** la secretaria
   entra a Pago de Salarios, **Then** ve una card por cada escribano con el detalle de
   qué escrituras trabajó y el importe a cobrar.

2. **Given** la card de un escribano, **When** la secretaria hace clic en una escritura
   listada, **Then** navega directamente a esa escritura.

3. **Given** la sección de Pago de Salarios, **When** la secretaria visualiza los salarios
   fijos, **Then** ve el salario total ($2.000.000 ARS) y la división entre Graciela y
   Guadalupe ($1.000.000 ARS cada una).

4. **Given** que el monto del salario fijo es modificado por un administrador,
   **When** la secretaria vuelve a la sección, **Then** el nuevo monto se refleja
   automáticamente sin cambios en el código.

---

### User Story 4 — Acceso y Autenticación (Priority: P4)

La secretaria accede a la plataforma desde un navegador web usando un nombre de usuario
y contraseña simples. No requiere conocimiento de AWS, credenciales cloud ni
configuraciones técnicas. El sistema recuerda la sesión durante la jornada laboral.

**Why this priority**: Prerrequisito funcional pero de menor riesgo; puede ser
implementado con valores mínimos y refinado sin bloquear el desarrollo de US1-US3.

**Independent Test**: Un usuario puede iniciar sesión, navegar por la plataforma, y su
sesión se mantiene activa durante la jornada.

**Acceptance Scenarios**:

1. **Given** que la secretaria accede a la URL de la plataforma, **When** ingresa su
   usuario y contraseña válidos, **Then** accede al dashboard principal sin necesidad de
   pasos adicionales.

2. **Given** una sesión activa, **When** la secretaria cierra el navegador y lo vuelve
   a abrir dentro del día laboral, **Then** sigue autenticada sin necesidad de volver a
   ingresar sus credenciales.

3. **Given** credenciales incorrectas, **When** intenta ingresar, **Then** recibe un
   mensaje claro de error sin información técnica.

4. **Given** una sesión inactiva por más de 8 horas, **When** la secretaria intenta
   continuar, **Then** es redirigida al login con un mensaje informativo.

---

### Edge Cases

- ¿Qué sucede si se ingresa un valor en dólares de cero o negativo? El sistema debe
  rechazarlo con un mensaje claro antes de guardar.
- ¿Qué sucede si el dólar MEP o el dólar Nación son iguales a cero? Bloquear el cálculo
  con validación explicativa.
- ¿Qué sucede con una escritura que fue creada en un mes anterior y sigue abierta?
  Debe aparecer en el mes actual con sus valores originales, y la liquidación del mes
  actual la incluye en su totalización.
- ¿Qué sucede con una escritura creada y cerrada dentro del mismo mes? Se incluye en la
  liquidación de ese mes porque el trabajo fue realizado en ese período. Una escritura
  de mes anterior ya cerrada NO se incluye en la liquidación del mes actual.
- ¿Qué pasa si se intenta editar una escritura cerrada? La plataforma muestra los datos
  en modo sólo lectura y no presenta controles de edición.
- ¿Qué sucede con los gastos administrativos fijos si sus montos cambian? El sistema
  debe permitir actualizar los valores fijos desde una configuración sin modificar el
  código, y los cambios aplican sólo a escrituras nuevas (las cerradas conservan sus
  valores históricos).

---

## Requirements *(mandatory)*

### Functional Requirements

**Escrituras**

- **FR-001**: El sistema DEBE permitir crear una nueva escritura ingresando: **nombre
  de la escritura** (campo obligatorio, texto libre), valor en USD, dólar MEP, dólar
  Nación y el escribano asignado (Costanza, Gabriel o Victoria).
- **FR-002**: Al crear una escritura, el sistema DEBE calcular y persistir automáticamente
  la factura principal completa (honorarios, leyes notariales, impuestos y gastos fijos)
  usando las fórmulas definidas en la constitución.
- **FR-003**: El sistema DEBE permitir editar los valores de entrada (USD, tipos de
  cambio) de una escritura abierta, recalculando todos los derivados automáticamente.
- **FR-004**: El sistema DEBE permitir agregar gastos adicionales a una escritura,
  registrando: concepto, monto, fecha y dirección (entrada/salida).
- **FR-005**: El sistema DEBE permitir filtrar escrituras por estado: abiertas, cerradas,
  o todas.
- **FR-006**: El sistema DEBE permitir cerrar una escritura; una escritura cerrada
  DEBE quedar en modo sólo lectura e inmutable.
- **FR-007**: Las escrituras abiertas al final de un mes DEBEN continuar activas en el
  mes siguiente sin intervención manual.
- **FR-008**: El sistema DEBE mostrar en cada escritura el desglose completo de la
  factura principal en el mismo formato estructurado que la planilla de Google Sheets
  actualmente en uso.

**Liquidación**

- **FR-009**: El sistema DEBE mostrar un resumen de liquidación mensual que totalice
  todas las escrituras **creadas en ese mes calendario** (tanto abiertas como cerradas
  dentro del mes), agrupadas por escribano. Las escrituras creadas en meses anteriores
  y ya cerradas NO deben incluirse en el mes actual.
- **FR-010**: Cada línea del resumen de liquidación DEBE ser referenciable a la escritura
  de origen (navegar al detalle con un clic).
- **FR-011**: El resumen de liquidación DEBE actualizarse en tiempo real cuando se creen
  o modifiquen escrituras, sin recarga de página.

**Pago de Salarios**

- **FR-012**: El sistema DEBE mostrar por cada escribano el detalle de escrituras
  trabajadas en el mes y el importe correspondiente. El importe de cada escribano se
  calcula como la suma del **honorario principal + certificación** de cada escritura
  asignada a ese escribano en el mes, sin retenciones adicionales.

## Clarifications

### Session 2026-07-18

- Q: ¿Es necesario exportar o imprimir documentos en esta versión? → A: No — solo visualización en pantalla; exportación/impresión fuera del alcance inicial.
- Q: ¿Se usará Figma para el diseño del frontend? → A: No — el frontend se implementa directamente siguiendo la spec y el plan, sin referencias Figma.
- Q: ¿Qué estrategia de testing se aplica a esta feature? → A: TDD completo — tests escritos antes de la implementación en todo el proyecto (motor de cálculo, API, liquidación, salarios).
- Q: ¿Cómo se identifica/nombra cada escritura en la interfaz? → A: Nombre libre ingresado manualmente por la secretaria al crear la escritura (campo obligatorio).
- Q: ¿Cuántos perfiles de acceso distintos existen? → A: Un solo perfil — todos los usuarios autenticados tienen acceso completo a todas las secciones incluyendo configuración.
- Q: ¿Cuál es la base de cálculo del importe a pagar a cada escribano en la liquidación mensual? → A: Honorario principal + Certificación de cada escritura del mes asignada al escribano, sin retenciones ni descuentos de la escribanía.
- **FR-013**: El sistema DEBE mostrar el salario fijo total de secretarias y su división
  entre Graciela y Guadalupe; estos montos DEBEN ser configurables sin modificar el código.
- **FR-014**: La sección de Pago de Salarios DEBE actualizarse en tiempo real
  cuando cambia la sección de escrituras o liquidación.
- **FR-015**: Desde el detalle de pago de cada escribano, el sistema DEBE permitir
  navegar a cualquier escritura referenciada.

**Autenticación y Acceso**

- **FR-016**: El acceso DEBE requerir usuario y contraseña; no puede haber rutas
  públicas que expongan datos financieros. Todos los usuarios autenticados tienen
  acceso completo a todas las secciones, incluyendo la configuración de tasas y salarios.
- **FR-017**: La sesión DEBE mantenerse activa durante 8 horas de inactividad y
  expirar luego de ese período.
- **FR-018**: La interfaz de login DEBE ser simple y libre de terminología técnica
  o referencias a infraestructura cloud.

**Configuración**

- **FR-019**: Los valores fijos y porcentajes de la factura (tasas, mínimos, montos
  de gastos administrativos, salarios) DEBEN estar almacenados en una tabla de
  configuración editable, no en el código fuente.
- **FR-020**: Los cambios en la configuración DEBEN aplicar sólo a escrituras nuevas;
  las escrituras ya existentes DEBEN conservar los valores con los que fueron calculadas.

**Seguridad y Despliegue**

- **FR-021**: El backend DEBE estar desplegado en una red privada de AWS sin acceso
  directo desde internet (sin IP pública expuesta para el API); el acceso externo se
  resuelve via un load balancer o gateway controlado.
- **FR-022**: Toda comunicación cliente-servidor DEBE ocurrir sobre HTTPS.
- **FR-023**: Las credenciales de base de datos y claves de sesión DEBEN inyectarse
  por variables de entorno; NUNCA deben estar en el código fuente.
- **FR-024**: La exportación o impresión de documentos (facturas, liquidaciones) queda
  **fuera del alcance de esta versión**; el sistema provee visualización en pantalla únicamente.

### Key Entities

- **Escritura**: entidad principal; contiene un **nombre libre** ingresado por la secretaria
  al momento de la creación (campo obligatorio, ej: "Venta López - Martínez"), los inputs
  (USD, tipos de cambio), estado (abierta/cerrada), escribano asignado, mes/año de creación.
- **FacturaPrincipal**: generada automáticamente al crear una Escritura; almacena todos
  los montos calculados (cada ítem de la factura) como valores persistidos para
  trazabilidad histórica.
- **GastoAdicional**: entrada de gasto asociada a una Escritura; contiene concepto,
  monto, fecha y dirección (entrada/salida).
- **Escribano**: entidad de configuración; valores posibles: Costanza, Gabriel, Victoria.
- **ConfiguracionFinanciera**: tabla de parámetros del sistema (tasas, mínimos,
  montos fijos, salarios); versionable.
- **LiquidacionMensual**: snapshot generado al cerrar el mes; referencia las escrituras
  incluidas y los totales por escribano.
- **PagoSalario**: registro del pago mensual por persona (escribanos y secretarias)
  con referencias a escrituras origen.
- **Usuario**: credenciales de acceso a la plataforma; perfil único con acceso
  completo a todas las secciones (escrituras, liquidación, salarios, configuración);
  sin exposición de detalles cloud.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Una secretaria sin experiencia IT puede crear una escritura completa
  (con factura calculada) en menos de 3 minutos desde la primera vez que usa el sistema.
- **SC-002**: Los montos de la factura principal coinciden al 100% con los valores
  de la planilla de Google Sheets para el caso ejemplo de USD 105.000 de la
  constitución del proyecto.
- **SC-003**: Cualquier cambio en una escritura (creación, edición, cierre) se refleja
  en la sección de Liquidación y Pago de Salarios en menos de 2 segundos, sin recargar
  la página.
- **SC-004**: El 100% de los montos en Liquidación y Pago de Salarios tienen un enlace
  directo a la escritura que los generó.
- **SC-005**: El sistema funciona de forma idéntica en un entorno local (Docker Compose)
  y en el entorno productivo de AWS, usando exclusivamente variables de entorno para
  diferenciar configuraciones.
- **SC-006**: Un usuario nuevo puede iniciar sesión y navegar a cualquier sección de la
  plataforma en menos de 30 segundos sin asistencia técnica.
- **SC-007**: Los valores de tasas, porcentajes y montos fijos pueden ser actualizados
  por un administrador sin modificar el código y sin reiniciar el sistema.
- **SC-008**: Una escritura cerrada no puede ser modificada; cualquier intento resulta
  en un mensaje informativo sin pérdida de datos.

---

## Testing Strategy

**Approach**: TDD — Test-Driven Development completo.

**Rationale**: Esta plataforma maneja cálculos financieros con impacto directo en pagos
reales (honorarios, impuestos, salarios). El motor de cálculo de la factura principal
debe coincidir al 100% con los valores de la planilla de referencia; TDD garantiza que
cada fórmula sea verificada antes de ser integrada. La constitución incluye un fixture
canónico con valores exactos que hace TDD inmediatamente aplicable desde el primer día.

**Scope**: Aplica a todo el proyecto — motor de cálculo financiero, lógica de liquidación,
lógica de pago de salarios, y endpoints de la API. Los tests deben ser escritos y
comprobados en estado FAILING antes de escribir la implementación correspondiente.

**Scope note**: Esta decisión DEBE ser respetada por `/spec-kitti.plan` (contratos de test)
y `/spec-kitti.tasks` (tareas TDD generadas en cada user story).

---

## Assumptions

- La plataforma es de uso interno; el número esperado de usuarios concurrentes es menor
  a 10 personas.
- La moneda base de la plataforma es ARS (pesos argentinos); los valores en USD son
  inputs que se convierten inmediatamente.
- El acceso a internet de los usuarios es desde una red de oficina estándar con navegador
  web moderno (Chrome/Firefox/Edge).
- Los tipos de cambio (MEP y Banco Nación) se ingresan manualmente por la secretaria en
  cada escritura; no se consumen APIs de cotizaciones externas en esta primera versión.
- La fórmula de pago al escribano es: **suma del honorario principal + certificación**
  de todas las escrituras asignadas a ese escribano en el mes, sin retenciones ni
  descuentos adicionales por parte de la escribanía. El escribano percibe el 100% de
  esa base.
- El "Libro de Entrada" y "Libro de Salida" son vistas derivadas de los datos de
  escrituras y gastos adicionales; no requieren carga manual adicional en esta primera versión.
