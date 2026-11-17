"""Crea y llena la base de datos SQLite de PixelOrbe.

Tablas: categorias, productos, clientes, pedidos, pagos y consultas_log.
El pago es simulado: se registra el método y la referencia, pero no se verifica dinero real.

Uso:
    python init_db.py          -> crea la BD si no existe y agrega lo que falte
    python init_db.py --reset  -> borra la BD y la deja como el catálogo original

Nota: si ya tenías una tienda.db con el esquema anterior, corre --reset una vez,
porque CREATE TABLE IF NOT EXISTS no modifica tablas que ya existen.
"""
import sqlite3
import sys
from pathlib import Path

# Variable de módulo: los tests la sustituyen con monkeypatch para usar una BD temporal
RUTA_DB = Path(__file__).parent / "data" / "tienda.db"

ESQUEMA = """
-- Categorías del catálogo (evita errores de escritura como "Laptops" vs "laptops")
CREATE TABLE IF NOT EXISTS categorias (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre  TEXT NOT NULL UNIQUE
);

-- Catálogo de productos con su precio (USD) y stock actual
CREATE TABLE IF NOT EXISTS productos (
    id            INTEGER PRIMARY KEY,
    nombre        TEXT    NOT NULL UNIQUE,
    categoria_id  INTEGER NOT NULL,
    precio_usd    REAL    NOT NULL CHECK (precio_usd > 0),
    stock         INTEGER NOT NULL CHECK (stock >= 0),
    activo        INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1)),
    FOREIGN KEY (categoria_id) REFERENCES categorias(id)
);

-- Clientes que han comprado (el email identifica a cada persona)
CREATE TABLE IF NOT EXISTS clientes (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre     TEXT NOT NULL,
    email      TEXT NOT NULL UNIQUE,
    creado_en  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Pedidos: guardan el precio del momento para que no cambien si el producto sube o baja
CREATE TABLE IF NOT EXISTS pedidos (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id           INTEGER NOT NULL,
    producto_id          INTEGER NOT NULL,
    cantidad             INTEGER NOT NULL CHECK (cantidad > 0),
    precio_unitario_usd  REAL    NOT NULL,
    total_usd            REAL    NOT NULL,
    estado               TEXT    NOT NULL DEFAULT 'pendiente_pago'
                         CHECK (estado IN ('pendiente_pago', 'pagado', 'cancelado')),
    creado_en            TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en       TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cliente_id)  REFERENCES clientes(id),
    FOREIGN KEY (producto_id) REFERENCES productos(id)
);

-- Pagos simulados: un pedido solo puede pagarse una vez (pedido_id UNIQUE)
CREATE TABLE IF NOT EXISTS pagos (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id   INTEGER NOT NULL UNIQUE,
    metodo      TEXT    NOT NULL
                CHECK (metodo IN ('transferencia', 'billetera_digital', 'tarjeta')),
    monto_usd   REAL    NOT NULL CHECK (monto_usd > 0),
    referencia  TEXT,
    pagado_en   TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pedido_id) REFERENCES pedidos(id)
);

-- Bitácora de búsquedas del bot (sirve para métricas del informe)
CREATE TABLE IF NOT EXISTS consultas_log (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha          TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    herramienta    TEXT NOT NULL,
    texto_buscado  TEXT,
    resultado      TEXT NOT NULL
                   CHECK (resultado IN ('encontrado', 'no_encontrado', 'ambiguo', 'error'))
);

CREATE INDEX IF NOT EXISTS idx_productos_categoria ON productos(categoria_id);
CREATE INDEX IF NOT EXISTS idx_pedidos_cliente     ON pedidos(cliente_id);
CREATE INDEX IF NOT EXISTS idx_pedidos_producto    ON pedidos(producto_id);
"""

# Catálogo: 6 categorías, 48 productos. Precios en USD. Hay 9 productos agotados (stock 0).
PRODUCTOS = [
    # (id, nombre, categoria, precio_usd, stock)

    # --- Smartphones (1-8) ---
    (1,  "Smartphone Nova 10 Pro",                  "smartphones",  506.40, 15),
    (2,  "Smartphone Samsung Galaxy A55",           "smartphones",  389.00,  0),
    (3,  "iPhone 15 128GB",                         "smartphones",  699.00,  8),
    (4,  "iPhone 16 Pro 256GB",                     "smartphones", 1099.00,  5),
    (5,  "Smartphone Xiaomi Redmi Note 13",         "smartphones",  229.00, 25),
    (6,  "Smartphone Motorola Moto G84",            "smartphones",  219.00, 18),
    (7,  "Smartphone Samsung Galaxy S24 Ultra",     "smartphones", 1199.00,  0),
    (8,  "Smartphone Honor X8b",                    "smartphones",  249.00, 12),

    # --- Laptops (9-16) ---
    (9,  "Laptop Lenovo IdeaPad 15",                "laptops",      599.00, 12),
    (10, "Laptop Asus TUF Gaming",                  "laptops",      826.67,  6),
    (11, "Laptop HP Pavilion 14",                   "laptops",      679.90,  5),
    (12, "MacBook Air M3 13 pulgadas",              "laptops",     1149.00,  4),
    (13, "Laptop Acer Aspire 5",                    "laptops",      549.00, 10),
    (14, "Laptop Dell Inspiron 15",                 "laptops",      589.00,  0),
    (15, "Laptop MSI Katana 15 RTX 4060",           "laptops",     1299.00,  3),
    (16, "Laptop Lenovo Legion 5",                  "laptops",     1199.00,  0),

    # --- Audio (17-24) ---
    (17, "Auriculares Gaming Asus ROG Delta S",     "audio",        239.73, 10),
    (18, "Parlante JBL Flip 6",                     "audio",        129.00, 20),
    (19, "Audífonos Sony WH-CH520",                 "audio",         59.90, 18),
    (20, "Audífonos Apple AirPods Pro 2",           "audio",        249.00,  7),
    (21, "Parlante JBL Go 3",                       "audio",         39.90,  0),
    (22, "Auriculares Studio Audio-Technica M40x",  "audio",         99.00,  9),
    (23, "Micrófono Condensador HyperX QuadCast",   "audio",        139.00,  6),
    (24, "Audífonos JBL Tune 510BT",                "audio",         39.00, 30),

    # --- Gaming (25-32) ---
    (25, "Consola PlayStation 5 Digital Pro 2TB",   "gaming",       933.07,  4),
    (26, "Monitor Samsung Odyssey G3 24 pulgadas",  "gaming",       189.00,  0),
    (27, "Mando Xbox Series X",                     "gaming",        59.99, 22),
    (28, "Consola Nintendo Switch OLED",            "gaming",       349.00,  6),
    (29, "Monitor LG UltraGear 27 144Hz",           "gaming",       219.00,  8),
    (30, "Teclado Mecánico Redragon Kumara",        "gaming",        32.00, 25),
    (31, "Mouse Gamer Logitech G203",               "gaming",        29.90, 35),
    (32, "Silla Gaming Ergonómica Cougar",          "gaming",       179.00,  0),

    # --- Wearables (33-38) ---
    (33, "Reloj inteligente GTS7 Pro",              "wearables",    290.40,  9),
    (34, "Smartband Xiaomi Band 8",                 "wearables",     45.00, 30),
    (35, "Apple Watch Series 9",                    "wearables",    399.00,  5),
    (36, "Smartwatch Samsung Galaxy Watch 6",       "wearables",    299.00,  0),
    (37, "Smartwatch Amazfit Bip 5",                "wearables",     79.00, 16),
    (38, "Smartband Huawei Band 9",                 "wearables",     55.00, 20),

    # --- Accesorios (39-48) ---
    (39, "Escritorio Gamer Racing Orange 129.5cm",  "accesorios",    71.73,  7),
    (40, "Mouse Logitech M185",                     "accesorios",    14.50, 60),
    (41, "Disco SSD Kingston 1TB",                  "accesorios",    74.50, 30),
    (42, "Power Bank Anker 30000mAh",               "accesorios",    49.90, 20),
    (43, "Hub USB-C Multipuerto 7 en 1",            "accesorios",    29.90, 25),
    (44, "Webcam Logitech C920 HD",                 "accesorios",    69.90,  0),
    (45, "Cargador Rápido USB-C 65W",               "accesorios",    24.90, 40),
    (46, "Router TP-Link Archer C6",                "accesorios",    45.00, 14),
    (47, "Disco Duro Externo WD 2TB",               "accesorios",    69.00, 11),
    (48, "Cámara GoPro Hero 12",                    "accesorios",   349.00,  7),
]


def _categorias_en_orden() -> list[str]:
    """Devuelve las categorías únicas respetando el orden en que aparecen en PRODUCTOS."""
    vistas: list[str] = []
    for _, _, categoria, _, _ in PRODUCTOS:
        if categoria not in vistas:
            vistas.append(categoria)
    return vistas


def crear_bd(reiniciar: bool = False) -> None:
    RUTA_DB.parent.mkdir(parents=True, exist_ok=True)
    if reiniciar and RUTA_DB.exists():
        RUTA_DB.unlink()  # borra la BD para empezar limpio

    con = sqlite3.connect(RUTA_DB)
    try:
        con.execute("PRAGMA foreign_keys = ON")  # activa las claves foráneas
        con.executescript(ESQUEMA)

        # Primero las categorías (OR IGNORE: no duplica si el script se corre dos veces)
        con.executemany(
            "INSERT OR IGNORE INTO categorias (nombre) VALUES (?)",
            [(c,) for c in _categorias_en_orden()],
        )

        # Luego los productos: el nombre de la categoría se traduce a su id con una subconsulta
        # OR IGNORE: no pisa el stock si el script se corre dos veces
        con.executemany(
            """INSERT OR IGNORE INTO productos (id, nombre, categoria_id, precio_usd, stock)
               VALUES (?, ?, (SELECT id FROM categorias WHERE nombre = ?), ?, ?)""",
            PRODUCTOS,
        )
        con.commit()
    finally:
        con.close()
    print(
        f"BD lista en {RUTA_DB} con {len(PRODUCTOS)} productos "
        f"en {len(_categorias_en_orden())} categorías"
    )


if __name__ == "__main__":
    crear_bd(reiniciar="--reset" in sys.argv)