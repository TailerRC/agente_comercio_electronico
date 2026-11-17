---
description: "Task list for feature implementation: Capa de Datos y Catálogo de PixelOrbe"
---

# Tasks: Capa de Datos y Catálogo de PixelOrbe

**Input**: Design documents from `specs/001-capa-datos-pixelorbe/` (`spec.md`, `plan.md`, `data-model.md`, `contracts/tools_db.md`, `research.md`, `quickstart.md`).

**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data-model.md`, `contracts/tools_db.md`.

**Tests**: Se incluyen tareas de prueba automatizadas con `pytest` que cubren los 13 casos de prueba acordados en el plan y la especificación.

**Organization**: Tareas agrupadas por historias de usuario para permitir desarrollo e integración incremental independiente.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Ejecutable en paralelo (archivos independientes o funciones sin dependencia secuencial inmediata).
- **[Story]**: Historia de usuario a la que pertenece (`[US1]`, `[US2]`, `[US3]`, `[US4]`).
- Rutas exactas incluidas en cada tarea.

## Path Conventions

- Código fuente: `init_db.py`, `tools_db.py`, `generar_fichas.py` en la raíz del repositorio.
- Almacenamiento y documentos: `data/tienda.db`, `data/docs/ficha_*.md`.
- Pruebas automatizadas: `tests/test_tools_db.py`, `pytest.ini`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verificación de configuración inicial del entorno y persistencia.

- [X] T001 Verificar entorno de dependencias y configuración de importación en `pytest.ini` y `requirements.txt`
- [X] T002 [P] Verificar la definición del esquema relacional (6 tablas) y catálogo inicial de 48 productos en `init_db.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Infraestructura central de conexión, normalización y búsqueda en memoria que bloquea a todas las tools.

**⚠️ CRITICAL**: Ninguna tool de usuario puede implementarse hasta completar esta fase.

- [X] T003 Definir variable de módulo `RUTA_DB = Path(__file__).parent / "data" / "tienda.db"` y función helper `_conectar()` con `row_factory=sqlite3.Row` y `PRAGMA foreign_keys=ON` en `tools_db.py`
- [X] T004 Implementar función helper `_normalizar(texto: str) -> str` para minúsculas y eliminación de tildes mediante `unicodedata` en `tools_db.py`
- [X] T005 Implementar función helper `_buscar_productos(texto: str)` que consulta el catálogo y realiza filtrado en memoria sobre los 48 productos normalizados en `tools_db.py`
- [X] T006 [P] Configurar el fixture `bd` en `tests/test_tools_db.py` que crea la base de datos temporal con `init_db.crear_bd(reiniciar=True)` y aplica monkeypatch a `RUTA_DB` en `tools_db.py` e `init_db.py`

**Checkpoint**: Base de conexión, helpers de búsqueda y fixture de testing listos para comenzar las historias de usuario.

---

## Phase 3: User Story 1 - Consulta de Disponibilidad y Precios en Catálogo (Priority: P1) 🎯 MVP

**Goal**: Permitir consultar stock y precios con búsqueda flexible en español (insensible a tildes), desambiguación determinista ante múltiples coincidencias y contención de errores.

**Independent Test**: Invocar `consultar_stock` y `consultar_precio` con productos específicos, productos agotados, variaciones sin tilde, nombres ambiguos y términos inexistentes.

### Implementation for User Story 1

- [X] T007 [US1] Implementar función de contrato `consultar_stock(producto: str) -> str` con reporte de stock disponible, estado agotado cuando `stock == 0` y listado de opciones ante ambigüedades en `tools_db.py`
- [X] T008 [US1] Implementar función de contrato `consultar_precio(producto: str) -> str` con precio en USD, estado agotado si aplica y desambiguación múltiple en `tools_db.py`

### Tests for User Story 1

- [X] T009 [P] [US1] Implementar test para consulta de stock de IdeaPad (ID 9, 12 unidades) verificando nombre completo y cantidad en `tests/test_tools_db.py`
- [X] T010 [P] [US1] Implementar test para monitor agotado (ID 26 Monitor Samsung Odyssey G3, stock 0) verificando estado "agotado" en `tests/test_tools_db.py`
- [X] T011 [P] [US1] Implementar test para producto inexistente verificando mensaje descriptivo sin excepciones en `tests/test_tools_db.py`
- [X] T012 [P] [US1] Implementar test para búsqueda sin tilde ("audifonos" coincide con "audífonos") en `tests/test_tools_db.py`
- [X] T013 [P] [US1] Implementar test para búsqueda con múltiples resultados ("mouse" retorna opciones con ID, nombre y precio) en `tests/test_tools_db.py`
- [X] T014 [P] [US1] Implementar test de seguridad comprobando que inyección SQL (comillas o cláusulas `' OR '1'='1`) en la búsqueda no altera la base de datos en `tests/test_tools_db.py`

**Checkpoint**: User Story 1 (MVP) completamente operativa, testeable y protegida contra SQL injection.

---

## Phase 4: User Story 2 - Registro Transaccional y Seguro de Pedidos (Priority: P1)

**Goal**: Registrar órdenes de compra de manera atómica (`BEGIN IMMEDIATE`), validando cantidad (1-20), formato de email y stock disponible, con confirmación estructurada y rollback ante fallos.

**Independent Test**: Registrar compras válidas confirmando decremento exacto en inventario y emisión de resumen; intentar compras inválidas verificando rechazo y stock inalterado.

### Implementation for User Story 2

- [X] T015 [US2] Implementar validaciones de negocio para `registrar_pedido`: cantidad entera entre 1 y 20, expresión regular de email `^[^@\s]+@[^@\s]+\.[^@\s]+$` y existencia de producto en `tools_db.py`
- [X] T016 [US2] Implementar función de contrato `registrar_pedido(cliente: str, email: str, producto_id: int, cantidad: int) -> str` ejecutando `BEGIN IMMEDIATE`, `UPDATE productos SET stock = stock - ? WHERE id = ? AND stock >= ?` y retornando ID, producto, cantidad y total en USD en `tools_db.py`

### Tests for User Story 2

- [X] T017 [P] [US2] Implementar test para pedido válido con reducción de stock (Mouse Logitech M185 ID 40 comprando 2 unidades, stock 60 → 58) en `tests/test_tools_db.py`
- [X] T018 [P] [US2] Implementar test para rechazo de cantidad 0 y cantidad negativa (-1) verificando que el stock permanece intacto en `tests/test_tools_db.py`
- [X] T019 [P] [US2] Implementar test para rechazo por email con formato inválido verificando que no se crea cliente ni pedido en `tests/test_tools_db.py`
- [X] T020 [P] [US2] Implementar test para rechazo al registrar pedido sobre producto agotado (stock 0) en `tests/test_tools_db.py`
- [X] T021 [P] [US2] Implementar test para rechazo cuando la cantidad solicitada excede el stock disponible en `tests/test_tools_db.py`

**Checkpoint**: User Stories 1 y 2 operativas con transacciones ACID seguras.

---

## Phase 5: User Story 3 - Historial y Consulta de Pedidos por Cliente (Priority: P2)

**Goal**: Permitir consultar el historial de compras asociadas a un correo electrónico en orden cronológico con detalles de producto, unidades y total en USD.

**Independent Test**: Consultar correos con pedidos previos y correos sin registros asociados comprobando formato de salida.

### Implementation for User Story 3

- [X] T022 [US3] Implementar función de contrato `listar_pedidos(email: str) -> str` con validación de email, consulta SQL parametrizada y formato amigable en `tools_db.py`

### Tests for User Story 3

- [X] T023 [P] [US3] Implementar test para listar pedidos tras registrar una compra válida verificando producto, cantidad, total y fecha en `tests/test_tools_db.py`
- [X] T024 [P] [US3] Implementar test para listar pedidos con un email sin compras previas verificando mensaje descriptivo en `tests/test_tools_db.py`

**Checkpoint**: Capa de consultas transaccionales de pedidos (User Story 3) completada y validada.

---

## Phase 6: User Story 4 - Fichas Técnicas Documentales para Soporte y RAG (Priority: P2)

**Goal**: Generar las 48 fichas técnicas en `data/docs/` con nomenclatura `ficha_<slug>.md`, con 12 fichas completas y 36 breves, estructuradas por secciones `##` para RAG y sin filtración de precios ni stock.

**Independent Test**: Ejecutar `python generar_fichas.py` y validar la existencia, formato de encabezados y ausencia de precios/stock en todos los archivos generados.

### Implementation for User Story 4

- [X] T025 [US4] Implementar script `generar_fichas.py` que importe `PRODUCTOS` de `init_db.py` y aplique slugging a los nombres de archivo en `generar_fichas.py`
- [X] T026 [US4] Implementar en `generar_fichas.py` el contenido de las 12 fichas completas (incluyendo ID 9 IdeaPad 15, ID 26 Monitor Odyssey G3, ID 40 Mouse M185 y al menos una por cada categoría) con secciones `## Descripción`, `## Especificaciones`, `## Uso recomendado` y `## Garantía referencial`
- [X] T027 [P] [US4] Implementar en `generar_fichas.py` las 36 fichas breves (5 a 8 líneas) y escribir todos los archivos en `data/docs/ficha_*.md` garantizando 0 menciones de precios o stock

**Checkpoint**: 48 fichas técnicas generadas en `data/docs/` listas para la Fase 2 (Jerzy).

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Verificación final, ejecución de suite de pruebas integral y actualización de documentación.

- [X] T028 Ejecutar la suite completa de pruebas en `tests/test_tools_db.py` con `pytest` y confirmar 100% de tests en verde
- [X] T029 [P] Actualizar `README.md` con instrucciones completas para inicializar la base de datos (`python init_db.py --reset`), generar fichas (`python generar_fichas.py`) y correr pruebas (`pytest`)
- [X] T030 Ejecutar validación interactiva completa de los escenarios descritos en `specs/001-capa-datos-pixelorbe/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Sin dependencias, inicia de inmediato.
- **Foundational (Phase 2)**: Depende de Phase 1. Bloquea la implementación de las tools.
- **User Story 1 (Phase 3)**: Depende de Phase 2. MVP de catálogo.
- **User Story 2 (Phase 4)**: Depende de Phase 2. Puede desarrollarse tras US1.
- **User Story 3 (Phase 5)**: Depende de Phase 2 (se beneficia de US2 para tests de pedidos existentes).
- **User Story 4 (Phase 6)**: Depende de `init_db.py` (Phase 1). Puede ejecutarse en paralelo con US1-US3.
- **Polish (Phase 7)**: Depende de la finalización de todas las historias anteriores.

### Matriz de los 13 Casos de Prueba del Plan

| # | Caso de Prueba | Tarea de Prueba | Módulo / Función probada |
|---|----------------|-----------------|--------------------------|
| 1 | Stock IdeaPad (ID 9, stock 12) | T009 | `tools_db.consultar_stock` |
| 2 | Monitor agotado (ID 26, stock 0) | T010 | `tools_db.consultar_stock` |
| 3 | Producto inexistente | T011 | `tools_db.consultar_stock` / `consultar_precio` |
| 4 | "audifonos" sin tilde | T012 | `tools_db._normalizar` / búsqueda |
| 5 | "mouse" con 2 resultados | T013 | `tools_db.consultar_stock` (desambiguación) |
| 6 | Pedido válido 60 → 58 (Mouse M185 ID 40) | T017 | `tools_db.registrar_pedido` |
| 7 | Cantidad 0 y -1 | T018 | `tools_db.registrar_pedido` (validación) |
| 8 | Email inválido | T019 | `tools_db.registrar_pedido` (regex) |
| 9 | Producto agotado | T020 | `tools_db.registrar_pedido` |
| 10 | Pedido mayor al stock | T021 | `tools_db.registrar_pedido` |
| 11 | Listar tras pedido | T023 | `tools_db.listar_pedidos` |
| 12 | Listar sin pedidos | T024 | `tools_db.listar_pedidos` |
| 13 | Inyección SQL | T014 | `tools_db._buscar_productos` / SQL parametrizado |

---

## Parallel Opportunities

- **Phase 1**: T002 puede prepararse en paralelo con T001.
- **Phase 2**: T006 (fixture de testing) puede desarrollarse en paralelo con T004 y T005.
- **Phase 3**: Las pruebas T009 a T014 pueden redactarse en paralelo una vez fijadas las firmas de T007 y T008.
- **Phase 4**: Las pruebas T017 a T021 pueden implementarse en paralelo para validar las distintas ramas de error de `registrar_pedido`.
- **Phase 6**: La generación de fichas técnicas (T025, T026, T027) es independiente de la lógica interna de `tools_db.py` y puede ejecutarse en paralelo con las fases de tools.

---

## Implementation Strategy

### MVP First (User Story 1 Only)
1. Completar Setup (Phase 1) y Foundational (Phase 2).
2. Implementar `consultar_stock` y `consultar_precio` (Phase 3).
3. Validar los tests T009 a T014 con `pytest`.
4. El sistema ya es capaz de atender consultas de catálogo de forma segura.

### Entrega Incremental Completa
1. Añadir User Story 2 (`registrar_pedido`) y verificar atomicidad de inventario.
2. Añadir User Story 3 (`listar_pedidos`) para consulta de órdenes.
3. Generar las 48 fichas Markdown con `generar_fichas.py` (User Story 4).
4. Ejecutar el checklist de entrega y verificación en Phase 7.
