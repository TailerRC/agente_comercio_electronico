"""Generador de fichas técnicas Markdown para el catálogo de PixelOrbe.

Lee los 48 productos definidos en init_db.py y genera un archivo por producto en data/docs/.
Formato requerido para el corpus RAG (Fase 2 - Jerzy):
- Título principal: `# <nombre exacto en BD>`
- Metadato: `Categoría: <categoría>`
- Secciones '##': Descripción, Especificaciones, Uso recomendado, Garantía referencial.
- 12 fichas detalladas (incluyendo IDs 9, 26, 40 y representantes de las 6 categorías).
- 36 fichas breves (5 a 8 líneas).
- Estricta exclusión de precios y existencias de stock.
"""

import re
import unicodedata
from pathlib import Path

from init_db import PRODUCTOS

DIR_DOCS = Path(__file__).parent / "data" / "docs"

# IDs designados para fichas detalladas (cubre las 6 categorías + IDs clave 9, 26, 40)
IDS_COMPLETAS = {1, 3, 9, 10, 18, 19, 25, 26, 33, 34, 40, 41}

# Datos detallados originales para las 12 fichas completas
FICHAS_DETALLADAS = {
    1: {  # Smartphones
        "descripcion": (
            "Dispositivo móvil de gama media-alta equipado con una pantalla curva OLED "
            "de alta fluidez visual y un sistema fotográfico optimizado para retratos "
            "y creadores de contenido móvil."
        ),
        "especificaciones": [
            "Pantalla OLED de 6.78 pulgadas con tasa de refresco de 120 Hz",
            "Cámara principal de 50 MP Ultra Vision y frontal dual de 60 MP ultra gran angular",
            "Batería de 4000 mAh con tecnología de carga ultrarrápida SuperCharge",
            "Conectividad 4G LTE avanzada, Wi-Fi 6 de doble banda y Bluetooth 5.2",
            "Almacenamiento interno de 256 GB y 8 GB de memoria RAM",
        ],
        "uso_recomendado": (
            "Ideal para creadores de contenido digital, entusiastas de la fotografía móvil "
            "y usuarios que requieren carga ágil y desempeño multitarea constante."
        ),
    },
    3: {  # Smartphones
        "descripcion": (
            "Teléfono inteligente insignia con diseño duradero de vidrio tintado en masa "
            "y estructura de aluminio de grado aeroespacial. Integra interfaz interactiva "
            "Dynamic Island y conector estándar universal."
        ),
        "especificaciones": [
            "Pantalla Super Retina XDR OLED de 6.1 pulgadas de alto brillo",
            "Procesador Apple A16 Bionic de arquitectura eficiente de 6 núcleos",
            "Sistema de dos cámaras con sensor principal de 48 MP y teleobjetivo 2x",
            "Puerto de conexión y transferencia de datos USB-C",
            "Capacidad de almacenamiento interno de 128 GB",
        ],
        "uso_recomendado": (
            "Pensado para profesionales y usuarios que buscan integración fluida en el "
            "ecosistema digital, durabilidad a largo plazo y captura de imagen prémium."
        ),
    },
    9: {  # Laptops (Producto clave de prueba)
        "descripcion": (
            "Computadora portátil equilibrada y moderna orientada a la productividad "
            "académica, administrativa y del hogar, con chasis liviano y teclado "
            "ergonómico con teclado numérico integrado."
        ),
        "especificaciones": [
            "Pantalla antirreflejo Full HD (1920x1080) de 15.6 pulgadas",
            "Procesador Intel Core i5 de 12.ª generación con gráficos Iris Xe",
            "Memoria RAM de 16 GB DDR4 para fluidez en múltiples aplicaciones",
            "Unidad de almacenamiento en estado sólido NVMe M.2 de 512 GB",
            "Puertos de conexión: HDMI, USB-C, USB 3.2 y conector combinado de audio",
            "Autonomía de batería de hasta 7 horas con soporte de carga rápida",
        ],
        "uso_recomendado": (
            "Excelente para estudiantes universitarios, teletrabajo, gestión de documentos, "
            "videoconferencias frecuentes y navegación con múltiples pestañas simultáneas."
        ),
    },
    10: {  # Laptops
        "descripcion": (
            "Portátil de alto rendimiento diseñado para resistir jornadas intensivas de "
            "videojuegos y cómputo pesado, certificado con durabilidad militar y sistema "
            "avanzado de disipación térmica de doble ventilador."
        ),
        "especificaciones": [
            "Pantalla IPS Full HD de 15.6 pulgadas con tasa de actualización de 144 Hz",
            "Procesador AMD Ryzen 7 serie 7000 de alto desempeño",
            "Tarjeta gráfica dedicada NVIDIA GeForce RTX 4050 con 6 GB GDDR6",
            "16 GB de memoria RAM DDR5 expandible y unidad SSD NVMe de 512 GB",
            "Teclado retroiluminado RGB con teclas WASD resaltadas",
        ],
        "uso_recomendado": (
            "Dirigido a entusiastas de los videojuegos competitivos, modelado 3D, "
            "edición de video en alta resolución y desarrollo de software."
        ),
    },
    18: {  # Audio
        "descripcion": (
            "Altavoz portátil inalámbrico diseñado para exteriores que ofrece un audio "
            "potente, nítido y con graves profundos gracias a su sistema de altavoces de 2 vías."
        ),
        "especificaciones": [
            "Certificación IP67 resistente al agua sumergible y al polvo exterior",
            "Hasta 12 horas continuas de reproducción musical con una sola carga",
            "Conectividad Bluetooth 5.1 estable y función PartyBoost para emparejamiento",
            "Radiadores pasivos duales para optimización acústica de frecuencias bajas",
            "Diseño tubular compacto y revestimiento de tela duradera",
        ],
        "uso_recomendado": (
            "Apto para paseos al aire libre, reuniones sociales, piscinas y ambientes "
            "donde se requiere resistencia climática y sonido contundente."
        ),
    },
    19: {  # Audio
        "descripcion": (
            "Audífonos inalámbricos de diadema ultraligeros con almohadillas acolchadas, "
            "diseñados para escuchar música y recibir llamadas durante todo el día con total confort."
        ),
        "especificaciones": [
            "Autonomía sobresaliente de batería de hasta 50 horas de reproducción continua",
            "Tecnología DSEE que restaura la calidad armónica de archivos comprimidos",
            "Conexión multipunto que permite alternar fácilmente entre dos dispositivos Bluetooth",
            "Micrófono incorporado con tecnología de reducción de eco para llamadas nítidas",
            "Estructura ajustable y diseño giratorio plano para fácil transporte",
        ],
        "uso_recomendado": (
            "Perfecto para uso diario en oficinas, viajes, transporte público y sesiones "
            "extensas de estudio o trabajo a distancia."
        ),
    },
    25: {  # Gaming
        "descripcion": (
            "Consola de entretenimiento interactivo de última generación en versión digital, "
            "diseñada para ofrecer transiciones instantáneas, retroalimentación háptica "
            "inmersiva y gráficos con trazado de rayos."
        ),
        "especificaciones": [
            "Unidad de almacenamiento SSD de ultra alta velocidad de 2 TB de capacidad",
            "Soporte para salida de video en 4K hasta 120 cuadros por segundo y tecnología HDR",
            "Arquitectura gráfica basada en AMD RDNA con aceleración por hardware de Ray Tracing",
            "Tecnología de audio 3D Tempest para sonido envolvente posicional",
            "Compatibilidad total con el mando inalámbrico DualSense y gatillos adaptativos",
        ],
        "uso_recomendado": (
            "Para jugadores dedicados que buscan la máxima fidelidad gráfica en títulos "
            "de última hornada y preferencia por bibliotecas de juegos 100% digitales."
        ),
    },
    26: {  # Gaming (Producto clave de prueba - Agotado)
        "descripcion": (
            "Monitor para videojuegos de panel rápido diseñado para responder a la acción "
            "vertiginosa con mínima latencia visual, eliminando el desenfoque de movimiento "
            "y garantizando transiciones suaves."
        ),
        "especificaciones": [
            "Panel plano de 24 pulgadas con resolución Full HD (1920x1080 píxeles)",
            "Tasa de actualización fluida de 144 Hz y tiempo de respuesta de 1 ms MPRT",
            "Soporte para AMD FreeSync Premium que previene el desgarro de imagen (tearing)",
            "Base ergonómica con ajuste de inclinación, giro, altura y rotación vertical (pivote)",
            "Entradas de video DisplayPort 1.2 y HDMI 1.4, salida de auriculares integrada",
        ],
        "uso_recomendado": (
            "Diseñado para deportes electrónicos (eSports), shooters en primera persona (FPS) "
            "y configuraciones de juego donde la velocidad de respuesta es determinante."
        ),
    },
    33: {  # Wearables
        "descripcion": (
            "Reloj inteligente versátil enfocado en el monitoreo integral del bienestar físico, "
            "la gestión de notificaciones del smartphone y el registro de actividad atlética."
        ),
        "especificaciones": [
            "Pantalla táctil AMOLED de 1.75 pulgadas de colores vivos y alta definición",
            "Sensores biométricos para medición continua de ritmo cardíaco y saturación de oxígeno",
            "Más de 100 modos deportivos predefinidos y seguimiento de calidad de sueño",
            "Resistencia al agua certificada de 5 ATM apta para natación en piscina",
            "Batería recargable con duración estimada de 7 a 10 días de uso típico",
        ],
        "uso_recomendado": (
            "Indicado para deportistas recreativos, personas que desean registrar sus "
            "hábitos de salud y usuarios que buscan consultar alertas sin sacar el teléfono."
        ),
    },
    34: {  # Wearables
        "descripcion": (
            "Pulsera de actividad física estilizada con marco metálico y sistema modular de "
            "correas intercambiables, ofreciendo lectura precisa de pasos y condición física."
        ),
        "especificaciones": [
            "Pantalla táctil AMOLED de 1.62 pulgadas con brillo ajustable automático",
            "Monitor continuo de frecuencia cardíaca, estrés, oxígeno en sangre y ciclo del sueño",
            "Autonomía prolongada de hasta 16 días con una sola recarga",
            "Resistencia a inmersiones de hasta 50 metros bajo el agua (5 ATM)",
            "Sincronización inalámbrica vía Bluetooth 5.1 Low Energy con Android e iOS",
        ],
        "uso_recomendado": (
            "Excelente alternativa liviana para usuarios que prefieren un dispositivo discreto "
            "para cuantificar su actividad diaria sin preocuparse por la recarga frecuente."
        ),
    },
    40: {  # Accesorios (Producto clave de prueba)
        "descripcion": (
            "Mouse inalámbrico compacto y ambidiestro con conectividad fiable de largo alcance, "
            "diseñado para ofrecer navegación precisa, practicidad portátil y máxima eficiencia energética."
        ),
        "especificaciones": [
            "Conexión inalámbrica de 2.4 GHz mediante nano receptor USB tipo Plug and Play",
            "Radio de alcance efectivo inalámbrico de hasta 10 metros sin cortes ni demoras",
            "Sensor óptico con resolución precisa de 1000 DPI para desplazamiento fluido",
            "Hasta 12 meses de funcionamiento ininterrumpido con una sola batería AA",
            "Forma contorneada apta para usuarios diestros y zurdos con botón de encendido manual",
        ],
        "uso_recomendado": (
            "Ideal para portátiles, oficinas compartidas, trabajo remoto, bibliotecas y "
            "usuarios que necesitan un mouse confiable que ocupe mínimo espacio en la mochila."
        ),
    },
    41: {  # Accesorios
        "descripcion": (
            "Unidad de almacenamiento en estado sólido de formato 2.5 pulgadas SATA 3, "
            "diseñada para revitalizar computadoras de escritorio y laptops antiguas "
            "multiplicando la velocidad de inicio y transferencia."
        ),
        "especificaciones": [
            "Capacidad amplia de almacenamiento digital de 1 TB (1000 GB)",
            "Interfaz SATA Rev 3.0 (6 Gb/s) retrocompatible con SATA Rev 2.0",
            "Velocidades secuenciales de lectura de hasta 500 MB/s y escritura de 450 MB/s",
            "Construcción sólida y resistente a golpes, vibraciones y caídas accidentales",
            "Consumo energético reducido que ayuda a preservar la batería en equipos portátiles",
        ],
        "uso_recomendado": (
            "Perfecto para actualizar discos duros mecánicos lentos, almacenar juegos pesados, "
            "bibliotecas multimedia o servir como unidad de respaldo de alto rendimiento."
        ),
    },
}


def slugificar(nombre: str) -> str:
    """Convierte el nombre comercial del producto en un slug limpio para archivo.

    Minúsculas, sin tildes ni diacríticos, y reemplaza caracteres no alfanuméricos
    por guiones bajos ('_').
    """
    descompuesto = unicodedata.normalize("NFD", nombre)
    sin_tildes = "".join(c for c in descompuesto if unicodedata.category(c) != "Mn")
    limpio = re.sub(r"[^a-zA-Z0-9]+", "_", sin_tildes.strip().lower())
    return limpio.strip("_")


def _generar_ficha_corta(nombre: str, categoria: str) -> str:
    """Crea una ficha técnica concisa de 5 a 8 líneas con todas las secciones estándar."""
    descripciones = {
        "smartphones": (
            f"Teléfono móvil de la línea {categoria} que combina rendimiento confiable, "
            "cámara de alta resolución y autonomía balanceada para el uso cotidiano."
        ),
        "laptops": (
            f"Equipo portátil de la categoría {categoria} diseñado para ofrecer productividad, "
            "conectividad versátil y portabilidad en tareas académicas y profesionales."
        ),
        "audio": (
            f"Dispositivo de sonido de alta fidelidad dentro del segmento {categoria}, "
            "equipado con transductores acústicos de precisión y diseño ergonómico."
        ),
        "gaming": (
            f"Periférico o dispositivo optimizado para el ecosistema {categoria}, "
            "desarrollado para brindar tiempos de respuesta ágiles y durabilidad ante uso intenso."
        ),
        "wearables": (
            f"Dispositivo vestible inteligente enfocado en el seguimiento de salud, "
            "registro de actividad deportiva diaria y sincronización con dispositivos móviles."
        ),
        "accesorios": (
            f"Accesorio esencial del catálogo de {categoria} que complementa y expande las "
            "capacidades técnicas, ergonómicas o de almacenamiento de tu entorno digital."
        ),
    }

    desc = descripciones.get(
        categoria,
        f"Artículo de alta calidad perteneciente al catálogo de {categoria} de PixelOrbe."
    )

    return (
        f"# {nombre}\n"
        f"Categoría: {categoria}\n\n"
        "## Descripción\n"
        f"{desc}\n\n"
        "## Especificaciones\n"
        f"- Factor de forma y diseño estándar para {categoria}.\n"
        "- Construcción con materiales de alta resistencia y durabilidad.\n"
        "- Compatibilidad plug-and-play y conectividad universal.\n\n"
        "## Uso recomendado\n"
        "Apto para uso personal, profesional o doméstico según requerimientos del usuario.\n\n"
        "## Garantía referencial\n"
        "Garantía referencial de fábrica según políticas de PixelOrbe. "
        "Para plazos y condiciones detalladas, consulte el documento central garantias.md.\n"
    )


def _generar_ficha_completa(id_prod: int, nombre: str, categoria: str) -> str:
    """Crea una ficha técnica detallada con especificaciones exhaustivas."""
    datos = FICHAS_DETALLADAS[id_prod]
    lista_specs = "\n".join(f"- {s}" for s in datos["especificaciones"])
    return (
        f"# {nombre}\n"
        f"Categoría: {categoria}\n\n"
        "## Descripción\n"
        f"{datos['descripcion']}\n\n"
        "## Especificaciones\n"
        f"{lista_specs}\n\n"
        "## Uso recomendado\n"
        f"{datos['uso_recomendado']}\n\n"
        "## Garantía referencial\n"
        "Garantía referencial de fábrica según políticas de PixelOrbe. "
        "Para plazos y condiciones detalladas, consulte el documento central garantias.md.\n"
    )


def generar_todas_las_fichas() -> list[Path]:
    """Genera las 48 fichas técnicas en data/docs/ y valida que no contengan precio ni stock."""
    DIR_DOCS.mkdir(parents=True, exist_ok=True)
    rutas_generadas: list[Path] = []

    for id_prod, nombre, categoria, _, _ in PRODUCTOS:
        slug = slugificar(nombre)
        archivo = DIR_DOCS / f"ficha_{slug}.md"

        if id_prod in IDS_COMPLETAS:
            contenido = _generar_ficha_completa(id_prod, nombre, categoria)
        else:
            contenido = _generar_ficha_corta(nombre, categoria)

        # Validación constitucional: cero menciones de precio o stock
        contenido_lower = contenido.lower()
        terminos_prohibidos = ["usd", "precio", " stock", "agotado"]
        for prohibido in terminos_prohibidos:
            if prohibido in contenido_lower:
                raise ValueError(
                    f"Fallo de política constitucional en producto {id_prod} ({nombre}): "
                    f"la ficha no puede contener '{prohibido}'."
                )

        archivo.write_text(contenido, encoding="utf-8")
        rutas_generadas.append(archivo)

    return rutas_generadas


if __name__ == "__main__":
    fichas = generar_todas_las_fichas()
    print(f"Se generaron exitosamente {len(fichas)} fichas técnicas en {DIR_DOCS}")
    print(f"- 12 fichas completas detalladas (IDs: {sorted(list(IDS_COMPLETAS))})")
    print(f"- {len(fichas) - len(IDS_COMPLETAS)} fichas concisas estandarizadas")
