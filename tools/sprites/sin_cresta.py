"""Quita la crestita oscura de la cabeza de cada frame de una tira de sprites.

La cresta son unos píxeles marrón-anaranjados que sobresalen en lo alto de la
cabeza. Se borra el saliente, se repinta la raya interior con el amarillo de
la cabeza y se rehace el borde naranja de la nueva cima.

Uso:
    python tools/sprites/sin_cresta.py public/sprites/processed/play.png --frames 8
"""

import argparse
from pathlib import Path

import numpy as np
from PIL import Image

MITAD_VENTANA = 6
FILAS_SALIENTES = 2
FILAS_VENTANA = 7
VERDE_OSCURO = 150
VERDE_AMARILLO = 185


def mediana_color(pixeles: np.ndarray) -> np.ndarray:
    """Devuelve el color mediano de una lista de píxeles RGBA."""
    return np.median(pixeles.reshape(-1, 4), axis=0).astype(np.uint8)


def quitar_cresta_frame(frame: np.ndarray) -> np.ndarray:
    """Borra la cresta de un frame RGBA y devuelve el resultado."""
    alto, ancho = frame.shape[:2]
    filas, columnas = np.nonzero(frame[..., 3] > 0)
    cima = filas.min()
    centro = int(columnas[filas == cima].mean())
    izquierda, derecha = max(0, centro - MITAD_VENTANA), min(ancho, centro + MITAD_VENTANA + 1)
    fin = min(alto, cima + FILAS_VENTANA)

    ventana = frame[cima:fin, izquierda:derecha]
    verde = ventana[..., 1].astype(int)
    oscuros = (verde < VERDE_OSCURO) & (ventana[..., 3] > 0)
    if not oscuros.any():
        return frame

    cuerpo = frame[fin : fin + 4, izquierda:derecha]
    amarillos = cuerpo[(cuerpo[..., 1] >= VERDE_AMARILLO) & (cuerpo[..., 3] > 0)]
    naranjas = ventana[(verde >= VERDE_OSCURO) & (verde < VERDE_AMARILLO) & (ventana[..., 3] > 0)]
    if len(amarillos) == 0 or len(naranjas) == 0:
        return frame
    amarillo, naranja = mediana_color(amarillos), mediana_color(naranjas)

    resultado = frame.copy()
    for fila, columna in zip(*np.nonzero(oscuros)):
        if fila < FILAS_SALIENTES:
            resultado[cima + fila, izquierda + columna] = (0, 0, 0, 0)
        else:
            resultado[cima + fila, izquierda + columna] = amarillo

    for columna in range(izquierda, derecha):
        opacos = np.nonzero(resultado[cima : fin + 1, columna, 3] > 0)[0]
        if len(opacos) == 0:
            continue
        borde = cima + opacos[0]
        if resultado[borde, columna, 1] >= VERDE_AMARILLO:
            resultado[borde, columna] = naranja
    return resultado


def main() -> None:
    """Lee la tira, limpia cada frame y la guarda en el mismo archivo."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tira", type=Path)
    parser.add_argument("--frames", type=int, required=True)
    argumentos = parser.parse_args()

    tira = np.array(Image.open(argumentos.tira).convert("RGBA"))
    ancho_frame = tira.shape[1] // argumentos.frames
    for indice in range(argumentos.frames):
        inicio = indice * ancho_frame
        tira[:, inicio : inicio + ancho_frame] = quitar_cresta_frame(
            tira[:, inicio : inicio + ancho_frame]
        )
    Image.fromarray(tira).save(argumentos.tira)
    print(f"{argumentos.frames} frames limpiados en {argumentos.tira}")


if __name__ == "__main__":
    main()
