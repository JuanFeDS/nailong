"""Corta una hoja en cuadrícula, quita el fondo y la guarda como una tira horizontal.

Uso:
    python tools/sprites/cuadricula.py hoja.webp -o public/sprites/processed/knock.png \
        --filas 2 --columnas 4 --ancho-celda 92
"""

import argparse
from pathlib import Path

import numpy as np
from PIL import Image

from fondo import quitar_fondo
from hoja import cuantizar_compartido


def cortar_cuadricula(hoja: Image.Image, filas: int, columnas: int) -> list[Image.Image]:
    """Devuelve las celdas de la cuadrícula en orden de lectura (fila a fila)."""
    ancho, alto = hoja.width // columnas, hoja.height // filas
    return [
        hoja.crop((columna * ancho, fila * alto, (columna + 1) * ancho, (fila + 1) * alto))
        for fila in range(filas)
        for columna in range(columnas)
    ]


def alinear_abajo_derecha(celdas: list[Image.Image]) -> list[Image.Image]:
    """Desplaza cada celda para que su contenido comparta borde inferior y derecho.

    Sirve cuando hay un elemento fijo (una puerta) que debe quedarse quieto
    mientras el resto de la imagen cambia entre frames.
    """
    cajas = [celda.getchannel("A").getbbox() for celda in celdas]
    derecha = max(caja[2] for caja in cajas)
    abajo = max(caja[3] for caja in cajas)
    alineadas = []
    for celda, caja in zip(celdas, cajas):
        nueva = Image.new("RGBA", celda.size, (0, 0, 0, 0))
        nueva.paste(celda, (derecha - caja[2], abajo - caja[3]))
        alineadas.append(nueva)
    return alineadas


def alinear_pies(celdas: list[Image.Image]) -> list[Image.Image]:
    """Centra los pies de cada celda y apoya todos los frames en el mismo suelo.

    Los pies son la franja inferior del contenido: centrarlos evita que el
    personaje se desplace al mover brazos o cabeza. Se recorta el vacío bajo
    los pies, para que el suelo coincida con el borde inferior de la celda.
    """
    cajas = [celda.getchannel("A").getbbox() for celda in celdas]
    suelo = max(caja[3] for caja in cajas)
    alineadas = []
    for celda, caja in zip(celdas, cajas):
        alto_pies = max(1, (caja[3] - caja[1]) // 6)
        franja = np.asarray(celda.getchannel("A"))[caja[3] - alto_pies : caja[3]] > 0
        columnas = np.nonzero(franja.any(axis=0))[0]
        centro_pies = (columnas.min() + columnas.max()) / 2
        nueva = Image.new("RGBA", celda.size, (0, 0, 0, 0))
        nueva.paste(celda, (round(celda.width / 2 - centro_pies), suelo - caja[3]))
        alineadas.append(nueva.crop((0, 0, celda.width, suelo)))
    return alineadas


def main() -> None:
    """Procesa la hoja y guarda la tira de frames."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("hoja", type=Path)
    parser.add_argument("-o", "--salida", type=Path, required=True)
    parser.add_argument("--filas", type=int, default=1)
    parser.add_argument("--columnas", type=int, default=4)
    parser.add_argument("--ancho-celda", type=int, required=True, help="Ancho nativo de cada frame")
    parser.add_argument("--tolerancia", type=int, default=70)
    parser.add_argument("--colores", type=int, default=48)
    parser.add_argument(
        "--alinear",
        choices=["derecha", "pies"],
        help="derecha: borde inferior y derecho (objeto fijo); pies: centra los pies (personaje)",
    )
    argumentos = parser.parse_args()

    sin_fondo = quitar_fondo(Image.open(argumentos.hoja), argumentos.tolerancia)
    celdas = cortar_cuadricula(sin_fondo, argumentos.filas, argumentos.columnas)
    if argumentos.alinear == "derecha":
        celdas = alinear_abajo_derecha(celdas)
    elif argumentos.alinear == "pies":
        celdas = alinear_pies(celdas)
    escala = argumentos.ancho_celda / celdas[0].width
    tamano = (argumentos.ancho_celda, round(celdas[0].height * escala))
    reducidas = cuantizar_compartido(
        [celda.resize(tamano, Image.BOX) for celda in celdas], argumentos.colores
    )

    tira = Image.new("RGBA", (tamano[0] * len(reducidas), tamano[1]))
    for indice, celda in enumerate(reducidas):
        tira.paste(celda, (indice * tamano[0], 0))
    argumentos.salida.parent.mkdir(parents=True, exist_ok=True)
    tira.save(argumentos.salida)
    print(f"{len(reducidas)} frames de {tamano[0]}x{tamano[1]} -> {tira.width}x{tira.height}")


if __name__ == "__main__":
    main()
