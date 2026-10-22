"""Extrae los objetos de una hoja de sala y los escala al tamaño nativo del juego.

Uso:
    python tools/sprites/objetos.py hoja.webp -o public/rooms/objects \
        --nombres door,bookshelf,clock,wallshelf,toybox,armchair,sidetable,pouf
"""

import argparse
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

from fondo import quitar_fondo
from pixelado import cuantizar

AREA_MINIMA = 600
NOMBRES_PRIMERA_HOJA = "bed,bowl,ball,door,rug,plant,shelf"
ANCHO_NATIVO = {
    "bed": 60,
    "bowl": 28,
    "ball": 14,
    "door": 44,
    "rug": 72,
    "plant": 28,
    "shelf": 44,
    "bookshelf": 44,
    "clock": 16,
    "wallshelf": 40,
    "toybox": 40,
    "armchair": 44,
    "sidetable": 24,
    "pouf": 26,
    "lamp": 24,
    "fishtank": 36,
    "desk": 48,
    "guitar": 22,
    "cactus": 24,
    "wardrobe": 40,
    "poster": 26,
    "mirror": 24,
    "backdoor": 43,
    "gate": 56,
    "swing": 100,
    "goal": 60,
    "soccerball": 20,
    "plot_empty": 44,
    "plot_sprout": 44,
    "plot_ripe": 44,
}


def ordenar_piezas(centros: list[tuple[float, float]], alto: int) -> list[int]:
    """Devuelve los índices de las piezas ordenados por fila y luego por columna.

    Las piezas se reparten en dos filas: las de la mitad superior de la hoja
    y las de la inferior.
    """
    return sorted(
        range(len(centros)),
        key=lambda indice: (centros[indice][1] > alto / 2, centros[indice][0]),
    )


def extraer(
    ruta_hoja: Path,
    carpeta_salida: Path,
    nombres: list[str],
    tolerancia: int,
    colores: int,
) -> None:
    """Separa cada objeto, lo reduce a su ancho nativo y lo guarda."""
    sin_fondo = quitar_fondo(Image.open(ruta_hoja), tolerancia, limpiar_halo=False)
    etiquetas, _ = ndimage.label(np.asarray(sin_fondo.getchannel("A")) > 0)

    piezas = []
    for indice, caja in enumerate(ndimage.find_objects(etiquetas), start=1):
        if (etiquetas[caja] == indice).sum() >= AREA_MINIMA:
            piezas.append((caja[1].start, caja[0].start, caja[1].stop, caja[0].stop))

    if len(piezas) != len(nombres):
        raise SystemExit(f"Se esperaban {len(nombres)} objetos y se detectaron {len(piezas)}")

    centros = [((izq + der) / 2, (arr + aba) / 2) for izq, arr, der, aba in piezas]
    carpeta_salida.mkdir(parents=True, exist_ok=True)
    for posicion, indice in enumerate(ordenar_piezas(centros, sin_fondo.height)):
        nombre = nombres[posicion]
        recorte = sin_fondo.crop(piezas[indice])
        escala = ANCHO_NATIVO[nombre] / recorte.width
        tamano = (ANCHO_NATIVO[nombre], max(1, round(recorte.height * escala)))
        reducido = cuantizar(recorte.resize(tamano, Image.BOX), colores)
        reducido.save(carpeta_salida / f"{nombre}.png")
        print(f"{nombre}: {reducido.width}x{reducido.height}")


def main() -> None:
    """Lee los argumentos y extrae los objetos."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("hoja", type=Path)
    parser.add_argument("-o", "--salida", type=Path, required=True)
    parser.add_argument(
        "--nombres",
        default=NOMBRES_PRIMERA_HOJA,
        help="Nombres de los objetos en orden de lectura (fila a fila)",
    )
    parser.add_argument("--tolerancia", type=int, default=70)
    parser.add_argument("--colores", type=int, default=48)
    argumentos = parser.parse_args()
    extraer(
        argumentos.hoja,
        argumentos.salida,
        argumentos.nombres.split(","),
        argumentos.tolerancia,
        argumentos.colores,
    )


if __name__ == "__main__":
    main()
