"""Extrae las piezas sueltas de una hoja de partes para animación por rig.

Uso:
    python tools/sprites/partes.py hoja_partes.webp -o public/sprites/processed/parts
"""

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

from fondo import quitar_fondo
from pixelado import cuantizar

AREA_MINIMA = 800


def nombrar_piezas(centros: list[tuple[float, float]], ancho: int, alto: int) -> list[str]:
    """Asigna un nombre a cada pieza según su posición relativa en la hoja.

    Distribución esperada: cabeza arriba a la izquierda, torso debajo, cuatro
    piezas de brazos a la derecha (cercano antes que lejano) y dos piernas abajo.
    """
    nombres = [""] * len(centros)
    brazos, piernas = [], []
    for indice, (centro_x, centro_y) in enumerate(centros):
        relativo_x, relativo_y = centro_x / ancho, centro_y / alto
        if relativo_x < 0.45 and relativo_y < 0.35:
            nombres[indice] = "head"
        elif relativo_x < 0.45:
            nombres[indice] = "torso"
        elif relativo_y < 0.6:
            brazos.append((centro_x, indice))
        else:
            piernas.append((centro_x, indice))

    for orden, (_, indice) in enumerate(sorted(brazos)):
        nombres[indice] = ["arm_near", "forearm_near", "arm_far", "forearm_far"][orden]
    for orden, (_, indice) in enumerate(sorted(piernas)):
        nombres[indice] = ["leg_near", "leg_far"][orden]
    return nombres


def extraer(
    ruta_hoja: Path, carpeta_salida: Path, escala: float, tolerancia: int, colores: int
) -> None:
    """Separa, escala y guarda cada pieza; escribe parts.json con sus tamaños."""
    sin_fondo = quitar_fondo(Image.open(ruta_hoja), tolerancia)
    mascara = np.asarray(sin_fondo.getchannel("A")) > 0
    etiquetas, cantidad = ndimage.label(mascara)
    cajas = ndimage.find_objects(etiquetas)

    piezas = []
    for indice, caja in enumerate(cajas, start=1):
        if (etiquetas[caja] == indice).sum() < AREA_MINIMA:
            continue
        recorte = sin_fondo.crop((caja[1].start, caja[0].start, caja[1].stop, caja[0].stop))
        centro = ((caja[1].start + caja[1].stop) / 2, (caja[0].start + caja[0].stop) / 2)
        piezas.append((recorte, centro))

    nombres = nombrar_piezas([centro for _, centro in piezas], *sin_fondo.size)
    carpeta_salida.mkdir(parents=True, exist_ok=True)
    medidas = {}
    for (recorte, _), nombre in zip(piezas, nombres):
        reducida = recorte.resize(
            (max(1, round(recorte.width * escala)), max(1, round(recorte.height * escala))),
            Image.NEAREST,
        )
        reducida = cuantizar(reducida, colores)
        reducida.save(carpeta_salida / f"{nombre}.png")
        medidas[nombre] = {"width": reducida.width, "height": reducida.height}
        print(f"{nombre}: {reducida.width}x{reducida.height}")

    (carpeta_salida / "parts.json").write_text(json.dumps(medidas, indent=2), encoding="utf-8")


def main() -> None:
    """Lee los argumentos y extrae las piezas."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("hoja", type=Path)
    parser.add_argument("-o", "--salida", type=Path, required=True)
    parser.add_argument("--escala", type=float, default=0.17)
    parser.add_argument("--tolerancia", type=int, default=70)
    parser.add_argument("--colores", type=int, default=32)
    argumentos = parser.parse_args()
    extraer(argumentos.hoja, argumentos.salida, argumentos.escala, argumentos.tolerancia, argumentos.colores)


if __name__ == "__main__":
    main()
