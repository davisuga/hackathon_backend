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
