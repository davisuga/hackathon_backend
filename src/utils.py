import tempfile
from typing import Union

async def save_media_bytes_to_temp(media: bytes, suffix: str = ".bin") -> str:
    """
    Guarda bytes en un archivo temporal y retorna el path.

    :param media: contenido binario
    :param suffix: sufijo/extension del archivo (ejemplo: .jpg, .mp4, .pdf)
    :return: ruta del archivo temporal
    """
    # Crear archivo temporal persistente
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    path = temp_file.name

    with open(path, "wb") as f:
        f.write(media)

    return path


COLORS = {
    # Básicos
    "negro": "#000000",
    "blanco": "#FFFFFF",
    "gris": "#9E9E9E",

    # Material Design 500
    "rojo": "#F44336",
    "rosa": "#E91E63",
    "purpura": "#9C27B0",
    "violeta": "#673AB7",
    "indigo": "#3F51B5",
    "azul": "#2196F3",
    "celeste": "#03A9F4",
    "cian": "#00BCD4",
    "teal": "#009688",
    "verde": "#4CAF50",
    "verde_claro": "#8BC34A",
    "lima": "#CDDC39",
    "amarillo": "#FFEB3B",
    "ambar": "#FFC107",
    "naranja": "#FF9800",
    "naranja_profundo": "#FF5722",
    "cafe": "#795548",
    "azul_grisaceo": "#607D8B",
}

def color_a_hex(nombre: str) -> str:
    """
    Convierte un nombre de color a su valor hexadecimal.
    Si no existe, levanta KeyError con los nombres válidos.

    :param str nombre: uno de los colores conocidos negro, blanco, 
    gris, rojo, rosa, purpura, violeta, indigo,
    azul, celeste, cian, teal, verde, verde_claro, lima, amarillo,
    ambar, naranja, naranja_profundo, cafe, azul_grisaceo.
    """
    nombre = nombre.strip().lower()
    if nombre not in COLORS:
        raise KeyError(
            f"Color '{nombre}' no está definido. Colores válidos: {list(COLORS.keys())}"
        )
    return COLORS[nombre]
