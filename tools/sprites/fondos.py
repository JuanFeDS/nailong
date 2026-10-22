"""Separa el fondo de la sala en pared y suelo y genera variantes de color.

Uso:
    python tools/sprites/fondos.py public/rooms/room_a.png -o public/rooms
"""

import argparse
from pathlib import Path

import numpy as np
from PIL import Image

LIMITE_PARED = 74
CUADRO = (131, 18, 160, 42)
DESPLAZAMIENTO_PARCHE = 60
MARGEN_PARCHE = 2
MATIZ_PARED_ORIGINAL = 237

PAREDES = {
    "blue": {"matiz": None, "saturacion": 1.0, "brillo": 1.0},
    "green": {"matiz": 140, "saturacion": 0.9, "brillo": 1.0},
    "rose": {"matiz": 350, "saturacion": 1.0, "brillo": 1.05},
    "cream": {"matiz": 42, "saturacion": 0.5, "brillo": 1.55},
    "gray": {"matiz": None, "saturacion": 0.08, "brillo": 1.1},
}
SUELOS = {
    "wood": {"matiz": None, "saturacion": 1.0, "brillo": 1.0},
    "dark": {"matiz": None, "saturacion": 0.9, "brillo": 0.6},
    "light": {"matiz": None, "saturacion": 0.65, "brillo": 1.3},
    "gray": {"matiz": None, "saturacion": 0.1, "brillo": 0.95},
}


def recolorear(imagen: Image.Image, ajuste: dict) -> Image.Image:
    """Aplica un cambio de matiz, saturación y brillo conservando el alfa."""
    alfa = imagen.getchannel("A")
    hsv = np.array(imagen.convert("RGB").convert("HSV")).astype(float)
    if ajuste["matiz"] is not None:
        desplazamiento = (ajuste["matiz"] - MATIZ_PARED_ORIGINAL) * 256 / 360
        hsv[..., 0] = (hsv[..., 0] + desplazamiento) % 256
    hsv[..., 1] = np.clip(hsv[..., 1] * ajuste["saturacion"], 0, 255)
    hsv[..., 2] = np.clip(hsv[..., 2] * ajuste["brillo"], 0, 255)
    resultado = Image.fromarray(hsv.astype(np.uint8), "HSV").convert("RGB").convert("RGBA")
    resultado.putalpha(alfa)
    return resultado


def quitar_cuadro(pared: Image.Image) -> tuple[Image.Image, Image.Image]:
    """Devuelve la pared sin el cuadro y el cuadro recortado como objeto."""
    izquierda, arriba, derecha, abajo = CUADRO
    cuadro = pared.crop(CUADRO)
    limpia = pared.copy()
    zona = (
        izquierda - MARGEN_PARCHE,
        arriba - MARGEN_PARCHE,
        derecha + MARGEN_PARCHE,
        abajo + MARGEN_PARCHE,
    )
    parche = pared.crop(
        (zona[0] - DESPLAZAMIENTO_PARCHE, zona[1], zona[2] - DESPLAZAMIENTO_PARCHE, zona[3])
    )
    limpia.paste(parche, zona[:2])
    return limpia, cuadro


def generar(ruta_fondo: Path, carpeta_salida: Path) -> None:
    """Escribe las paredes, los suelos y el cuadro en la carpeta de salida."""
    fondo = Image.open(ruta_fondo).convert("RGBA")
    pared = fondo.crop((0, 0, fondo.width, LIMITE_PARED))
    suelo = fondo.crop((0, LIMITE_PARED, fondo.width, fondo.height))
    pared, cuadro = quitar_cuadro(pared)

    for nombre, carpeta, base, variantes in (
        ("pared", "walls", pared, PAREDES),
        ("suelo", "floors", suelo, SUELOS),
    ):
        destino = carpeta_salida / carpeta
        destino.mkdir(parents=True, exist_ok=True)
        for identificador, ajuste in variantes.items():
            recolorear(base, ajuste).save(destino / f"{identificador}.png")
        print(f"{nombre}: {len(variantes)} variantes en {destino}")

    objetos = carpeta_salida / "objects"
    objetos.mkdir(parents=True, exist_ok=True)
    cuadro.save(objetos / "frame.png")
    print(f"cuadro: {cuadro.size} en {objetos / 'frame.png'}")


def main() -> None:
    """Lee los argumentos de línea de comandos y genera los fondos."""
    analizador = argparse.ArgumentParser(description=__doc__)
    analizador.add_argument("fondo", type=Path)
    analizador.add_argument("-o", "--salida", type=Path, required=True)
    argumentos = analizador.parse_args()
    generar(argumentos.fondo, argumentos.salida)


if __name__ == "__main__":
    main()
