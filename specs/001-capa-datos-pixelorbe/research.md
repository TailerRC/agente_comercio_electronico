# Research & Architectural Decisions: Capa de Datos de PixelOrbe

**Feature**: `specs/001-capa-datos-pixelorbe`
**Date**: 2026-11-16
**Status**: Completed

## Overview
Investigación técnica y justificación de decisiones arquitectónicas para la implementación de la capa de datos de PixelOrbe (Fase 1 - Rodrigo), asegurando estricto cumplimiento de la constitución, rendimiento óptimo y portabilidad.

---

## 1. Normalización y Búsqueda Flexible de Productos sin Dependencias C

### Decisión
Implementar un helper interno `_normalizar(texto: str) -> str` utilizando la biblioteca estándar `unicodedata` (`NFD`, filtrado de `Mn` y minúsculas) y realizar el filtrado de búsqueda en memoria en Python sobre los 48 productos del catálogo.

### Justificación
- La función estándar `LIKE` de SQLite solo realiza case-folding en caracteres ASCII (A-Z). Consultas como `LIKE '%audifonos%'` no coinciden con `'Audífonos'`, y `COLLATE NOCASE` tampoco normaliza tildes ni caracteres diacríticos en español.
- Habilitar soporte ICU en SQLite requiere compilar e instalar extensiones nativas C (`libsqlite3-icu`), lo cual rompe la portabilidad entre plataformas (Windows, Linux, macOS) y agrega fricción de despliegue.
- El catálogo consta de exactamente 48 productos. Cargar los registros en memoria y evaluarlos en Python mediante normalización toma menos de 0.5 milisegundos por consulta, ofreciendo una experiencia instantánea (< 50 ms) y determinista sin requerir dependencias externas.

### Alternativas Evaluadas
- **Extensión SQLite ICU**: Descartada por complejidad de instalación y dependencia de compilación nativa en el sistema operativo del usuario.
- **SQLite FTS5 (Full Text Search)**: Descartada por sobredimensionamiento (overkill) y necesidad de sincronización entre tablas auxiliares virtuales para un catálogo estático de 48 registros.
- **Búsqueda exacta con `LIKE`**: Descartada porque degrada severamente la experiencia del usuario final al fallar ante variaciones de acentuación ("ideapad" vs "IdeaPad", "audifonos" vs "audífonos").

---

## 2. Concurrencia y Atomicidad en el Registro de Pedidos

### Decisión
Utilizar una transacción con bloqueo inmediato (`BEGIN IMMEDIATE`) y una actualización condicional en una sola sentencia SQL:
```sql
UPDATE productos
SET stock = stock - ?
WHERE id = ? AND stock >= ?;
```
Inspeccionando `cursor.rowcount`: si es 0, ejecutar `ROLLBACK` y retornar mensaje amigable de stock insuficiente; si es 1, ejecutar la inserción en la tabla `pedidos` y finalizar con `COMMIT`.

### Justificación
- En SQLite, una transacción estándar (`BEGIN DEFERRED`) adquiere un lock compartido y recién intenta elevarlo a lock exclusivo al ejecutar una escritura, lo que puede provocar excepciones de tipo `sqlite3.OperationalError: database is locked` si múltiples hilos o consultas coinciden.
- `BEGIN IMMEDIATE` asegura un lock reservado de escritura desde el primer instante, serializando las mutaciones de forma segura.
- La cláusula condicional `AND stock >= ?` previene condiciones de carrera a nivel de fila (*time-of-check to time-of-use* o TOCTOU). No hay intervalo de vulnerabilidad entre la comprobación del stock y su descuento.
- Cumple fielmente la Regla Constitucional 7 (Atomicidad transaccional).

### Alternativas Evaluadas
- **Lectura previa con `SELECT` y luego `UPDATE`**: Descartada por permitir race conditions si dos transacciones concurrentes leen el mismo stock antes de que cualquiera de las dos descuente.
- **Triggers en SQLite**: Descartados para mantener la lógica de validación visible y comprobable en el código de aplicación en Python con mensajes de error descriptivos.

---

## 3. Estrategia de Pruebas Aisladas con Pytest y Monkeypatch

### Decisión
Definir `RUTA_DB = Path(__file__).parent / "data" / "tienda.db"` como variable de nivel de módulo en `tools_db.py` e `init_db.py`. En `tests/test_tools_db.py`, implementar un fixture de pytest:
```python
@pytest.fixture
def bd(tmp_path, monkeypatch):
    ruta = tmp_path / "tienda.db"
    monkeypatch.setattr(init_db, "RUTA_DB", ruta)
    monkeypatch.setattr(tools_db, "RUTA_DB", ruta)
    init_db.crear_bd(reiniciar=True)
    return ruta
```

### Justificación
- Garantiza que la ejecución de pruebas NUNCA toque ni contamine la base de datos real en `data/tienda.db`.
- Cada prueba o función de prueba recibe una base de datos limpia e independiente en el directorio temporal manejado por pytest (`tmp_path`).
- No requiere alterar las firmas públicas de las tools (las cuales deben recibir solo los parámetros acordados: `producto`, `email`, etc., sin recibir objetos de conexión externos).

### Alternativas Evaluadas
- **Bases en memoria (`:memory:`)**: En SQLite, `:memory:` crea una base que solo vive mientras esa conexión específica permanezca abierta. Si cada tool invoca `_conectar()`, cada llamada abriría una base en memoria distinta y vacía.
- **Inyección de dependencias por parámetro en las tools**: Descartada porque violaría la Regla Constitucional 4 sobre inmutabilidad de firmas públicas (`consultar_stock(producto: str) -> str`).

---

## 4. Generación y Segmentación de Fichas Técnicas para RAG

### Decisión
Crear un script utilitario `generar_fichas.py` que importe la lista `PRODUCTOS` de `init_db.py` y genere los 48 archivos Markdown en `data/docs/ficha_<slug>.md`. Contará con 12 fichas detalladas (incluyendo IDs 9, 26 y 40) y 36 fichas breves pero completas con las 4 secciones estándar `## Descripción`, `## Especificaciones`, `## Uso recomendado` y `## Garantía referencial`.

### Justificación
- Facilita la división semántica (chunking) en la Fase 2 (Jerzy) mediante partición por encabezados `##`.
- Excluye estrictamente precio y stock de las fichas, cumpliendo la Regla Constitucional 11 (Separación de datos dinámicos y corpus RAG).
- La convención de slug unificada (`ficha_<slug>.md`) permite mapeo directo y reproducible entre la base de datos relacional y el corpus documental.

### Alternativas Evaluadas
- **Creación manual de 48 fichas**: Ineficiente y propensa a inconsistencias en la nomenclatura de archivos o encabezados.
- **Formato JSON / YAML**: Menos adecuado para búsqueda semántica vectorial basada en embeddings de texto en lenguaje natural.
