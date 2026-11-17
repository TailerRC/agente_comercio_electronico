# Tienda Agent: Agente de Comercio Electrónico (PixelOrbe)

- **Tienda**: PixelOrbe
- **Bot**: PixAI
- **Curso**: Redes Neuronales Artificiales 2026-2 (URP)

---

## 👥 Esquema de Relevos del Equipo

El proyecto está diseñado bajo un modelo de relevos secuenciales con responsabilidades delimitadas:

1. **Parte 1 (Rodrigo) — Base de Datos, Tools y Catálogo**:
   - Diseño del esquema relacional en SQLite e inicialización (`init_db.py`).
   - Implementación de las tools del contrato (`tools_db.py`).
   - Generación de las 48 fichas técnicas Markdown en `data/docs/` (`generar_fichas.py`).
   - Suite de pruebas unitarias automatizadas (`tests/test_tools_db.py`).
2. **Parte 2 (Jerzy) — Agente Conversacional, RAG y Corpus**:
   - Ingesta y vectorización del corpus documental en ChromaDB (`rag.py`, `ingest.py`).
   - Estructuración del agente LLM con function calling y memoria por sesión (`agent.py`).
   - Métricas y evaluación RAG (`evaluar_rag.py`).
3. **Parte 3 (Alisson) — Servicios Externos, Bot de Telegram y E2E**:
   - Integración de API de tipo de cambio y servicio de correo SMTP (`tools_ext.py`).
   - Conexión del agente a Telegram (`bot.py`).
   - Pruebas de integración de extremo a extremo (`tests/test_e2e.py`).

---

## 🛠️ Requisitos e Instalación

### 1. Prerrequisitos
- Python 3.10 o superior instalado.
- Git para control de versiones.

### 2. Configuración del Entorno
Clonar el repositorio y crear un entorno virtual:

```bash
git clone <URL_DEL_REPOSITORIO>
cd agente_comercio_electronico

python -m venv .venv
# En Windows:
.venv\Scripts\activate
# En Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Variables de Entorno
Copiar la plantilla de variables de entorno y configurar los valores necesarios:

```bash
cp .env.example .env
```

---

## 🚀 Puesta en Marcha de la Capa de Datos (Parte 1 - Rodrigo)

### 1. Inicialización de la Base de Datos SQLite
Para crear la base de datos `data/tienda.db` con el catálogo inicial de 48 productos distribuidos en 6 categorías (9 de ellos agotados):

```bash
python init_db.py --reset
```

### 2. Generación de Fichas Técnicas Markdown
Para generar las 48 fichas técnicas en `data/docs/ficha_*.md` (12 detalladas y 36 concisas, preparadas para chunking por encabezados `##` en RAG y sin datos de precio ni stock):

```bash
python generar_fichas.py
```

### 3. Ejecución de Pruebas Automatizadas
La suite de pruebas en `tests/test_tools_db.py` opera sobre una base de datos temporal en memoria/tmp (vía monkeypatch) sin tocar `data/tienda.db`:

```bash
pytest
```

Para reporte detallado:

```bash
pytest -v
```

---

## 🔍 Contrato de Tools de Base de Datos (`tools_db.py`)

Todas las funciones retornan `str`, nunca propagan excepciones y manejan precios en USD:

- `consultar_stock(producto: str) -> str`: Busca productos activos (insensible a tildes o mayúsculas). Retorna stock disponible, aviso de producto agotado o lista de desambiguación si hay múltiples coincidencias.
- `consultar_precio(producto: str) -> str`: Retorna el precio unitario en USD.
- `registrar_pedido(cliente: str, email: str, producto_id: int, cantidad: int) -> str`: Operación atómica (`BEGIN IMMEDIATE` + `UPDATE` condicional). Valida cantidad (1 a 20 unidades), email y stock disponible. En éxito, descuenta inventario y emite ID de orden, producto, cantidad y total.
- `listar_pedidos(email: str) -> str`: Retorna el historial cronológico de compras asociadas al correo del cliente.

### Verificación Interactiva Rápida (Smoke Test)

```bash
python -c "import tools_db as t; print(t.consultar_stock('ideapad')); print(t.consultar_stock('mouse')); print(t.consultar_stock('odyssey'))"
```
