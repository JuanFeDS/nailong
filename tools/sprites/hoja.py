"""Procesado de hojas de sprites: varios frames en una tira horizontal."""

import numpy as np
from PIL import Image

from pixelado import cuantizar


def dividir_en_frames(hoja: Image.Image, cantidad_frames: int) -> list[Image.Image]:
    """Corta la hoja en columnas de igual ancho."""
    ancho_frame = hoja.width // cantidad_frames
    return [
        hoja.crop((indice * ancho_frame, 0, (indice + 1) * ancho_frame, hoja.height))
        for indice in range(cantidad_frames)
    ]


def _centro_horizontal(frame: Image.Image) -> float:
    """Calcula el centro de masa horizontal de los píxeles opacos."""
    opacos_por_columna = (np.asarray(frame.getchannel("A")) > 0).sum(axis=0)
    posiciones = np.arange(frame.width)
    return float((opacos_por_columna * posiciones).sum() / opacos_por_columna.sum())


def alinear_frames(
    frames: list[Image.Image], alto_objetivo: int, lado_celda: int
) -> list[Image.Image]:
    """Reduce todos los frames con la misma escala y los alinea en celdas.

    La escala se calcula con el frame más alto, así el personaje no cambia de
    tamaño entre frames. Horizontalmente se centra por masa y verticalmente se
    conserva el desnivel original entre frames, para mantener el rebote del paso.
    """
    cajas = [frame.getchannel("A").getbbox() for frame in frames]
    alto_maximo = max(caja[3] - caja[1] for caja in cajas)
    suelo_global = max(caja[3] for caja in cajas)
    escala = alto_objetivo / alto_maximo
    desfase_y = lado_celda - round(suelo_global * escala)

    celdas = []
    for frame in frames:
        reducido = frame.resize(
            (round(frame.width * escala), round(frame.height * escala)), Image.NEAREST
        )
        desfase_x = round(lado_celda / 2 - _centro_horizontal(frame) * escala)
        celda = Image.new("RGBA", (lado_celda, lado_celda), (0, 0, 0, 0))
        celda.paste(reducido, (desfase_x, desfase_y))
        celdas.append(celda)
    return celdas


def cuantizar_compartido(
    celdas: list[Image.Image], cantidad_colores: int
) -> list[Image.Image]:
    """Cuantiza todos los frames con una única paleta para que no cambien de tono."""
    lado = celdas[0].width
    tira = Image.new("RGBA", (lado * len(celdas), celdas[0].height))
    for indice, celda in enumerate(celdas):
        tira.paste(celda, (indice * lado, 0))
    tira = cuantizar(tira, cantidad_colores)
    return [
        tira.crop((indice * lado, 0, (indice + 1) * lado, tira.height))
        for indice in range(len(celdas))
    ]
