"""Pruebas de tools_db.py con una BD temporal (nunca tocan data/tienda.db)."""
import sqlite3

import pytest

import init_db
import tools_db as t


@pytest.fixture
def bd(tmp_path, monkeypatch):
    """Crea una BD temporal con el catálogo original y la usa en ambos módulos."""
    ruta = tmp_path / "tienda.db"
    monkeypatch.setattr(init_db, "RUTA_DB", ruta)
    monkeypatch.setattr(t, "RUTA_DB", ruta)
    init_db.crear_bd(reiniciar=True)
    return ruta


def consulta(ruta, sql, params=()):
    """Ejecuta un SELECT directo en la BD temporal para comprobar resultados."""
    con = sqlite3.connect(ruta)
    try:
        return con.execute(sql, params).fetchall()
    finally:
        con.close()


def stock_de(ruta, producto_id):
    return consulta(ruta, "SELECT stock FROM productos WHERE id = ?", (producto_id,))[0][0]


def contar(ruta, tabla):
    return consulta(ruta, f"SELECT COUNT(*) FROM {tabla}")[0][0]


# ------------------------------------------------------------ catálogo

def test_catalogo_inicial(bd):
    assert contar(bd, "productos") == 48
    assert contar(bd, "categorias") == 6
    assert consulta(bd, "SELECT COUNT(*) FROM productos WHERE stock = 0")[0][0] == 9


# ------------------------------------------------------------ consultar_stock / precio

def test_stock_ideapad_una_coincidencia(bd):
    r = t.consultar_stock("ideapad")
    assert "Laptop Lenovo IdeaPad 15" in r and "12 unidades" in r


def test_stock_agotado(bd):
    assert "agotado" in t.consultar_stock("monitor samsung").lower()


def test_producto_inexistente(bd):
    assert "No encontré" in t.consultar_stock("pasajes de avión")


def test_busqueda_sin_tilde(bd):
    assert "Audífonos" in t.consultar_stock("audifonos")


def test_busqueda_con_mayusculas_y_tildes(bd):
    assert "Audífonos Sony WH-CH520" in t.consultar_stock("AUDÍFONOS sony")


def test_mouse_lista_dos_opciones(bd):
    r = t.consultar_stock("mouse")
    assert "id 31" in r and "id 40" in r
    assert "Mouse Gamer Logitech G203" in r and "Mouse Logitech M185" in r


def test_precio_en_usd(bd):
    r = t.consultar_precio("ideapad")
    assert "USD 599.00" in r


def test_precio_mouse_ambiguo_lista_opciones(bd):
    r = t.consultar_precio("mouse")
    assert "id 31" in r and "id 40" in r


def test_consulta_vacia(bd):
    assert isinstance(t.consultar_stock("   "), str)
    assert isinstance(t.consultar_precio(""), str)


def test_inyeccion_sql_no_rompe_nada(bd):
    r = t.consultar_stock("'; DROP TABLE productos;--")
    assert "No encontré" in r
    assert contar(bd, "productos") == 48


# ------------------------------------------------------------ registrar_pedido

def test_pedido_valido_descuenta_stock(bd):
    r = t.registrar_pedido("Ana", "ana@mail.com", 40, 2)
    assert "Id del pedido: 1" in r
    assert "Mouse Logitech M185" in r and "Cantidad: 2" in r and "USD 29.00" in r
    assert stock_de(bd, 40) == 58


def test_pedido_guarda_estado_pendiente_y_cliente(bd):
    t.registrar_pedido("Ana", "ana@mail.com", 40, 2)
    assert consulta(bd, "SELECT estado FROM pedidos")[0][0] == "pendiente_pago"
    assert consulta(bd, "SELECT nombre, email FROM clientes") == [("Ana", "ana@mail.com")]


@pytest.mark.parametrize("cantidad", [0, -1])
def test_pedido_cantidad_invalida(bd, cantidad):
    r = t.registrar_pedido("Ana", "ana@mail.com", 40, cantidad)
    assert "mayor que 0" in r
    assert stock_de(bd, 40) == 60 and contar(bd, "pedidos") == 0


def test_pedido_cantidad_sobre_el_tope(bd):
    r = t.registrar_pedido("Ana", "ana@mail.com", 40, t.MAX_CANTIDAD + 1)
    assert str(t.MAX_CANTIDAD) in r
    assert stock_de(bd, 40) == 60


def test_pedido_email_invalido(bd):
    r = t.registrar_pedido("Ana", "malmail", 40, 1)
    assert "email" in r.lower()
    assert stock_de(bd, 40) == 60 and contar(bd, "pedidos") == 0


def test_pedido_producto_agotado(bd):
    r = t.registrar_pedido("Ana", "ana@mail.com", 26, 1)
    assert "agotado" in r.lower()
    assert stock_de(bd, 26) == 0 and contar(bd, "pedidos") == 0


def test_pedido_mayor_al_stock(bd):
    r = t.registrar_pedido("Ana", "ana@mail.com", 9, 13)
    assert "insuficiente" in r.lower()
    assert stock_de(bd, 9) == 12 and contar(bd, "pedidos") == 0


def test_pedido_producto_inexistente(bd):
    assert "No existe" in t.registrar_pedido("Ana", "ana@mail.com", 999, 1)


def test_pedido_rechazado_no_crea_cliente(bd):
    """Si el pedido falla, la transacción se revierte completa (tampoco queda el cliente)."""
    t.registrar_pedido("Luis", "luis@mail.com", 9, 13)
    assert contar(bd, "clientes") == 0


def test_mismo_email_un_solo_cliente(bd):
    t.registrar_pedido("Ana", "ana@mail.com", 40, 1)
    t.registrar_pedido("Ana Gómez", "ANA@mail.com", 9, 1)
    assert contar(bd, "clientes") == 1 and contar(bd, "pedidos") == 2


def test_pedido_conserva_precio_del_momento(bd):
    t.registrar_pedido("Ana", "ana@mail.com", 40, 2)
    con = sqlite3.connect(bd)
    con.execute("UPDATE productos SET precio_usd = 99 WHERE id = 40")
    con.commit()
    con.close()
    assert consulta(bd, "SELECT precio_unitario_usd, total_usd FROM pedidos") == [(14.5, 29.0)]


# ------------------------------------------------------------ listar y estado

def test_listar_pedidos_tras_un_pedido(bd):
    t.registrar_pedido("Ana", "ana@mail.com", 40, 2)
    r = t.listar_pedidos("ana@mail.com")
    assert "Pedido #1" in r and "Mouse Logitech M185" in r and "USD 29.00" in r


def test_listar_pedidos_sin_pedidos(bd):
    assert "No encontré pedidos" in t.listar_pedidos("nadie@mail.com")


def test_listar_pedidos_email_invalido(bd):
    assert "no es válido" in t.listar_pedidos("xxx")


def test_estado_solo_para_el_dueno(bd):
    t.registrar_pedido("Ana", "ana@mail.com", 40, 2)
    assert "pendiente de pago" in t.consultar_estado_pedido(1, "ana@mail.com")
    assert "No encontré" in t.consultar_estado_pedido(1, "otro@mail.com")


# ------------------------------------------------------------ cancelar

def test_cancelar_devuelve_stock(bd):
    t.registrar_pedido("Ana", "ana@mail.com", 40, 2)
    assert stock_de(bd, 40) == 58
    r = t.cancelar_pedido(1, "ana@mail.com")
    assert "cancelado" in r
    assert stock_de(bd, 40) == 60
    assert consulta(bd, "SELECT estado FROM pedidos")[0][0] == "cancelado"


def test_cancelar_con_email_ajeno(bd):
    t.registrar_pedido("Ana", "ana@mail.com", 40, 2)
    assert "No encontré" in t.cancelar_pedido(1, "otro@mail.com")
    assert stock_de(bd, 40) == 58


def test_cancelar_dos_veces_no_duplica_stock(bd):
    t.registrar_pedido("Ana", "ana@mail.com", 40, 2)
    t.cancelar_pedido(1, "ana@mail.com")
    assert "ya estaba cancelado" in t.cancelar_pedido(1, "ana@mail.com")
    assert stock_de(bd, 40) == 60


# ------------------------------------------------------------ pagos (simulados)

def test_pago_marca_pedido_como_pagado(bd):
    t.registrar_pedido("Ana", "ana@mail.com", 40, 2)
    r = t.registrar_pago(1, "ana@mail.com", "billetera digital", "R-77")
    assert "Pago registrado" in r and "Id del pedido: 1" in r and "USD 29.00" in r
    assert consulta(bd, "SELECT estado FROM pedidos")[0][0] == "pagado"
    assert consulta(bd, "SELECT metodo, monto_usd, referencia FROM pagos") == [
        ("billetera_digital", 29.0, "R-77")
    ]


def test_pago_doble_rechazado(bd):
    t.registrar_pedido("Ana", "ana@mail.com", 40, 2)
    t.registrar_pago(1, "ana@mail.com", "tarjeta")
    assert "ya estaba pagado" in t.registrar_pago(1, "ana@mail.com", "tarjeta")
    assert contar(bd, "pagos") == 1


def test_pago_metodo_invalido(bd):
    t.registrar_pedido("Ana", "ana@mail.com", 40, 2)
    assert "no válido" in t.registrar_pago(1, "ana@mail.com", "bitcoin")
    assert contar(bd, "pagos") == 0


def test_pago_email_ajeno(bd):
    t.registrar_pedido("Ana", "ana@mail.com", 40, 2)
    assert "No encontré" in t.registrar_pago(1, "otro@mail.com", "tarjeta")
    assert contar(bd, "pagos") == 0


def test_no_se_paga_pedido_cancelado(bd):
    t.registrar_pedido("Ana", "ana@mail.com", 40, 2)
    t.cancelar_pedido(1, "ana@mail.com")
    assert "cancelado" in t.registrar_pago(1, "ana@mail.com", "tarjeta")
    assert contar(bd, "pagos") == 0


def test_no_se_cancela_pedido_pagado(bd):
    t.registrar_pedido("Ana", "ana@mail.com", 40, 2)
    t.registrar_pago(1, "ana@mail.com", "transferencia")
    assert "no se puede cancelar" in t.cancelar_pedido(1, "ana@mail.com")
    assert stock_de(bd, 40) == 58


# ------------------------------------------------------------ categorías

def test_listar_categorias(bd):
    r = t.listar_categorias()
    for nombre in ["smartphones", "laptops", "audio", "gaming", "wearables", "accesorios"]:
        assert nombre in r


def test_productos_por_categoria_excluye_agotados(bd):
    r = t.productos_por_categoria("Audio")
    assert "Parlante JBL Flip 6" in r
    assert "Parlante JBL Go 3" not in r  # agotado (id 21)


def test_categoria_inexistente(bd):
    assert "No existe la categoría" in t.productos_por_categoria("ropa")


# ------------------------------------------------------------ log y robustez

def test_consultas_log_registra_ambiguo(bd):
    t.consultar_stock("mouse")
    assert consulta(bd, "SELECT herramienta, resultado FROM consultas_log") == [
        ("consultar_stock", "ambiguo")
    ]


def test_sin_base_de_datos_devuelve_texto(tmp_path, monkeypatch):
    monkeypatch.setattr(t, "RUTA_DB", tmp_path / "no_existe.db")
    r = t.consultar_stock("ideapad")
    assert isinstance(r, str) and "base de datos" in r