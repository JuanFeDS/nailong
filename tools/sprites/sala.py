"""Convierte el fondo de una sala generado con IA a la resolución nativa del juego.

Uso:
    python tools/sprites/sala.py fondo.webp -o public/rooms/room_a.png
"""

import argparse
from pathlib import Path

from PIL import Image

from pixelado import cuantizar

ANCHO_NATIVO = 320
ALTO_NATIVO = 180


def procesar_sala(ruta_entrada: Path, cantidad_colores: int) -> Image.Image:
    """Reduce el fondo a 320x180 promediando bloques y limita la paleta.

    Se promedia (BOX) en lugar de muestrear porque el fondo generado tiene
    textura fina: muestrear daría ruido, promediar da áreas planas.
    """
    imagen = Image.open(ruta_entrada).convert("RGB")
    reducida = imagen.resize((ANCHO_NATIVO, ALTO_NATIVO), Image.BOX).convert("RGBA")
    return cuantizar(reducida, cantidad_colores)


def borrar_zona(sala: Image.Image, caja: tuple[int, int, int, int], origen_x: int) -> Image.Image:
    """Tapa una zona copiando un trozo de pared vacía situado a la misma altura."""
    izquierda, arriba, derecha, abajo = caja
    ancho = derecha - izquierda
    parche = sala.crop((origen_x, arriba, origen_x + ancho, abajo))
    resultado = sala.copy()
    resultado.paste(parche, (izquierda, arriba))
    return resultado


def main() -> None:
    """Lee los argumentos, procesa el fondo y guarda el resultado."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("entrada", type=Path)
    parser.add_argument("-o", "--salida", type=Path, required=True)
    parser.add_argument("--colores", type=int, default=32)
    parser.add_argument(
        "--borrar", type=int, nargs=4, metavar=("X0", "Y0", "X1", "Y1"),
        help="Zona nativa a tapar con pared (por ejemplo una ventana fija)",
    )
    parser.add_argument("--desde-x", type=int, default=200, help="X de la pared vacía a copiar")
    argumentos = parser.parse_args()

    argumentos.salida.parent.mkdir(parents=True, exist_ok=True)
    sala = procesar_sala(argumentos.entrada, argumentos.colores)
    if argumentos.borrar:
        sala = borrar_zona(sala, tuple(argumentos.borrar), argumentos.desde_x)
    sala.save(argumentos.salida)
    print(f"{argumentos.entrada.name} -> {sala.width}x{sala.height}")


if __name__ == "__main__":
    main()
