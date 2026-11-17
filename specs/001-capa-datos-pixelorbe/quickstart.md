# Quickstart & Verification Guide: Capa de Datos de PixelOrbe

**Feature**: `specs/001-capa-datos-pixelorbe`
**Date**: 2026-11-16
**Status**: Ready for Verification

Este documento detalla los pasos reproducibles para inicializar, validar y probar la capa de datos de PixelOrbe (Fase 1 - Rodrigo) en un entorno limpio.

---

## 1. Prerrequisitos

- Python 3.10 o superior instalado.
- Entorno virtual activo con dependencias instaladas:
  ```bash
  pip install -r requirements.txt
  ```

---

## 2. Inicialización de la Base de Datos

Para inicializar la base de datos de producción con el catálogo oficial de 48 productos:

```bash
python init_db.py --reset
```

**Resultado esperado**:
- Archivo creado en `data/tienda.db`.
- Salida en consola confirmando:
  - 6 categorías creadas.
  - 48 productos insertados.
  - 9 productos con stock en 0 (agotados).

---

## 3. Generación y Validación de Fichas Técnicas

Para generar o regenerar las 48 fichas técnicas Markdown:

```bash
python generar_fichas.py
```

**Resultado esperado**:
- 48 archivos generados en `data/docs/ficha_*.md`.
- Cada archivo contiene `# <Nombre exacto>`, categoría y encabezados `## Descripción`, `## Especificaciones`, `## Uso recomendado` y `## Garantía referencial`.
- Ningún archivo contiene referencias a precios ni stock.

---

## 4. Ejecución de la Suite de Pruebas Automatizadas

La suite de pruebas en `tests/test_tools_db.py` utiliza una base de datos temporal en `tmp_path` mediante monkeypatch, garantizando aislamiento total.

Para ejecutar todas las pruebas:

```bash
pytest
```

Para ejecutar con reporte detallado:

```bash
pytest -v tests/test_tools_db.py
```

**Criterio de Aceptación**:
- 100% de las pruebas en verde (`passed`).
- Cobertura de:
  - Verificación del catálogo inicial (48 productos, 6 categorías, 9 agotados).
  - Consulta de stock y precios con coincidencia única, sin coincidencias y desambiguación múltiple.
  - Normalización de acentos y caracteres diacríticos (búsqueda insensible a tildes).
  - Resistencia a inyección SQL en consultas de texto.
  - Registro atómico de pedidos y reducción de stock.
  - Rechazo de pedidos con stock insuficiente o cantidad inválida sin afectar la base.
  - Listado de pedidos por cliente.

---

## 5. Validación Interactiva Rápida (Smoke Test en REPL)

Puede verificarse el comportamiento de las tools interactivamente en la terminal:

```bash
python -c "import tools_db as t; print(t.consultar_stock('ideapad')); print(t.consultar_stock('mouse')); print(t.consultar_stock('odyssey'))"
```

**Salida esperada**:
1. `ideapad`: Detalle de 12 unidades disponibles para "Laptop Lenovo IdeaPad 15".
2. `mouse`: Listado de múltiples opciones (Logitech M185, G203, etc.) con sus IDs y precios.
3. `odyssey`: Indicación de producto agotado para "Monitor Samsung Odyssey G3 24 pulgadas".
