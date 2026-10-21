"""Reduce la cabeza de cada frame de una tira de sprites sin encoger el cuerpo.

Corta cada frame justo debajo de la barbilla (donde empieza la panza crema),
reduce la parte de arriba (la cabeza) con vecino más cercano y la vuelve a
apoyar sobre el cuerpo, anclada al centro de la barbilla.

Uso:
    python tools/sprites/achicar_cabeza.py entrada.png salida.png --frames 8 --escala 0.82
"""

import argparse
from pathlib import Path

import numpy as np
from PIL import Image

MINIMO_PIXELES_PANZA = 3
FRACCION_RESPALDO = 0.55


def es_panza(pixeles: np.ndarray) -> np.ndarray:
    """Marca los píxeles del color crema de la panza."""
    return (pixeles[..., 0] > 235) & (pixeles[..., 1] > 205) & (pixeles[..., 2] > 140) & (pixeles[..., 3] > 0)


def fila_de_barbilla(frame: np.ndarray) -> int:
    """Devuelve la fila donde acaba la cabeza: la primera con panza visible."""
    filas, _ = np.nonzero(frame[..., 3] > 0)
    cima, base = filas.min(), filas.max()
    panza = es_panza(frame)
    for fila in range(cima, base):
        if panza[fila].sum() >= MINIMO_PIXELES_PANZA:
            return fila
    return cima + int((base - cima) * FRACCION_RESPALDO)


def achicar_frame(frame: np.ndarray, escala: float) -> np.ndarray:
    """Reduce la parte superior (cabeza) de un frame RGBA."""
    corte = fila_de_barbilla(frame)
    cabeza = frame[:corte]
    filas, columnas = np.nonzero(cabeza[..., 3] > 0)
    if len(filas) == 0:
        return frame
    cima = filas.min()
    recorte = Image.fromarray(cabeza[cima:])
    ancla_x = (columnas.min() + columnas.max()) / 2

    nuevo_ancho = max(1, round(recorte.width * escala))
    nuevo_alto = max(1, round(recorte.height * escala))
    reducida = recorte.resize((nuevo_ancho, nuevo_alto), Image.NEAREST)

    resultado = np.zeros_like(frame)
    resultado[corte:] = frame[corte:]
    izquierda = round(ancla_x - nuevo_ancho / 2)
    arriba = corte - nuevo_alto
    capa = Image.fromarray(resultado)
    capa.alpha_composite(reducida, (max(0, izquierda), max(0, arriba)))
    return np.array(capa)


def main() -> None:
    """Procesa la tira frame a frame y guarda el resultado."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("entrada", type=Path)
    parser.add_argument("salida", type=Path)
    parser.add_argument("--frames", type=int, required=True)
    parser.add_argument("--escala", type=float, default=0.82)
    argumentos = parser.parse_args()

    tira = np.array(Image.open(argumentos.entrada).convert("RGBA"))
    ancho = tira.shape[1] // argumentos.frames
    for indice in range(argumentos.frames):
        inicio = indice * ancho
        tira[:, inicio : inicio + ancho] = achicar_frame(tira[:, inicio : inicio + ancho], argumentos.escala)
    Image.fromarray(tira).save(argumentos.salida)
    print(f"{argumentos.frames} frames -> {argumentos.salida}")


if __name__ == "__main__":
    main()
