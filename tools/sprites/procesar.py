"""Convierte imágenes de Nailong generadas con IA en sprites listos para el juego.

Uso:
    python tools/sprites/procesar.py public/sprites/hello.png -o public/sprites/processed
"""

import argparse
from pathlib import Path

from PIL import Image

from fondo import quitar_fondo
from hoja import alinear_frames, cuantizar_compartido, dividir_en_frames
from lienzo import anclar_en_celda
from pixelado import cuantizar, recortar_contenido, reducir

ESCALA_VISTA_PREVIA = 8


def procesar_imagen(
    ruta_entrada: Path,
    alto_objetivo: int,
    lado_celda: int,
    cantidad_colores: int,
    tolerancia: int,
) -> Image.Image:
    """Aplica el pipeline completo a una imagen y devuelve la celda final."""
    imagen = Image.open(ruta_entrada)
    sin_fondo = quitar_fondo(imagen, tolerancia)
    recortada = recortar_contenido(sin_fondo)
    pequena = reducir(recortada, alto_objetivo)
    return anclar_en_celda(cuantizar(pequena, cantidad_colores), lado_celda)


def procesar_hoja(
    ruta_entrada: Path,
    cantidad_frames: int,
    alto_objetivo: int,
    lado_celda: int,
    cantidad_colores: int,
    tolerancia: int,
) -> Image.Image:
    """Procesa una hoja horizontal y devuelve una tira de celdas alineadas."""
    sin_fondo = quitar_fondo(Image.open(ruta_entrada), tolerancia)
    frames = dividir_en_frames(sin_fondo, cantidad_frames)
    celdas = cuantizar_compartido(
        alinear_frames(frames, alto_objetivo, lado_celda), cantidad_colores
    )
    tira = Image.new("RGBA", (lado_celda * len(celdas), lado_celda))
    for indice, celda in enumerate(celdas):
        tira.paste(celda, (indice * lado_celda, 0))
    return tira


def leer_argumentos() -> argparse.Namespace:
    """Define y lee los argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("entradas", nargs="+", type=Path, help="Imágenes a procesar")
    parser.add_argument("-o", "--salida", type=Path, required=True, help="Carpeta de salida")
    parser.add_argument("--alto", type=int, default=56, help="Alto del personaje en píxeles")
    parser.add_argument("--celda", type=int, default=64, help="Lado de la celda cuadrada")
    parser.add_argument("--colores", type=int, default=32, help="Tamaño máximo de la paleta")
    parser.add_argument("--tolerancia", type=int, default=40, help="Tolerancia del fondo")
    parser.add_argument(
        "--frames", type=int, default=1, help="Frames de la hoja horizontal (1 = imagen suelta)"
    )
    return parser.parse_args()


def main() -> None:
    """Procesa cada imagen y guarda el sprite y una vista previa ampliada."""
    argumentos = leer_argumentos()
    argumentos.salida.mkdir(parents=True, exist_ok=True)

    for ruta_entrada in argumentos.entradas:
        if argumentos.frames > 1:
            celda = procesar_hoja(
                ruta_entrada,
                argumentos.frames,
                argumentos.alto,
                argumentos.celda,
                argumentos.colores,
                argumentos.tolerancia,
            )
        else:
            celda = procesar_imagen(
                ruta_entrada,
                argumentos.alto,
                argumentos.celda,
                argumentos.colores,
                argumentos.tolerancia,
            )
        celda.save(argumentos.salida / f"{ruta_entrada.stem}.png")
        vista_previa = celda.resize(
            (celda.width * ESCALA_VISTA_PREVIA, celda.height * ESCALA_VISTA_PREVIA),
            Image.NEAREST,
        )
        vista_previa.save(argumentos.salida / f"{ruta_entrada.stem}_preview.png")
        print(f"{ruta_entrada.name} -> {celda.size[0]}x{celda.size[1]}")


if __name__ == "__main__":
    main()
