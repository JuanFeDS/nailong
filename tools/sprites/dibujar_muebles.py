"""Dibuja en código los muebles nuevos de la tienda y los guarda como sprites.

Uso:
    python tools/sprites/dibujar_muebles.py -o public/rooms/objects
    python tools/sprites/dibujar_muebles.py -o public/rooms/objects --lamina vista.png
"""

import argparse
from pathlib import Path

from PIL import Image

import muebles_patio
import muebles_sala

AMPLIACION_LAMINA = 5
SEPARACION_LAMINA = 8
FONDO_LAMINA = (60, 70, 90, 255)


def armar_lamina(sprites: dict[str, Image.Image]) -> Image.Image:
    """Pone todos los sprites en fila, ampliados, para revisarlos de un vistazo."""
    ancho = sum(sprite.width for sprite in sprites.values()) + SEPARACION_LAMINA * (len(sprites) + 1)
    alto = max(sprite.height for sprite in sprites.values()) + SEPARACION_LAMINA * 2
    lamina = Image.new("RGBA", (ancho, alto), FONDO_LAMINA)
    posicion_x = SEPARACION_LAMINA
    for sprite in sprites.values():
        lamina.alpha_composite(sprite, (posicion_x, alto - SEPARACION_LAMINA - sprite.height))
        posicion_x += sprite.width + SEPARACION_LAMINA
    return lamina.resize((ancho * AMPLIACION_LAMINA, alto * AMPLIACION_LAMINA), Image.NEAREST)


def main():
    """Genera los sprites y, si se pide, una lámina de revisión."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-o", "--salida", type=Path, required=True)
    parser.add_argument("--lamina", type=Path)
    argumentos = parser.parse_args()

    sprites = {nombre: dibujar() for nombre, dibujar in {**muebles_sala.OBJETOS, **muebles_patio.OBJETOS}.items()}
    argumentos.salida.mkdir(parents=True, exist_ok=True)
    for nombre, sprite in sprites.items():
        sprite.save(argumentos.salida / f"{nombre}.png")
    if argumentos.lamina:
        armar_lamina(sprites).save(argumentos.lamina)


if __name__ == "__main__":
    main()
