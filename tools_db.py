"""Tools de la capa de datos de PixelOrbe (SQLite).

Contrato con el equipo:
- Todas las tools devuelven `str` y nunca lanzan excepciones.
- Los precios se devuelven en USD (la conversión a soles la hace otro módulo).
- Cuando registrar_pedido o registrar_pago tienen éxito, el texto incluye el id del pedido,
  el nombre del producto, la cantidad y el total (se usan en el correo de confirmación).
- Si el nombre de un producto es ambiguo (ej. "mouse"), la tool lista las opciones con su id
  y el agente le pregunta al cliente cuál quiere.

Tools del contrato:
    consultar_stock, consultar_precio, registrar_pedido, listar_pedidos
Tools extra:
    registrar_pago, consultar_estado_pedido, cancelar_pedido,
    listar_categorias, productos_por_categoria

Seguridad: todo el SQL usa parámetros (?), nunca se concatena texto del cliente.
"""
import os
import re
import sqlite3
import unicodedata
from contextlib import closing, contextmanager
from functools import wraps
from pathlib import Path

# Variable de módulo: los tests la sustituyen con monkeypatch para usar una BD temporal
RUTA_DB = Path(__file__).parent / "data" / "tienda.db"

NOMBRE_TIENDA = os.getenv("NOMBRE_TIENDA", "PixelOrbe")
MAX_CANTIDAD = 20      # tope razonable de unidades por pedido
MAX_LISTA = 10         # máximo de opciones que se listan cuando hay varias coincidencias
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Palabras que se ignoran al buscar productos ("el stock del ideapad" -> "stock", "ideapad")
PALABRAS_VACIAS = {
    "de", "del", "la", "el", "los", "las", "un", "una", "para", "con", "y", "en", "por",
}

# Métodos de pago aceptados (clave normalizada -> valor guardado en la BD)
METODOS_PAGO = {
    "transferencia": "transferencia",
    "billetera": "billetera_digital",
    "billetera_digital": "billetera_digital",
    "tarjeta": "tarjeta",
}

TEXTO_ESTADO = {
    "pendiente_pago": "pendiente de pago",
    "pagado": "pagado",
    "cancelado": "cancelado",
}

MSG_ERROR_BD = (
    "Tuve un problema para acceder a la base de datos. "
    "Intenta de nuevo en unos minutos."
)


class _Rechazo(Exception):
    """Se usa dentro de una transacción para cancelarla con un mensaje amigable."""


def _seguro(funcion):
    """Garantiza que la tool devuelva texto aunque falle SQLite."""
    @wraps(funcion)
    def envoltura(*args, **kwargs):
        try:
            return funcion(*args, **kwargs)
        except sqlite3.Error:
            return MSG_ERROR_BD
    return envoltura


# ---------------------------------------------------------------- helpers

def _conectar() -> sqlite3.Connection:
    """Abre la BD con filas tipo diccionario y claves foráneas activadas."""
    if not Path(RUTA_DB).exists():
        raise sqlite3.OperationalError("La base de datos no existe (ejecuta init_db.py)")
    # isolation_level=None: las transacciones se manejan a mano (BEGIN IMMEDIATE / COMMIT)
    con = sqlite3.connect(RUTA_DB, isolation_level=None, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def _normalizar(texto) -> str:
    """Minúsculas y sin tildes, para que "Audífonos" y "audifonos" coincidan."""
    if texto is None:
        texto = ""
    descompuesto = unicodedata.normalize("NFD", str(texto))
    sin_tildes = "".join(c for c in descompuesto if unicodedata.category(c) != "Mn")
    return " ".join(sin_tildes.lower().split())


def _a_entero(valor):
    """Convierte a int si es posible (acepta "2" o 2.0); si no, devuelve None."""
    if isinstance(valor, bool):
        return None
    if isinstance(valor, int):
        return valor
    if isinstance(valor, float) and valor.is_integer():
        return int(valor)
    if isinstance(valor, str):
        limpio = valor.strip()
        if re.fullmatch(r"-?\d+", limpio):
            return int(limpio)
    return None


def _usd(monto: float) -> str:
    return f"USD {monto:,.2f}"


def _email_valido(email) -> bool:
    return isinstance(email, str) and bool(EMAIL_RE.match(email.strip()))


def _buscar_productos(con: sqlite3.Connection, texto) -> list:
    """Busca productos activos comparando texto normalizado en Python.

    LIKE de SQLite no ignora tildes, por eso se compara aquí sobre los 48 productos.
    Si el texto coincide exactamente con un nombre, devuelve solo ese producto.
    Si no, devuelve los productos cuyo nombre contiene todas las palabras buscadas.
    """
    consulta = _normalizar(texto)
    palabras = [
        p for p in consulta.split() if p not in PALABRAS_VACIAS and len(p) > 1
    ]
    if not palabras:
        return []

    filas = con.execute(
        """SELECT p.id, p.nombre, c.nombre AS categoria, p.precio_usd, p.stock
           FROM productos p JOIN categorias c ON c.id = p.categoria_id
           WHERE p.activo = 1
           ORDER BY p.id"""
    ).fetchall()

    exactas = [f for f in filas if _normalizar(f["nombre"]) == consulta]
    if exactas:
        return exactas
    return [f for f in filas if all(p in _normalizar(f["nombre"]) for p in palabras)]


def _registrar_log(con, herramienta: str, texto, resultado: str) -> None:
    """Anota la búsqueda en consultas_log. Nunca debe romper la tool."""
    try:
        con.execute(
            "INSERT INTO consultas_log (herramienta, texto_buscado, resultado) VALUES (?, ?, ?)",
            (herramienta, str(texto)[:200], resultado),
        )
    except sqlite3.Error:
        pass


def _rollback(con) -> None:
    try:
        con.execute("ROLLBACK")
    except sqlite3.Error:
        pass


@contextmanager
def _transaccion(con):
    """BEGIN IMMEDIATE ... COMMIT; si algo falla o se rechaza, hace ROLLBACK."""
    con.execute("BEGIN IMMEDIATE")
    try:
        yield
        con.execute("COMMIT")
    except BaseException:
        _rollback(con)
        raise


def _linea_producto(p, mostrar_stock: bool) -> str:
    texto = f"- id {p['id']}: {p['nombre']} — {_usd(p['precio_usd'])}"
    if mostrar_stock:
        texto += " — agotado" if p["stock"] == 0 else f" — {p['stock']} en stock"
    return texto


def _lista_opciones(consulta: str, productos: list, mostrar_stock: bool) -> str:
    """Texto para cuando hay varias coincidencias: el agente le pregunta al cliente cuál."""
    lineas = [_linea_producto(p, mostrar_stock) for p in productos[:MAX_LISTA]]
    resto = len(productos) - MAX_LISTA
    extra = f"\n(Hay {resto} resultados más; pide al cliente que sea más específico.)" if resto > 0 else ""
    return (
        f"Encontré {len(productos)} productos que coinciden con «{consulta}». "
        "Pregunta al cliente cuál le interesa (id o nombre completo):\n"
        + "\n".join(lineas)
        + extra
    )


def _no_encontrado(consulta) -> str:
    return f"No encontré ningún producto que coincida con «{consulta}» en el catálogo de {NOMBRE_TIENDA}."


# ---------------------------------------------------------------- tools del contrato

@_seguro
def consultar_stock(producto: str) -> str:
    """Devuelve el stock de un producto (0, 1 o varias coincidencias)."""
    if not isinstance(producto, str) or not producto.strip():
        return "Indícame el nombre del producto que quieres consultar."
    with closing(_conectar()) as con:
        encontrados = _buscar_productos(con, producto)
        if not encontrados:
            _registrar_log(con, "consultar_stock", producto, "no_encontrado")
            return _no_encontrado(producto.strip())
        if len(encontrados) > 1:
            _registrar_log(con, "consultar_stock", producto, "ambiguo")
            return _lista_opciones(producto.strip(), encontrados, mostrar_stock=True)

        p = encontrados[0]
        _registrar_log(con, "consultar_stock", producto, "encontrado")
        if p["stock"] == 0:
            return f"«{p['nombre']}» (id {p['id']}) está agotado: 0 unidades disponibles."
        return f"«{p['nombre']}» (id {p['id']}) tiene {p['stock']} unidades disponibles."


@_seguro
def consultar_precio(producto: str) -> str:
    """Devuelve el precio en USD de un producto (0, 1 o varias coincidencias)."""
    if not isinstance(producto, str) or not producto.strip():
        return "Indícame el nombre del producto que quieres consultar."
    with closing(_conectar()) as con:
        encontrados = _buscar_productos(con, producto)
        if not encontrados:
            _registrar_log(con, "consultar_precio", producto, "no_encontrado")
            return _no_encontrado(producto.strip())
        if len(encontrados) > 1:
            _registrar_log(con, "consultar_precio", producto, "ambiguo")
            return _lista_opciones(producto.strip(), encontrados, mostrar_stock=False)

        p = encontrados[0]
        _registrar_log(con, "consultar_precio", producto, "encontrado")
        aviso = " (actualmente agotado)" if p["stock"] == 0 else ""
        return f"El precio de «{p['nombre']}» (id {p['id']}) es {_usd(p['precio_usd'])}{aviso}."


@_seguro
def registrar_pedido(cliente: str, email: str, producto_id: int, cantidad: int) -> str:
    """Registra un pedido en una sola transacción y descuenta el stock."""
    # --- validaciones (antes de tocar la BD)
    nombre_cliente = " ".join(str(cliente or "").split())
    if len(nombre_cliente) < 2 or len(nombre_cliente) > 100:
        return "Necesito el nombre del cliente (entre 2 y 100 caracteres) para registrar el pedido."
    if not _email_valido(email):
        return "El email no es válido. Pídele al cliente un correo con formato nombre@dominio.com."
    email_limpio = email.strip().lower()
    id_producto = _a_entero(producto_id)
    if id_producto is None:
        return "El id del producto no es válido."
    unidades = _a_entero(cantidad)
    if unidades is None or unidades <= 0:
        return "La cantidad debe ser un número entero mayor que 0."
    if unidades > MAX_CANTIDAD:
        return f"Por pedido se pueden comprar hasta {MAX_CANTIDAD} unidades. Indica una cantidad menor."

    with closing(_conectar()) as con:
        try:
            with _transaccion(con):
                producto = con.execute(
                    "SELECT id, nombre, precio_usd, stock FROM productos WHERE id = ? AND activo = 1",
                    (id_producto,),
                ).fetchone()
                if producto is None:
                    raise _Rechazo(f"No existe un producto con id {id_producto} en el catálogo.")

                # Descuento atómico: solo se aplica si todavía hay stock suficiente
                descuento = con.execute(
                    "UPDATE productos SET stock = stock - ? WHERE id = ? AND stock >= ?",
                    (unidades, id_producto, unidades),
                )
                if descuento.rowcount == 0:
                    if producto["stock"] == 0:
                        raise _Rechazo(f"«{producto['nombre']}» está agotado, no se puede registrar el pedido.")
                    raise _Rechazo(
                        f"Stock insuficiente: de «{producto['nombre']}» solo quedan "
                        f"{producto['stock']} unidades y se pidieron {unidades}."
                    )

                # Busca al cliente por email; si no existe, lo crea
                fila = con.execute(
                    "SELECT id FROM clientes WHERE email = ?", (email_limpio,)
                ).fetchone()
                if fila is None:
                    id_cliente = con.execute(
                        "INSERT INTO clientes (nombre, email) VALUES (?, ?)",
                        (nombre_cliente, email_limpio),
                    ).lastrowid
                else:
                    id_cliente = fila["id"]

                total = round(producto["precio_usd"] * unidades, 2)
                id_pedido = con.execute(
                    """INSERT INTO pedidos
                       (cliente_id, producto_id, cantidad, precio_unitario_usd, total_usd)
                       VALUES (?, ?, ?, ?, ?)""",
                    (id_cliente, id_producto, unidades, producto["precio_usd"], total),
                ).lastrowid
        except _Rechazo as motivo:
            return str(motivo)

    return (
        "Pedido registrado correctamente.\n"
        f"- Id del pedido: {id_pedido}\n"
        f"- Producto: {producto['nombre']} (id {id_producto})\n"
        f"- Cantidad: {unidades}\n"
        f"- Precio unitario: {_usd(producto['precio_usd'])}\n"
        f"- Total: {_usd(total)}\n"
        "- Estado: pendiente de pago\n"
        "Para completar la compra falta registrar el pago "
        "(transferencia, billetera digital o tarjeta)."
    )


@_seguro
def listar_pedidos(email: str) -> str:
    """Lista los pedidos de un cliente con producto, cantidad, total, estado y fecha."""
    if not _email_valido(email):
        return "El email no es válido. Necesito el correo con el que se hizo el pedido."
    email_limpio = email.strip().lower()
    with closing(_conectar()) as con:
        filas = con.execute(
            """SELECT pe.id, pr.nombre AS producto, pe.cantidad, pe.total_usd,
                      pe.estado, pe.creado_en
               FROM pedidos pe
               JOIN clientes cl ON cl.id = pe.cliente_id
               JOIN productos pr ON pr.id = pe.producto_id
               WHERE cl.email = ?
               ORDER BY pe.id DESC""",
            (email_limpio,),
        ).fetchall()
    if not filas:
        return f"No encontré pedidos registrados con el email {email_limpio}."
    lineas = [
        f"- Pedido #{f['id']}: {f['producto']} x{f['cantidad']} — {_usd(f['total_usd'])} — "
        f"{TEXTO_ESTADO.get(f['estado'], f['estado'])} — {f['creado_en']}"
        for f in filas
    ]
    return f"Pedidos de {email_limpio} ({len(filas)}):\n" + "\n".join(lineas)


# ---------------------------------------------------------------- tools extra

def _pedido_del_cliente(con, id_pedido: int, email_limpio: str):
    """Devuelve el pedido solo si pertenece al email indicado."""
    return con.execute(
        """SELECT pe.id, pe.cantidad, pe.total_usd, pe.estado, pe.producto_id,
                  pr.nombre AS producto
           FROM pedidos pe
           JOIN clientes cl ON cl.id = pe.cliente_id
           JOIN productos pr ON pr.id = pe.producto_id
           WHERE pe.id = ? AND cl.email = ?""",
        (id_pedido, email_limpio),
    ).fetchone()


def _validar_pedido_y_email(pedido_id, email):
    """Devuelve (id_pedido, email_limpio, mensaje_error)."""
    id_pedido = _a_entero(pedido_id)
    if id_pedido is None or id_pedido <= 0:
        return None, None, "El id del pedido no es válido."
    if not _email_valido(email):
        return None, None, "El email no es válido. Necesito el correo con el que se hizo el pedido."
    return id_pedido, email.strip().lower(), None


@_seguro
def registrar_pago(pedido_id: int, email: str, metodo: str, referencia: str = "") -> str:
    """Registra un pago SIMULADO: guarda método y referencia y marca el pedido como pagado."""
    id_pedido, email_limpio, error = _validar_pedido_y_email(pedido_id, email)
    if error:
        return error
    clave_metodo = _normalizar(metodo).replace(" ", "_")
    metodo_bd = METODOS_PAGO.get(clave_metodo)
    if metodo_bd is None:
        return "Método de pago no válido. Opciones: transferencia, billetera digital o tarjeta."
    ref = " ".join(str(referencia or "").split())[:60]

    with closing(_conectar()) as con:
        try:
            with _transaccion(con):
                pedido = _pedido_del_cliente(con, id_pedido, email_limpio)
                if pedido is None:
                    raise _Rechazo(f"No encontré el pedido #{id_pedido} asociado a ese email.")
                if pedido["estado"] == "pagado":
                    raise _Rechazo(f"El pedido #{id_pedido} ya estaba pagado.")
                if pedido["estado"] == "cancelado":
                    raise _Rechazo(f"El pedido #{id_pedido} está cancelado y no se puede pagar.")

                con.execute(
                    "INSERT INTO pagos (pedido_id, metodo, monto_usd, referencia) VALUES (?, ?, ?, ?)",
                    (id_pedido, metodo_bd, pedido["total_usd"], ref or None),
                )
                con.execute(
                    "UPDATE pedidos SET estado = 'pagado', actualizado_en = CURRENT_TIMESTAMP WHERE id = ?",
                    (id_pedido,),
                )
        except _Rechazo as motivo:
            return str(motivo)

    return (
        "Pago registrado correctamente (pago simulado).\n"
        f"- Id del pedido: {id_pedido}\n"
        f"- Producto: {pedido['producto']} (id {pedido['producto_id']})\n"
        f"- Cantidad: {pedido['cantidad']}\n"
        f"- Total pagado: {_usd(pedido['total_usd'])}\n"
        f"- Método: {metodo_bd.replace('_', ' ')}\n"
        f"- Referencia: {ref or 'sin referencia'}\n"
        "- Estado: pagado"
    )


@_seguro
def consultar_estado_pedido(pedido_id: int, email: str) -> str:
    """Muestra el estado de un pedido (solo si el email coincide con el del pedido)."""
    id_pedido, email_limpio, error = _validar_pedido_y_email(pedido_id, email)
    if error:
        return error
    with closing(_conectar()) as con:
        pedido = _pedido_del_cliente(con, id_pedido, email_limpio)
        if pedido is None:
            return f"No encontré el pedido #{id_pedido} asociado a ese email."
        pago = con.execute(
            "SELECT metodo, referencia, pagado_en FROM pagos WHERE pedido_id = ?", (id_pedido,)
        ).fetchone()

    texto = (
        f"Pedido #{id_pedido}: {pedido['producto']} x{pedido['cantidad']} — "
        f"{_usd(pedido['total_usd'])} — {TEXTO_ESTADO.get(pedido['estado'], pedido['estado'])}."
    )
    if pago is not None:
        texto += (
            f" Pagado con {pago['metodo'].replace('_', ' ')} el {pago['pagado_en']}"
            f" (ref. {pago['referencia'] or 'sin referencia'})."
        )
    return texto


@_seguro
def cancelar_pedido(pedido_id: int, email: str) -> str:
    """Cancela un pedido pendiente de pago y devuelve el stock en la misma transacción."""
    id_pedido, email_limpio, error = _validar_pedido_y_email(pedido_id, email)
    if error:
        return error
    with closing(_conectar()) as con:
        try:
            with _transaccion(con):
                pedido = _pedido_del_cliente(con, id_pedido, email_limpio)
                if pedido is None:
                    raise _Rechazo(f"No encontré el pedido #{id_pedido} asociado a ese email.")
                if pedido["estado"] == "cancelado":
                    raise _Rechazo(f"El pedido #{id_pedido} ya estaba cancelado.")
                if pedido["estado"] == "pagado":
                    raise _Rechazo(f"El pedido #{id_pedido} ya fue pagado y no se puede cancelar desde el chat.")

                # La condición estado = 'pendiente_pago' evita devolver el stock dos veces
                cambio = con.execute(
                    """UPDATE pedidos SET estado = 'cancelado', actualizado_en = CURRENT_TIMESTAMP
                       WHERE id = ? AND estado = 'pendiente_pago'""",
                    (id_pedido,),
                )
                if cambio.rowcount == 0:
                    raise _Rechazo(f"No se pudo cancelar el pedido #{id_pedido}.")
                con.execute(
                    "UPDATE productos SET stock = stock + ? WHERE id = ?",
                    (pedido["cantidad"], pedido["producto_id"]),
                )
        except _Rechazo as motivo:
            return str(motivo)

    return (
        f"Pedido #{id_pedido} cancelado. Se devolvieron {pedido['cantidad']} unidades "
        f"de «{pedido['producto']}» al stock."
    )


@_seguro
def listar_categorias() -> str:
    """Lista las categorías del catálogo con la cantidad de productos de cada una."""
    with closing(_conectar()) as con:
        filas = con.execute(
            """SELECT c.nombre, COUNT(p.id) AS total
               FROM categorias c
               LEFT JOIN productos p ON p.categoria_id = c.id AND p.activo = 1
               GROUP BY c.id ORDER BY c.id"""
        ).fetchall()
    if not filas:
        return f"El catálogo de {NOMBRE_TIENDA} no tiene categorías por ahora."
    lineas = [f"- {f['nombre']} ({f['total']} productos)" for f in filas]
    return f"Categorías de {NOMBRE_TIENDA}:\n" + "\n".join(lineas)


@_seguro
def productos_por_categoria(categoria: str) -> str:
    """Lista los productos disponibles (con stock) de una categoría."""
    if not isinstance(categoria, str) or not categoria.strip():
        return "Indícame la categoría que quieres ver."
    consulta = _normalizar(categoria)
    with closing(_conectar()) as con:
        categorias = con.execute("SELECT id, nombre FROM categorias ORDER BY id").fetchall()
        elegida = next((c for c in categorias if _normalizar(c["nombre"]) == consulta), None)
        if elegida is None:
            nombres = ", ".join(c["nombre"] for c in categorias)
            _registrar_log(con, "productos_por_categoria", categoria, "no_encontrado")
            return f"No existe la categoría «{categoria.strip()}». Las categorías son: {nombres}."
        filas = con.execute(
            """SELECT id, nombre, precio_usd, stock FROM productos
               WHERE categoria_id = ? AND activo = 1 AND stock > 0
               ORDER BY id""",
            (elegida["id"],),
        ).fetchall()
        _registrar_log(con, "productos_por_categoria", categoria, "encontrado")
    if not filas:
        return f"Por ahora todos los productos de «{elegida['nombre']}» están agotados."
    lineas = [_linea_producto(f, mostrar_stock=True) for f in filas]
    return f"Productos disponibles en {elegida['nombre']}:\n" + "\n".join(lineas)