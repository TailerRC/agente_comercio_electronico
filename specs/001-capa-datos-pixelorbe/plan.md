# Implementation Plan: Capa de Datos y Catálogo de PixelOrbe

**Branch**: `rodrigo` | **Date**: 2026-11-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-capa-datos-pixelorbe/spec.md`

## Summary

Implementación de la capa de datos de PixelOrbe (Fase 1 - Rodrigo), que comprende el catálogo relacional en SQLite con 48 productos distribuidos en 6 categorías (9 agotados), las 4 herramientas base de acceso a datos para function calling (`consultar_stock`, `consultar_precio`, `registrar_pedido`, `listar_pedidos`), un script generador de fichas técnicas Markdown estructuradas para consumo de RAG en `data/docs/`, y la suite de pruebas unitarias exhaustiva con `pytest` sobre base de datos temporal aislada.

La arquitectura se fundamenta en la biblioteca estándar `sqlite3` de Python sin ORMs, rutas con `pathlib`, normalización diacrítica con `unicodedata` para búsquedas en memoria insensibles a tildes, transaccionalidad atómica (`BEGIN IMMEDIATE` y `UPDATE` condicional) y contención total de excepciones retornando mensajes amigables en `str`.

## Technical Context

**Language/Version**: Python 3.10+ (utilizando módulos de la biblioteca estándar: `sqlite3`, `unicodedata`, `pathlib`, `re`, `contextlib`).

**Primary Dependencies**: Ninguna dependencia externa en tiempo de ejecución para la capa de datos; `pytest` para la suite de pruebas automatizadas.

**Storage**: SQLite 3 (`data/tienda.db` en producción, base temporal en `tmp_path` durante pruebas) con 6 tablas relacionales (`categorias`, `productos`, `clientes`, `pedidos`, `pagos`, `consultas_log`) e integridad referencial activa (`PRAGMA foreign_keys = ON`).

**Testing**: `pytest` con fixture de monkeypatching sobre `RUTA_DB` y reinicialización completa del catálogo (`init_db.crear_bd(reiniciar=True)`).

**Target Platform**: Multiplataforma (Windows, Linux, macOS) sin requerimientos de compilación C ni librerías nativas externas.

**Project Type**: Capa de persistencia y biblioteca de tools para agente conversacional.

**Performance Goals**: Tiempo de respuesta < 50ms en cualquier invocación de tool; filtrado en memoria de 48 productos en < 1ms.

**Constraints**:
- Todas las consultas SQL parametrizadas estrictamente con marcadores de posición (`?`).
- Todas las tools públicas retornan `str` y encapsulan cualquier `sqlite3.Error`.
- Todos los precios e importes almacenados y calculados en USD.
- Transacciones atómicas de pedido con `BEGIN IMMEDIATE` y descuento condicional `stock >= ?`.

**Scale/Scope**: Catálogo fijo de 48 productos, 6 categorías, 9 productos agotados, 4 contratos de tools principales, 48 fichas técnicas en `data/docs/`.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio Constitucional | Estado | Justificación / Cumplimiento |
|--------------------------|--------|------------------------------|
| **I. Seguridad y Gestión de Secretos** | **PASS** | La capa de datos no requiere credenciales externas; todas las consultas SQL son estrictamente parametrizadas con `?` prohibiendo concatenación de cadenas. |
| **II. Estabilidad de Contratos de Módulos** | **PASS** | Las firmas públicas de `consultar_stock`, `consultar_precio`, `registrar_pedido` y `listar_pedidos` coinciden con exactitud; retornan siempre `str` y atrapan excepciones; precios en USD; mutaciones atómicas. |
| **III. Comportamiento y Separación de Datos** | **PASS** | Los datos dinámicos (precios y stock) viven exclusivamente en SQLite; las fichas técnicas Markdown no contienen precios ni existencias. |
| **IV. Calidad y Relevos en Equipo** | **PASS** | El alcance está restringido a la Fase 1 (Rodrigo); suite de pruebas `pytest` completa en verde; README actualizado para despliegue desde cero. |
| **V. Código y Documentación** | **PASS** | Código y docstrings redactados en español; fichas técnicas de redacción original y estructuradas con secciones `##` para RAG. |

## Project Structure

### Documentation (this feature)

```text
specs/001-capa-datos-pixelorbe/
├── plan.md              # Este plan de implementación
├── research.md          # Decisiones de investigación (Fase 0)
├── data-model.md        # Modelo relacional y documental (Fase 1)
├── quickstart.md        # Guía de verificación y ejecución (Fase 1)
├── contracts/
│   └── tools_db.md      # Contratos de interfaces públicas de tools (Fase 1)
├── checklists/
│   └── requirements.md  # Checklist de validación de calidad de la especificación
└── tasks.md             # Plan de tareas de implementación (Fase 2 - /speckit-tasks)
```

### Source Code (repository root)

```text
.
├── data/
│   ├── tienda.db             # Base de datos SQLite de producción (creada por init_db.py)
│   └── docs/
│       ├── .gitkeep
│       └── ficha_*.md        # 48 fichas técnicas Markdown generadas
├── tests/
│   ├── __init__.py
│   ├── pytest.ini            # Configuración de rutas para pytest
│   └── test_tools_db.py      # Pruebas automatizadas sobre BD temporal
├── init_db.py                # Definición de esquema SQLite y catálogo de 48 productos
├── tools_db.py               # Implementación de tools públicas con SQLite
├── generar_fichas.py         # Script utilitario para crear las 48 fichas Markdown
└── README.md                 # Documentación e instrucciones paso a paso
```

**Structure Decision**: Estructura de proyecto único estándar en Python. Los módulos de la capa de datos residen en la raíz del proyecto para facilitar su importación por el agente (`agent.py`) y bot (`bot.py`) en fases subsiguientes, con almacenamiento de datos y fichas en `data/` y pruebas en `tests/`.

## Complexity Tracking

> *Sin violaciones ni excepciones constitucionales. No se requiere tracking de complejidad adicional.*
