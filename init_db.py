"""Crea y llena la base de datos SQLite (productos y pedidos)."""
"""Crea y llena la base de datos SQLite (productos y pedidos)."""
import sqlite3
from pathlib import Path

RUTA_DB = Path(__file__).parent / "data" / "tienda.db"

ESQUEMA = """
CREATE TABLE IF NOT EXISTS productos (
    id          INTEGER PRIMARY KEY,
    nombre      TEXT    NOT NULL UNIQUE,
    categoria   TEXT    NOT NULL,
    precio_usd  REAL    NOT NULL CHECK (precio_usd > 0),
    stock       INTEGER NOT NULL CHECK (stock >= 0)
);

CREATE TABLE IF NOT EXISTS pedidos (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente     TEXT    NOT NULL,
    email       TEXT    NOT NULL,
    producto_id INTEGER NOT NULL,
    cantidad    INTEGER NOT NULL CHECK (cantidad > 0),
    total_usd   REAL    NOT NULL,
    fecha       TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (producto_id) REFERENCES productos(id)
);
"""

PRODUCTOS = [
    # (id, nombre, categoria, precio_usd, stock)
    (1,  "Laptop Lenovo IdeaPad 15",   "laptops",     549.00, 12),
    (2,  "Laptop HP Pavilion 14",      "laptops",     679.90,  5),
    (3,  "Mouse Logitech M185",        "accesorios",   14.50, 60),
    (4,  "Teclado Redragon Kumara",    "accesorios",   32.00, 25),
    (5,  "Monitor Samsung 24 pulgadas","monitores",   129.90,  0),
    (6,  "Monitor LG UltraGear 27",    "monitores",   219.00,  8),
    (7,  "Audífonos Sony WH-CH520",    "audio",        59.90, 18),
    (8,  "Parlante JBL Go 3",          "audio",        39.90,  0),
    (9,  "Disco SSD Kingston 1TB",     "almacenamiento", 74.50, 30),
    (10, "Router TP-Link Archer C6",   "redes",        45.00, 14),
]

def crear_bd(reiniciar: bool = False) -> None:
    RUTA_DB.parent.mkdir(parents=True, exist_ok=True)
    if reiniciar and RUTA_DB.exists():
        RUTA_DB.unlink()                       # borra la BD para empezar limpio

    con = sqlite3.connect(RUTA_DB)
    con.execute("PRAGMA foreign_keys = ON")    # activa las claves foráneas
    con.executescript(ESQUEMA)
    con.executemany(
        "INSERT OR IGNORE INTO productos VALUES (?, ?, ?, ?, ?)", PRODUCTOS
    )
    con.commit()
    con.close()
    print(f"BD lista en {RUTA_DB} con {len(PRODUCTOS)} productos")

if __name__ == "__main__":
    import sys
    crear_bd(reiniciar="--reset" in sys.argv)