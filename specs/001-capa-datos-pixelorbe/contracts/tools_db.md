# Interface Contract: Tools de Base de Datos (`tools_db.py`)

**Feature**: `specs/001-capa-datos-pixelorbe`
**Date**: 2026-11-16
**Status**: Stable

## Principios del Contrato
1. **Tipado Estricto de Retorno**: Todas las funciones públicas retornan exclusivamente `str`.
2. **Cero Excepciones**: Ninguna excepción se propaga hacia el llamador; los errores se capturan internamente y retornan mensajes descriptivos en lenguaje natural.
3. **Moneda Base**: Todos los importes monetarios se expresan y calculan en dólares estadounidenses (USD).
4. **Seguridad**: Todas las consultas SQL están estrictamente parametrizadas con marcadores `?`.

---

## 1. `consultar_stock`

### Firma
```python
def consultar_stock(producto: str) -> str:
```

### Parámetros
- `producto` (`str`): Término de búsqueda, nombre completo o ID numérico del producto.

### Comportamiento
1. Si `producto` está vacío o solo contiene espacios: Retorna mensaje solicitando ingresar un nombre.
2. Si coincide con 0 productos: Retorna `"No encontré ningún producto que coincida con '[término]'."`
3. Si coincide con exactamente 1 producto:
   - Si `stock == 0`: Retorna `"[Nombre completo]: AGOTADO (0 unidades disponibles)."`
   - Si `stock > 0`: Retorna `"[Nombre completo]: [stock] unidades disponibles."`
4. Si coincide con múltiples productos (2 o más):
   - Retorna lista con ID, nombre y precio de cada opción para que el usuario precise su consulta:
     ```text
     Encontré varias coincidencias para '[término]'. Por favor especifica cuál deseas:
     - [ID] Nombre del Producto (USD $Precio)
     - [ID] Otro Producto (USD $Precio)
     ```

---

## 2. `consultar_precio`

### Firma
```python
def consultar_precio(producto: str) -> str:
```

### Parámetros
- `producto` (`str`): Término de búsqueda, nombre completo o ID numérico del producto.

### Comportamiento
1. Si coincide con 0 productos: Retorna mensaje de producto no encontrado.
2. Si coincide con exactamente 1 producto:
   - Retorna precio unitario formateado en USD y estado de inventario si está agotado:
     - Con stock: `"[Nombre completo]: USD $[precio_usd]."`
     - Sin stock: `"[Nombre completo]: USD $[precio_usd] (Actualmente agotado)."`
3. Si coincide con múltiples productos:
   - Retorna lista idéntica al formato de desambiguación de `consultar_stock`.

---

## 3. `registrar_pedido`

### Firma
```python
def registrar_pedido(cliente: str, email: str, producto_id: int, cantidad: int) -> str:
```

### Parámetros
- `cliente` (`str`): Nombre del comprador (no vacío).
- `email` (`str`): Correo electrónico válido (`^[^@\s]+@[^@\s]+\.[^@\s]+$`).
- `producto_id` (`int`): ID numérico del producto en el catálogo.
- `cantidad` (`int`): Unidades solicitadas (entero estrictamente mayor a 0 y menor o igual a 20).

### Validaciones y Manejo de Errores
- Si `cantidad <= 0` o `cantidad > 20`: Retorna mensaje de error explicando el rango permitido (1 a 20 unidades).
- Si `email` no cumple el formato: Retorna mensaje indicando correo inválido.
- Si `producto_id` no existe en catálogo o está inactivo: Retorna mensaje de producto no encontrado.
- Si `stock < cantidad`: Retorna mensaje indicando stock insuficiente (mostrando unidades disponibles).
- En cualquiera de estos fallos, la base de datos ejecuta `ROLLBACK` y el stock NO se modifica.

### Éxito
- Ejecuta en una sola transacción atómica (`BEGIN IMMEDIATE`):
  1. Descuento condicional: `UPDATE productos SET stock = stock - ? WHERE id = ? AND stock >= ?`
  2. Registro o recuperación del cliente en tabla `clientes`.
  3. Inserción de orden en tabla `pedidos` con estado `'pendiente_pago'`.
  4. `COMMIT`.
- Retorna texto de confirmación conteniendo:
  - ID del pedido generado.
  - Nombre exacto del producto.
  - Cantidad de unidades.
  - Total calculado en USD.
  - Indicación de estado pendiente de pago.

---

## 4. `listar_pedidos`

### Firma
```python
def listar_pedidos(email: str) -> str:
```

### Parámetros
- `email` (`str`): Dirección de correo del cliente a consultar.

### Comportamiento
1. Si `email` tiene formato inválido: Retorna mensaje de error de formato.
2. Si el cliente no existe o no registra pedidos: Retorna `"No se encontraron pedidos registrados para el correo [email]."`
3. Si registra pedidos: Retorna listado ordenado cronológicamente con:
   - ID de pedido.
   - Nombre del producto.
   - Cantidad adquirida.
   - Total en USD.
   - Estado del pedido ('pendiente de pago', 'pagado', 'cancelado').
   - Fecha de registro.
