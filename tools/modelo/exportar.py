"""Exporta las hojas de sprites que usa el juego a partir del modelo 3D.

Uso:
    .venv/bin/python tools/modelo/exportar.py [hoja ...]

Sin argumentos exporta todas las hojas; con nombres, solo esas.

Escribe cada hoja en public/sprites/nailong/ y un índice en
src/lib/nailongSprites.json con el archivo, la cantidad de cuadros y cuánto
dura cada cuadro, para que el juego no tenga esos números escritos a mano.
"""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from PIL import Image, ImageOps  # noqa: E402

from nailong import construir  # noqa: E402
from render import preparar_escena, renderizar_hoja  # noqa: E402

RAIZ = Path(__file__).resolve().parents[2]
CARPETA = RAIZ / "public" / "sprites" / "nailong"
INDICE = RAIZ / "src" / "lib" / "nailongSprites.json"

# nombre en el juego: (animación, vista, ánimo, cuadros, ms por cuadro, espejar)
# El quieto va por estado de ánimo del juego; regar mira a la izquierda porque
# Nailong se para a la derecha de la maceta.
HOJAS = {
    "idle_happy": ("quieto", "lado", "feliz", 4, 600, False),
    "idle_hungry": ("quieto", "lado", "antojado", 4, 600, False),
    "idle_sleepy": ("quieto", "lado", "cansado", 4, 600, False),
    "idle_sad": ("quieto", "lado", "triste", 4, 600, False),
    "walk_side": ("caminar", "lado", "feliz", 8, 70, False),
    "walk_side_sad": ("caminar", "lado", "triste", 8, 90, False),
    "walk_front": ("caminar", "frente", "feliz", 8, 70, False),
    "walk_back": ("caminar", "espalda", "feliz", 8, 70, False),
    "eat": ("comer", "frente", "feliz", 8, 0, False),
    "play": ("saltar", "frente", "feliz", 8, 0, False),
    "water": ("regar", "lado", "feliz", 8, 0, True),
    "sleep": ("acostado", "frente", "feliz", 8, 0, False),
}

# Hojas con cuadro distinto al cuadrado de siempre: (ancho, alto, altura del centro, zoom).
# Acostado, Nailong es más largo que alto, y se dibuja un poco más chico para
# que quepa en la cama sin perder el píxel nítido.
ENCUADRES = {"sleep": (80, 48, 0.45, 0.8)}


def main():
    modelo = construir()
    camara, material = preparar_escena()
    CARPETA.mkdir(parents=True, exist_ok=True)
    solo = set(sys.argv[1:]) or set(HOJAS)
    indice = json.loads(INDICE.read_text()) if INDICE.exists() else {}
    with tempfile.TemporaryDirectory() as temporal:
        for nombre, (animacion, vista, animo, cuadros, ms, espejar) in HOJAS.items():
            if nombre not in solo:
                continue
            encuadre = ENCUADRES.get(nombre)
            argumentos = (encuadre,) if encuadre else ()
            hoja = renderizar_hoja(modelo, camara, material, animacion, vista, animo, [], cuadros, Path(temporal), *argumentos)
            if espejar:
                # Se espeja cuadro por cuadro para que la secuencia no quede al revés.
                lado = hoja.height
                partes = [ImageOps.mirror(hoja.crop((i * lado, 0, (i + 1) * lado, lado))) for i in range(cuadros)]
                hoja = Image.new("RGBA", hoja.size)
                for i, parte in enumerate(partes):
                    hoja.paste(parte, (i * lado, 0))
            hoja.save(CARPETA / f"{nombre}.png")
            # Las acciones duran lo que diga el juego: ms 0 significa que el
            # cuadro sale del avance de la acción, no de un reloj fijo.
            indice[nombre] = {"file": f"sprites/nailong/{nombre}.png", "frames": cuadros, "frameMs": ms}
            print(f"{nombre}: {cuadros} cuadros")
    INDICE.write_text(json.dumps(indice, indent=2) + "\n")


if __name__ == "__main__":
    main()
