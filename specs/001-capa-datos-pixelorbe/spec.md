# Feature Specification: Capa de Datos y Catálogo de PixelOrbe

**Feature Branch**: `rodrigo`

**Created**: 2026-11-16

**Status**: Draft

**Input**: User description: "Alcance: esta spec cubre solo la Parte 1 (Rodrigo): init_db.py, tools_db.py, tests/test_tools_db.py, data/docs/ficha_*.md y README. No incluye agent.py, RAG, correo ni bot. Especifica la capa de datos de PixelOrbe: base SQLite con 48 productos en 6 categorías (9 agotados), 4 tools y fichas técnicas."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Consulta de Disponibilidad y Precio en Catálogo (Priority: P1)

Como cliente o agente de soporte de la tienda, quiero consultar el stock y precio de los productos mediante lenguaje natural o nombres parciales para conocer la disponibilidad y costo antes de tomar una decisión de compra.

**Why this priority**: Es la interacción fundamental y más frecuente en el flujo de comercio electrónico. Sin capacidad de consulta confiable, ninguna otra operación puede realizarse.

**Independent Test**: Puede probarse de manera aislada consultando nombres exactos, términos parciales, productos con stock disponible, productos agotados y términos inexistentes.

**Acceptance Scenarios**:

1. **Given** un catálogo con el producto "Laptop Lenovo IdeaPad 15" con 12 unidades en stock, **When** se consulta el stock con el término "ideapad", **Then** el sistema responde con una única coincidencia indicando nombre completo y 12 unidades disponibles.
2. **Given** un catálogo con el producto "Monitor Samsung Odyssey G3 24 pulgadas" con 0 unidades en stock, **When** se consulta el stock o precio, **Then** el sistema responde indicando que el producto se encuentra agotado.
3. **Given** un término de búsqueda general como "mouse" que coincide con múltiples artículos (ej. "Mouse Logitech M185" y "Mouse Gamer Logitech G203"), **When** se consulta stock o precio, **Then** el sistema lista todas las opciones coincidentes con su identificador (ID), nombre y precio referencial para que el interlocutor elija, sin seleccionar nunca una opción al azar.
4. **Given** un término que no coincide con ningún producto del catálogo, **When** se consulta stock o precio, **Then** el sistema retorna un mensaje cortés indicando que el producto no fue encontrado sin lanzar excepciones.

---

### User Story 2 - Registro Transaccional y Seguro de Pedidos (Priority: P1)

Como cliente listo para comprar, quiero registrar un pedido indicando mis datos, el producto y la cantidad deseada para apartar las unidades y generar una orden de compra válida.

**Why this priority**: Representa el cierre de venta y la mutación crítica de inventario. Debe ser completamente seguro, atómico y libre de inconsistencias o sobreventas.

**Independent Test**: Puede probarse registrando compras con cantidades válidas verificando la reducción en inventario y la emisión de datos del pedido, así como intentando registrar pedidos inválidos y comprobando que el inventario queda intacto.

**Acceptance Scenarios**:

1. **Given** un producto con stock disponible (ej. ID 9 con 12 unidades), **When** un cliente con nombre válido y correo válido solicita una cantidad positiva menor o igual al stock y al tope máximo de 20 unidades, **Then** el sistema descuenta el stock de forma atómica, registra el pedido y responde con un mensaje de confirmación que incluye obligatoriamente ID de pedido, nombre del producto, cantidad comprada y total en USD.
2. **Given** un producto con stock menor al solicitado o solicitud mayor a 20 unidades, **When** se solicita el pedido, **Then** el sistema rechaza la operación informando el motivo del fallo y el stock en base de datos permanece inalterado.
3. **Given** un cliente que ingresa un correo con formato inválido o un identificador de producto inexistente, **When** se procesa la solicitud, **Then** el sistema rechaza la operación sin registrar ningún pedido ni modificar inventario.

---

### User Story 3 - Historial y Consulta de Pedidos por Cliente (Priority: P2)

Como cliente o agente de soporte, quiero listar los pedidos asociados a una dirección de correo electrónico para verificar el estado de mis compras recientes y montos acumulados.

**Why this priority**: Brinda visibilidad y soporte postventa al usuario final y permite a los agentes de atención brindar seguimiento sin acceso directo al motor de base de datos.

**Independent Test**: Puede probarse consultando correos con múltiples pedidos registrados, correos con un solo pedido y correos sin pedidos previos.

**Acceptance Scenarios**:

1. **Given** un correo con compras previamente registradas, **When** se solicita el historial de pedidos de dicho correo, **Then** el sistema lista cronológicamente cada pedido detallando nombre de producto, cantidad, total pagado en USD y fecha/hora de registro.
2. **Given** un correo sin historial de compras en la tienda, **When** se solicita el listado de pedidos, **Then** el sistema responde con un mensaje claro indicando que no se registran pedidos asociados a esa dirección.

---

### User Story 4 - Fichas Técnicas Documentales para Soporte y RAG (Priority: P2)

Como agente o subsistema de búsqueda documental (RAG), requiero disponer de fichas técnicas estandarizadas en Markdown para cada producto del catálogo, de modo que se puedan responder consultas técnicas y de garantía sin mezclar información dinámica de stock o precios.

**Why this priority**: Habilita la base de conocimiento para la Fase 2 (Jerzy), permitiendo segmentación y chunking limpio por encabezados para el corpus RAG.

**Independent Test**: Puede probarse validando la existencia, nomenclatura y estructura de secciones Markdown (`##`) en todas las fichas de `data/docs/`.

**Acceptance Scenarios**:

1. **Given** el catálogo de 48 productos, **When** se examina el directorio de documentación `data/docs/`, **Then** existe exactamente una ficha por producto bajo la convención `ficha_<slug>.md` con título `# <nombre exacto>`, indicación de categoría y secciones `## Descripción`, `## Especificaciones`, `## Uso recomendado` y `## Garantía referencial`.
2. **Given** las fichas técnicas generadas, **When** se audita su contenido, **Then** ninguna ficha contiene datos variables de precio ni existencias de stock, y se cuenta con 12 fichas detalladas (incluyendo obligatoriamente IDs 9, 26, 40 y representantes de las 6 categorías) y 36 fichas breves (5 a 8 líneas).

---

### Edge Cases

- **Inyección SQL en parámetros de texto**: Búsquedas que incluyan comillas, caracteres de escape o cláusulas SQL maliciosas (ej. `' OR '1'='1`) deben tratarse como texto literal y no alterar la integridad ni ejecución de las consultas.
- **Términos de búsqueda vacíos o con palabras vacías**: Consultas con espacios en blanco o conectores irrelevantes ("de", "el", "para") deben normalizarse adecuadamente y responder de forma amigable sin errores.
- **Agotamiento total de existencias en pedido**: Cuando un pedido consume exactamente el stock disponible restante, el stock resultante debe ser 0 y futuras solicitudes deben marcarse como agotadas.
- **Límite superior de compra**: Intentos de compra de 21 o más unidades deben ser rechazados de inmediato bajo la regla de negocio de compra máxima por orden.
- **Caracteres especiales y tildes en nombres de productos**: La búsqueda debe resolver coincidencias independientemente de mayúsculas, minúsculas o signos diacríticos (ej. "IdeaPad" vs "ideapad").

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: La base de datos DEBE implementarse en SQLite con esquema relacional conteniendo tablas para categorías, productos, clientes y pedidos.
- **FR-002**: El catálogo inicial DEBE contener exactamente 48 productos distribuidos en 6 categorías, con exactamente 9 productos con stock inicial en 0 (agotados).
- **FR-003**: Los productos clave de prueba DEBEN conservar invariables sus identificadores, nombres y stocks iniciales: ID 9 "Laptop Lenovo IdeaPad 15" (stock 12), ID 26 "Monitor Samsung Odyssey G3 24 pulgadas" (stock 0), ID 40 "Mouse Logitech M185" (stock 60).
- **FR-004**: La función `consultar_stock(producto: str) -> str` DEBE devolver una cadena de texto amigable indicando la cantidad disponible o el estado "agotado" si el stock es 0.
- **FR-005**: La función `consultar_precio(producto: str) -> str` DEBE devolver una cadena de texto con el precio unitario expresado exclusivamente en dólares estadounidenses (USD).
- **FR-006**: Si una búsqueda de stock o precio arroja múltiples coincidencias, el sistema DEBE retornar una lista formateada con ID, nombre y precio referencial de cada opción, sin elegir arbitrariamente ninguna.
- **FR-007**: Si una búsqueda no encuentra resultados, el sistema DEBE retornar un mensaje explicativo sin lanzar excepciones.
- **FR-008**: La función `registrar_pedido(cliente: str, email: str, producto_id: int, cantidad: int) -> str` DEBE validar que la cantidad sea un entero entre 1 y 20, el email cumpla con un patrón válido, el producto exista y haya suficiente stock.
- **FR-009**: Al completarse un pedido exitoso, `registrar_pedido` DEBE retornar un texto que contenga obligatoriamente: identificador del pedido, nombre del producto, cantidad adquirida y monto total en USD.
- **FR-010**: Si falla cualquier validación en `registrar_pedido`, el sistema DEBE rechazar la transacción de manera atómica, garantizando que el stock y los pedidos no sufran ninguna modificación.
- **FR-011**: La función `listar_pedidos(email: str) -> str` DEBE retornar la relación de pedidos asociados al correo con producto, cantidad, total en USD y fecha, o un mensaje claro si no existen registros.
- **FR-012**: Todas las tools DEBEN capturar internamente cualquier error o excepción y retornar siempre un valor de tipo `str`.
- **FR-013**: Todas las consultas a la base de datos DEBEN ejecutarse mediante SQL parametrizado con marcadores de posición (`?`), prohibiéndose la concatenación de cadenas.
- **FR-014**: DEBEN generarse 48 fichas técnicas en `data/docs/` con la nomenclatura `ficha_<slug>.md`, con 12 fichas completas y 36 fichas breves, estructuradas con secciones Markdown (`##`) para chunking RAG.
- **FR-015**: Las fichas técnicas NO DEBEN contener bajo ninguna circunstancia valores de precio ni existencias de stock.
- **FR-016**: La suite de pruebas automatizadas con `pytest` en `tests/test_tools_db.py` DEBE ejecutarse al 100% en verde sobre una base de datos temporal aislada sin alterar la base de producción.

### Key Entities *(include if feature involves data)*

- **Categoria**: Representa la agrupación lógica de productos (6 categorías: Laptops, Componentes, Periféricos, Monitores, Almacenamiento, Redes/Accesorios). Atributos clave: id, nombre.
- **Producto**: Artículo del catálogo comercial. Atributos: id, nombre único, categoría asociada, precio en USD, stock numérico (>= 0), estado activo.
- **Cliente**: Comprador registrado por su correo electrónico. Atributos: id, nombre, email único, fecha de creación.
- **Pedido**: Registro transaccional de una compra confirmada. Atributos: id, cliente asociado, producto adquirido, cantidad comprada, precio unitario histórico en USD, total en USD, estado ('pendiente_pago', 'pagado', 'cancelado'), fecha de registro y actualización.
- **FichaTecnica**: Documento Markdown descriptivo de conocimiento estático para RAG. Estructura: título exacto del producto, categoría, secciones 'Descripción', 'Especificaciones', 'Uso recomendado', 'Garantía referencial'.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El 100% de las pruebas automatizadas en `tests/test_tools_db.py` se ejecutan exitosamente con `pytest` en verde sin fallos.
- **SC-002**: El catálogo inicial contiene exactamente 48 productos validados, con 6 categorías y exactamente 9 productos en condición de agotados (stock = 0).
- **SC-003**: El tiempo de respuesta de cualquier consulta de catálogo o registro de pedido en la capa de datos es inferior a 50 milisegundos en entorno local.
- **SC-004**: Cero fallos no controlados o excepciones no capturadas al invocar las 4 tools bajo cualquier tipo de entrada (incluyendo valores nulos, caracteres especiales o cargas útiles de inyección SQL).
- **SC-005**: 100% de consistencia atómica: ante un pedido fallido o cancelado, la discrepancia en stock de inventario es exactamente 0.
- **SC-006**: Se cuenta con las 48 fichas técnicas en `data/docs/` con el 100% de cumplimiento de la convención de títulos y secciones `##`, con 0% de filtración de precios o stock.
- **SC-007**: El archivo `README.md` permite la inicialización y prueba completa de la capa de datos desde un entorno limpio siguiendo sus instrucciones paso a paso.

## Assumptions

- **Aislamiento de capa**: Las funciones de la capa de datos no realizan llamadas de red a APIs externas ni invocan modelos LLM; la conversión a soles y el envío de correos son responsabilidad de fases posteriores.
- **Moneda base**: Todos los precios y totales se almacenan y expresan exclusivamente en USD.
- **Almacenamiento local**: La base de datos SQLite se almacena en la ruta `data/tienda.db` en producción y en directorios temporales durante la ejecución de pruebas.
- **Formato de correo**: La validación de correos electrónicos requiere una estructura básica estándar (`usuario@dominio.extension`) suficiente para control de datos en tienda.
- **Políticas de garantía**: Las referencias a garantías en las fichas técnicas hacen mención al documento central `garantias.md` sin detallar cláusulas legales dinámicas.
