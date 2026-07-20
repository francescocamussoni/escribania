# Feature Specification: Mejoras de Usabilidad en Escrituras y Marca

**Feature Branch**: `004-escrituras-ui-mejoras`  
**Created**: 2026-07-20  
**Status**: Draft  
**Input**: User description: "Mejoras en listado de escrituras (fecha de creación, ordenamiento, filtros por escribano y estado, búsqueda por nombre), rebranding del header a Escribanía Barat, layout de detalle en dos columnas, renombrar Pagos al colegio a Pagos de la escribanía"

## Clarifications

### Session 2026-07-20

- Q: ¿Aplicar TDD y/o unit tests estrictos para esta feature? → A: Híbrido — unit tests en lógica central (filtros, orden, búsqueda); sin TDD estricto en layout/CSS.
- Q: ¿Cómo deben presentarse los filtros de escribano y estado en el listado? → A: Dos filas de píldoras — escribanos arriba (Todas + cada escribano), estado abajo (Todas / Abiertas / Cerradas), mismo estilo visual que los botones actuales.
- Q: ¿Alcance del rebranding "Escribanía Barat"? → A: Toda la aplicación — reemplazar "Contaduría Escribanía" en cualquier texto visible al usuario.
- Q: ¿Alcance del renombre "Pagos de la escribanía"? → A: Toda la aplicación — reemplazar "Pagos al Colegio" / "pago al Colegio" en detalle, libros, formularios y mensajes visibles.
- Q: ¿Persistencia de filtros y búsqueda al volver al listado? → A: Persistir en la sesión — conservar filtros de escribano/estado, texto de búsqueda y orden mientras la pestaña del navegador permanezca abierta.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Encontrar y Filtrar Escrituras con Mayor Precisión (Priority: P1)

La secretaria consulta el listado de escrituras para ubicar trámites por escribano, estado,
antigüedad o nombre. El listado muestra la fecha de creación junto a los datos financieros
existentes, permite ordenar por esa fecha, filtrar primero por escribano y luego por estado
(abiertas/cerradas), y buscar por el nombre de la escritura.

**Why this priority**: El listado de escrituras es la pantalla de entrada principal del
sistema. Mejorar filtros, búsqueda y visibilidad de la fecha de creación reduce el tiempo
diario de búsqueda y evita errores al trabajar con múltiples escribanos.

**Independent Test**: Se puede probar navegando al listado de escrituras, aplicando
combinaciones de filtros y búsqueda, y verificando que los resultados y el orden mostrado
coinciden con los criterios seleccionados — sin necesidad de abrir el detalle ni modificar
el layout.

**Acceptance Scenarios**:

1. **Given** un listado con escrituras de distintos escribanos y fechas, **When** la
   secretaria visualiza la tabla, **Then** cada fila muestra: Nombre, Escribano, Estado,
   Fecha de creación, Costo total, Total pagado, Saldo pendiente y Cobro (indicadores de
   pago al 100% / sobrepago).

2. **Given** el listado de escrituras, **When** la secretaria activa el ordenamiento por
   fecha de creación, **Then** las escrituras se reordenan cronológicamente y la secretaria
   puede alternar entre orden ascendente (más antiguas primero) y descendente (más recientes
   primero).

3. **Given** el listado de escrituras, **When** la secretaria visualiza los filtros, **Then** ve dos filas de botones tipo píldora: la fila superior con "Todas" más un botón por cada escribano, y la fila inferior con "Todas", "Abiertas" y "Cerradas" (mismo estilo que los filtros de estado actuales).

4. **Given** el listado de escrituras, **When** la secretaria selecciona un escribano en la fila superior (o "Todas"), **Then** solo se muestran las escrituras de ese escribano (o todas, si eligió "Todas").

5. **Given** un escribano seleccionado en la fila superior (o "Todas"), **When** la secretaria aplica un botón de la fila inferior de estado (Todas / Abiertas / Cerradas), **Then** el listado refleja la intersección de ambos criterios.

6. **Given** escrituras con nombres distintos, **When** la secretaria escribe en la barra de
   búsqueda un fragmento del nombre de una escritura, **Then** el listado muestra únicamente
   las escrituras cuyo nombre contiene ese texto (sin distinguir mayúsculas/minúsculas).

7. **Given** filtros de escribano, estado y texto de búsqueda activos simultáneamente,
   **When** la secretaria revisa el listado, **Then** solo aparecen escrituras que cumplen
   los tres criterios a la vez.

8. **Given** una búsqueda o combinación de filtros sin resultados, **When** el listado queda
   vacío, **Then** el sistema muestra un mensaje claro indicando que no hay escrituras que
   coincidan con los criterios actuales.

9. **Given** filtros, búsqueda u orden activos en el listado, **When** la secretaria abre el
   detalle de una escritura y vuelve al listado en la misma pestaña, **Then** se restauran
   los mismos criterios (escribano, estado, texto de búsqueda y orden por fecha).

---

### User Story 2 — Consultar el Detalle de una Escritura con Menos Desplazamiento (Priority: P2)

La secretaria abre el detalle de una escritura y encuentra la información organizada en un
layout más compacto: los bloques de saldo y datos de la escritura permanecen en la parte
superior; debajo, la factura principal ocupa una columna y, en la otra columna, los pagos del
cliente y — debajo de estos — los pagos de la escribanía. La sección de factura principal
presenta sus subsecciones en dos columnas para reducir el scroll vertical.

**Why this priority**: El detalle concentra la mayor cantidad de información operativa
(factura, pagos, saldo). Un layout más eficiente acelera la revisión diaria y reduce
errores por información fuera de vista.

**Independent Test**: Se puede probar abriendo una escritura con factura y pagos cargados
y verificando que las secciones principales son visibles con menos scroll que el layout
anterior, y que la factura principal muestra sus bloques en dos columnas.

**Acceptance Scenarios**:

1. **Given** el detalle de una escritura, **When** la secretaria visualiza la pantalla en un
   viewport de escritorio estándar, **Then** la estructura superior muestra en secuencia:
   encabezado con nombre y acciones, bloque de Saldo y bloque de Datos de la escritura.

2. **Given** el detalle de una escritura en viewport de escritorio, **When** la secretaria
   desplaza hacia la zona inferior, **Then** ve dos columnas principales: columna izquierda
   con "Factura principal" y columna derecha con "Pagos del cliente" seguido de "Pagos de la
   escribanía" (uno debajo del otro en la misma columna).

3. **Given** la sección Factura principal, **When** la secretaria la expande visualmente,
   **Then** las subsecciones de la factura (bases de cálculo, honorarios, leyes notariales,
   impuestos, gastos administrativos, total) se distribuyen en dos columnas para ocupar
   menos altura vertical que un listado de una sola columna.

4. **Given** una escritura con pagos del cliente y pagos de la escribanía registrados,
   **When** la secretaria revisa la columna derecha, **Then** ambos listados y sus formularios
   de alta (si la escritura está abierta) permanecen accesibles sin interferir con la factura
   principal.

5. **Given** un viewport estrecho (pantalla móvil o ventana reducida), **When** la secretaria
   visualiza el detalle, **Then** las columnas se apilan en un orden lógico (saldo y datos
   primero, luego factura principal, luego pagos del cliente, luego pagos de la escribanía)
   manteniendo toda la información accesible.

---

### User Story 3 — Identidad de Marca y Terminología Consistente (Priority: P3)

La secretaria y demás usuarios ven "Escribanía Barat" como nombre de la aplicación en
todos los textos visibles (en lugar de "Contaduría Escribanía"). En toda la interfaz, la
terminología "Pagos al Colegio" pasa a llamarse "Pagos de la escribanía" (títulos de
sección, formularios, libros contables y mensajes al usuario).

**Why this priority**: Refuerza la identidad del estudio y alinea la terminología con el
lenguaje interno del equipo. Es un cambio de bajo riesgo que complementa las mejoras
funcionales.

**Independent Test**: Se puede probar abriendo cualquier página autenticada y el detalle de
una escritura, verificando el texto del header y el título de la sección de pagos.

**Acceptance Scenarios**:

1. **Given** cualquier pantalla de la aplicación, **When** el usuario observa textos de marca
   o títulos que antes decían "Contaduría Escribanía", **Then** lee "Escribanía Barat"
   (navbar, login, títulos de página y demás superficies visibles al usuario).

2. **Given** cualquier pantalla que antes mostraba "Pagos al Colegio" o variantes, **When**
   el usuario lee títulos, formularios, libros o mensajes vacíos, **Then** ve "Pagos de la
   escribanía" (o "pago de la escribanía" en frases de acción, según gramática del contexto).

3. **Given** la sección renombrada, **When** el usuario registra o consulta un pago, **Then**
   la funcionalidad existente (montos, fechas, conceptos, restricciones de escritura cerrada)
   se mantiene sin cambios de comportamiento.

---

### Edge Cases

- ¿Qué ocurre si un escribano fue desactivado pero tiene escrituras históricas? El filtro
  principal debe seguir permitiendo ver esas escrituras al seleccionar ese escribano (o
  "Todas"); el nombre mostrado conserva la convención existente para escribanos inactivos.
- ¿Qué ocurre si la búsqueda por nombre coincide con muchas escrituras? El listado muestra
  todas las coincidencias respetando filtros y orden activos, sin límite artificial que
  oculte resultados en el volumen operativo habitual del estudio.
- ¿Qué ocurre si no hay escribanos activos configurados? El filtro principal muestra al menos
  la opción "Todas" y un estado vacío o mensaje informativo coherente con el resto de la app.
- ¿Qué ocurre al combinar orden por fecha con búsqueda vacía? Se muestran todas las escrituras
  que cumplen los filtros, ordenadas según la preferencia de fecha activa.
- ¿Qué ocurre en escrituras sin pagos de la escribanía? La sección renombrada se muestra
  igualmente, con listado vacío y formulario disponible si la escritura está abierta.
- ¿Qué ocurre al cerrar la pestaña del navegador? Los filtros, búsqueda y orden se reinician
  a los valores por defecto en la próxima visita.
- ¿Qué ocurre al navegar a otra sección (liquidación, libros) y volver a Escrituras en la
  misma pestaña? Se conservan filtros, búsqueda y orden activos.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El listado de escrituras MUST mostrar una columna "Fecha de creación" con la
  fecha en que se registró cada escritura, usando el mismo formato de fecha que el resto de
  la aplicación.

- **FR-002**: El listado MUST permitir ordenar las filas por fecha de creación, con al menos
  dos sentidos: ascendente y descendente. El orden activo MUST ser visible para el usuario
  (indicador en la columna o control equivalente).

- **FR-003**: El listado MUST ofrecer una fila superior de filtros tipo píldora con la opción
  "Todas" más un botón por cada escribano disponible en el sistema (activos e inactivos con
  escrituras asociadas, según la configuración existente), usando el mismo estilo visual que
  los filtros de estado actuales.

- **FR-004**: Debajo de la fila de escribanos, el listado MUST mostrar una segunda fila de
  filtros tipo píldora con las opciones: Todas, Abiertas y Cerradas.

- **FR-005**: Los filtros de escribano y estado MUST combinarse de forma acumulativa (AND):
  una escritura solo aparece si cumple ambos criterios seleccionados.

- **FR-006**: El listado MUST incluir una barra de búsqueda que filtre por coincidencia
  parcial en el nombre de la escritura, sin distinguir mayúsculas de minúsculas.

- **FR-007**: La búsqueda por nombre MUST aplicarse junto con los filtros de escribano y
  estado activos, sin resetearlos automáticamente.

- **FR-008**: Cuando ningún resultado coincide con los criterios activos, el sistema MUST
  mostrar un mensaje explícito de listado vacío (no una pantalla en blanco ni un error).

- **FR-008a**: El listado MUST conservar en la sesión del navegador (misma pestaña) los
  filtros de escribano y estado, el texto de búsqueda y el orden por fecha de creación al
  navegar al detalle de una escritura y volver, o al visitar otras secciones y regresar a
  Escrituras. Al cerrar la pestaña, los criterios vuelven a los valores por defecto.

- **FR-009**: Toda mención visible al usuario de "Contaduría Escribanía" MUST reemplazarse por
  "Escribanía Barat" en la aplicación completa (navbar, login, títulos de página y cualquier
  otra superficie de interfaz).

- **FR-010**: Toda mención visible al usuario de "Pagos al Colegio" o "pago al Colegio" MUST
  reemplazarse por "Pagos de la escribanía" / "pago de la escribanía" en la aplicación
  completa (detalle de escritura, libro de salida, formularios y mensajes de estado vacío).
  Los identificadores internos de sistema (API, tipos de evento) quedan fuera de alcance.

- **FR-011**: El detalle de escritura MUST reorganizar el contenido inferior (debajo de Saldo
  y Datos de la escritura) en dos columnas en viewports amplios: Factura principal a la
  izquierda; Pagos del cliente y Pagos de la escribanía apilados a la derecha.

- **FR-012**: La sección Factura principal MUST presentar sus subsecciones en un layout de
  dos columnas para reducir el scroll vertical en viewports amplios.

- **FR-013**: En viewports estrechos, el layout del detalle MUST apilar las secciones en
  orden lógico sin pérdida de información ni de funcionalidad.

- **FR-014**: Ningún cambio de esta feature MUST alterar las reglas de negocio existentes
  (cálculo de factura, registro de pagos, cierre condicionado al saldo, inmutabilidad de
  escrituras cerradas).

### Key Entities

- **Escritura (listado)**: Representa un trámite con nombre, escribano asignado, estado
  (abierta/cerrada), fecha de creación, montos de costo total, total pagado, saldo pendiente
  e indicadores de cobro.

- **Escribano**: Profesional titular al que se asigna una escritura; usado como dimensión
  del filtro principal del listado.

- **Factura principal**: Desglose financiero de la escritura, organizado en subsecciones
  visibles en layout de dos columnas.

- **Pago del cliente / Pago de la escribanía**: Movimientos de caja asociados a la escritura;
  en toda la UI visible, "Pagos de la escribanía" reemplaza a "Pagos al Colegio"; el
  significado operativo no cambia.

---

## Assumptions

- "Nombre de la factura" en el pedido del usuario se interpreta como el **nombre de la
  escritura** (`nombre`), que es el identificador legible del trámite en el listado.
- El orden por defecto al cargar el listado será **fecha de creación descendente** (más
  recientes primero), alineado con el uso habitual de revisar trámites nuevos.
- Los escribanos listados en el filtro principal se obtienen de la configuración existente;
  escrituras de escribanos inactivos siguen siendo filtrables y visibles.
- Los filtros y la búsqueda operan sobre el conjunto de escrituras accesibles al usuario
  autenticado, respetando permisos actuales del sistema.
- Filtros de escribano y estado se resuelven en servidor; búsqueda por nombre y orden por
  fecha de creación se aplican en cliente sobre el resultado cargado (volumen operativo
  habitual del estudio).
- Filtros, búsqueda y orden se persisten en la sesión de la pestaña del navegador; el
  impacto en rendimiento es despreciable (solo estado de UI, no datos adicionales del servidor).
- El rebranding a "Escribanía Barat" aplica a **todos los textos visibles** de la aplicación;
  no implica cambios en dominios, correos ni documentación externa salvo que se indique en
  otra feature.
- El layout de dos columnas aplica a resoluciones de escritorio (aprox. ≥ 1024 px de ancho);
  por debajo de ese umbral las secciones se apilan verticalmente.

---

## Testing Strategy

- **Enfoque elegido**: Hybrid (Unit Tests for core logic, no strict TDD)
- **Rationale**: La feature es predominantemente de interfaz; la lógica de filtrado por
  escribano/estado, ordenamiento por fecha y búsqueda por nombre sí requiere cobertura con
  unit tests, pero no se impone TDD estricto en cambios de layout, CSS o rebranding visual.
- **Alcance de tests obligatorios**:
  - Unit tests para combinación de filtros (escribano AND estado AND búsqueda por nombre).
  - Unit tests para ordenamiento por fecha de creación (ascendente/descendente).
  - Unit tests para restauración de estado de filtros/búsqueda/orden al volver al listado.
  - Sin tareas obligatorias de tests visuales o de layout más allá de verificación manual.
- **Scope note**: This decision MUST be honored by `/spec-kitti.plan` (test contracts) and
  `/spec-kitti.tasks` (TDD / unit-test tasks generated or omitted accordingly).

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Una secretaria puede localizar una escritura por nombre parcial en menos de
  10 segundos usando la barra de búsqueda, en el 95% de intentos en una sesión de prueba con
  al menos 20 escrituras cargadas.

- **SC-002**: Una secretaria puede filtrar el listado por escribano y estado, y ver solo las
  escrituras que cumplen ambos criterios, en un único flujo de dos pasos sin recargar la
  página manualmente.

- **SC-003**: Al abrir el detalle de una escritura con factura completa en un monitor de
  escritorio estándar, la secretaria puede ver simultáneamente el bloque de Saldo y el inicio
  de la Factura principal o Pagos del cliente sin más de una pantalla de scroll desde el
  encabezado.

- **SC-004**: El 100% de las superficies visibles que mostraban "Contaduría Escribanía" o
  "Pagos al Colegio" en la aplicación pasan a mostrar "Escribanía Barat" y "Pagos de la
  escribanía" respectivamente, verificable por revisión de todas las rutas principales
  (login, escrituras, detalle, liquidación, salarios, libros, configuración).

- **SC-005**: Ninguna regresión en flujos críticos existentes: crear escritura, registrar
  pagos, cerrar escritura con saldo en cero y consultar montos del listado siguen
  funcionando tras los cambios de interfaz.
