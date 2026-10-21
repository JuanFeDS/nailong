"""Recorta las ventanas de una hoja y las deja con fondo transparente a escala nativa.

Uso:
    python tools/sprites/ventanas.py hoja.webp -o public/rooms/windows
"""

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

from pixelado import cuantizar

NOMBRES = [
    "night", "dawn", "day", "sunset",
    "winter", "spring", "summer", "autumn",
    "rain", "fog", "storm", "aurora",
]
COLUMNAS = 4
COLOR_MARCADOR = (255, 0, 255)
MARGEN = 3


def localizar_ventanas(hoja: Image.Image, tolerancia: int) -> list[tuple[int, int, int, int]]:
    """Devuelve la caja de cada ventana, ordenadas por filas de izquierda a derecha."""
    pixeles = np.asarray(hoja.convert("RGB")).astype(int)
    alto, ancho = pixeles.shape[:2]
    color_pared = np.median(pixeles[alto // 3 : alto // 3 + 20, ancho // 2 - 10 : ancho // 2 + 10], axis=(0, 1))
    distancia = np.abs(pixeles - color_pared).sum(axis=-1)
    mascara = ndimage.binary_closing(distancia > tolerancia, iterations=6)
    etiquetas, _ = ndimage.label(mascara)
    cajas = [
        (caja[1].start, caja[0].start, caja[1].stop, caja[0].stop)
        for caja in ndimage.find_objects(etiquetas)
        if ancho * 0.08 < (caja[1].stop - caja[1].start) < ancho * 0.25
        and (caja[0].stop - caja[0].start) > alto * 0.08
    ]
    cajas.sort(key=lambda caja: ((caja[1] + caja[3]) // 2 // (alto // 3 + 1), caja[0]))
    return cajas


def recortar_sin_pared(hoja: Image.Image, caja: tuple[int, int, int, int], tolerancia: int) -> Image.Image:
    """Recorta una ventana y hace transparente la pared que la rodea."""
    izquierda, arriba, derecha, abajo = caja
    recorte = hoja.convert("RGB").crop(
        (izquierda - MARGEN, arriba - MARGEN, derecha + MARGEN, abajo + MARGEN)
    )
    relleno = recorte.copy()
    ancho, alto = relleno.size
    for esquina in ((0, 0), (ancho - 1, 0), (0, alto - 1), (ancho - 1, alto - 1)):
        ImageDraw.floodfill(relleno, esquina, COLOR_MARCADOR, thresh=tolerancia)
    resultado = np.array(recorte.convert("RGBA"))
    resultado[np.all(np.array(relleno) == COLOR_MARCADOR, axis=-1)] = (0, 0, 0, 0)
    return Image.fromarray(resultado)


def main() -> None:
    """Extrae, reduce y guarda cada ventana con su nombre."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("hoja", type=Path)
    parser.add_argument("-o", "--salida", type=Path, required=True)
    parser.add_argument("--ancho", type=int, default=58, help="Ancho nativo final de la ventana")
    parser.add_argument("--tolerancia", type=int, default=60)
    parser.add_argument("--colores", type=int, default=32)
    argumentos = parser.parse_args()

    hoja = Image.open(argumentos.hoja)
    cajas = localizar_ventanas(hoja, argumentos.tolerancia)
    if len(cajas) != len(NOMBRES):
        raise SystemExit(f"Se esperaban {len(NOMBRES)} ventanas y se detectaron {len(cajas)}")

    argumentos.salida.mkdir(parents=True, exist_ok=True)
    escala = argumentos.ancho / (cajas[0][2] - cajas[0][0] + 2 * MARGEN)
    for nombre, caja in zip(NOMBRES, cajas):
        ventana = recortar_sin_pared(hoja, caja, argumentos.tolerancia)
        nueva_forma = (round(ventana.width * escala), round(ventana.height * escala))
        reducida = cuantizar(ventana.resize(nueva_forma, Image.BOX), argumentos.colores)
        reducida.save(argumentos.salida / f"{nombre}.png")
        print(f"{nombre}: {reducida.width}x{reducida.height}")


if __name__ == "__main__":
    main()
