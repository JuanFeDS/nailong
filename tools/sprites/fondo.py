"""Eliminación del fondo sólido de un sprite."""

import numpy as np
from PIL import Image
from scipy import ndimage

BORDE_HALO = 2


def quitar_fondo(
    imagen: Image.Image, tolerancia: int = 40, limpiar_halo: bool = True
) -> Image.Image:
    """Hace transparente el fondo conectado a los bordes de la imagen.

    El color de fondo se toma de las esquinas. Solo se elimina el fondo
    alcanzable desde los bordes, así que los píxeles oscuros dentro del
    personaje (contornos, ojos) se conservan. La limpieza de halo magenta
    se desactiva para objetos rojos o rosados.
    """
    pixeles = np.array(imagen.convert("RGBA"))
    rgb = pixeles[..., :3].astype(int)
    esquinas = np.array([rgb[0, 0], rgb[0, -1], rgb[-1, 0], rgb[-1, -1]])
    color_fondo = np.median(esquinas, axis=0)

    parecido_al_fondo = np.abs(rgb - color_fondo).sum(axis=-1) <= tolerancia
    etiquetas, _ = ndimage.label(parecido_al_fondo)
    en_borde = np.unique(
        np.concatenate(
            [etiquetas[0], etiquetas[-1], etiquetas[:, 0], etiquetas[:, -1]]
        )
    )
    es_fondo = np.isin(etiquetas, en_borde[en_borde > 0])
    pixeles[es_fondo] = (0, 0, 0, 0)
    return Image.fromarray(quitar_halo(pixeles) if limpiar_halo else pixeles)


def quitar_halo(pixeles: np.ndarray) -> np.ndarray:
    """Borra los píxeles de borde teñidos de magenta por el antialiasing.

    Se distinguen del rosa de las mejillas porque tienen muy poco verde. Solo
    se borran los píxeles pegados al exterior, para no vaciar zonas internas
    del mismo color, como el interior de una boca abierta.
    """
    rojo, verde, azul = pixeles[..., 0], pixeles[..., 1], pixeles[..., 2]
    parece_halo = (rojo > 150) & (verde < 120) & (azul >= 70)
    transparente = pixeles[..., 3] == 0
    junto_al_exterior = ndimage.binary_dilation(transparente, iterations=BORDE_HALO) & ~transparente
    pixeles[parece_halo & junto_al_exterior] = (0, 0, 0, 0)
    return pixeles
