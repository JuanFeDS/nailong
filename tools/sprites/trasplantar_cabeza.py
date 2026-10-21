"""Sustituye la cabeza de cada frame por la de una hoja de referencia.

Sirve para que una animación generada con la cara de frente recupere la vista
en tres cuartos del diseño original. La cabeza de referencia se escala a la
altura de la cabeza original y se apoya sobre la barbilla; opcionalmente se le
pinta la boca abierta en lugar de la sonrisa.

Uso:
    python tools/sprites/trasplantar_cabeza.py play_original.png play.png --frames 8 \
        --referencia public/sprites/processed/idle.png --frames-referencia 4 \
        --cabezas 3,3,3,-1,3,3,2,3 --boca-abierta 3
"""

import argparse
from pathlib import Path

import numpy as np
from PIL import Image

from achicar_cabeza import fila_de_barbilla

COLOR_BOCA = (150, 35, 55, 255)
COLOR_LENGUA = (236, 104, 116, 255)
MARGEN_CUBRIR = 1
FRACCION_BOCA = 0.55


def cabeza_de(frame: np.ndarray) -> Image.Image:
    """Recorta la cabeza (de la cima a la barbilla) de un frame RGBA."""
    corte = fila_de_barbilla(frame)
    imagen = Image.fromarray(frame[:corte])
    return imagen.crop(imagen.getchannel("A").getbbox())


def abrir_boca(cabeza: Image.Image) -> Image.Image:
    """Cambia la línea gris de la sonrisa por una boca abierta."""
    datos = np.array(cabeza)
    rojo, verde, azul = datos[..., 0].astype(int), datos[..., 1].astype(int), datos[..., 2].astype(int)
    gris = (abs(rojo - verde) < 25) & (abs(verde - azul) < 25) & (verde > 90) & (verde < 190) & (datos[..., 3] > 0)
    gris[: int(datos.shape[0] * FRACCION_BOCA)] = False
    filas, columnas = np.nonzero(gris)
    if len(filas) == 0:
        return cabeza
    centro_fila, centro_columna = int(filas.mean()), int(columnas.mean())
    datos[gris] = datos[max(0, filas.min() - 2), centro_columna]
    for desfase_fila in range(-1, 3):
        mitad = 3 - abs(desfase_fila - 0.5) * 1.2
        for desfase_columna in range(-int(mitad), int(mitad) + 1):
            fila, columna = centro_fila + desfase_fila, centro_columna + desfase_columna
            if 0 <= fila < datos.shape[0] and 0 <= columna < datos.shape[1]:
                datos[fila, columna] = COLOR_LENGUA if desfase_fila == 2 else COLOR_BOCA
    return Image.fromarray(datos)


def trasplantar(frame: np.ndarray, nueva: Image.Image, borrar: bool) -> np.ndarray:
    """Cubre la cabeza original con la nueva, apoyada en la barbilla.

    Con borrar=False solo se pega encima, así los brazos junto a la cabeza se conservan.
    """
    corte = fila_de_barbilla(frame)
    filas, columnas = np.nonzero(frame[:corte, :, 3] > 0)
    cima = filas.min()
    alto_original = corte - cima
    fila_media = cima + alto_original // 2
    tramo = np.nonzero(frame[fila_media, :, 3] > 0)[0]
    centro_x = int((tramo.min() + tramo.max()) / 2)
    ancho_original = int(tramo.max() - tramo.min() + 1)

    escala = alto_original / nueva.height
    nuevo_ancho, nuevo_alto = max(1, round(nueva.width * escala)), alto_original
    reducida = nueva.resize((nuevo_ancho, nuevo_alto), Image.NEAREST)

    resultado = frame.copy()
    if borrar:
        radio_x = (max(ancho_original, nuevo_ancho) / 2) + MARGEN_CUBRIR
        radio_y = alto_original / 2 + MARGEN_CUBRIR
        ejes_y, ejes_x = np.ogrid[: resultado.shape[0], : resultado.shape[1]]
        dentro = ((ejes_x - centro_x) / radio_x) ** 2 + ((ejes_y - fila_media) / radio_y) ** 2 <= 1
        dentro[corte:] = False
        resultado[dentro] = (0, 0, 0, 0)

    capa = Image.fromarray(resultado)
    capa.alpha_composite(reducida, (max(0, centro_x - nuevo_ancho // 2), cima))
    return np.array(capa)


def main() -> None:
    """Trasplanta la cabeza elegida a cada frame de la tira."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("entrada", type=Path)
    parser.add_argument("salida", type=Path)
    parser.add_argument("--frames", type=int, required=True)
    parser.add_argument("--referencia", type=Path, required=True)
    parser.add_argument("--frames-referencia", type=int, required=True)
    parser.add_argument("--cabezas", required=True, help="Frame de referencia por frame (-1 = no tocar)")
    parser.add_argument("--boca-abierta", type=int, nargs="*", default=[], help="Frames de referencia con boca abierta")
    parser.add_argument("--borrar", action="store_true", help="Borrar la cabeza original antes de pegar")
    argumentos = parser.parse_args()

    tira = np.array(Image.open(argumentos.entrada).convert("RGBA"))
    referencia = np.array(Image.open(argumentos.referencia).convert("RGBA"))
    ancho_ref = referencia.shape[1] // argumentos.frames_referencia
    cabezas = {}
    for indice in range(argumentos.frames_referencia):
        cabeza = cabeza_de(referencia[:, indice * ancho_ref : (indice + 1) * ancho_ref])
        cabezas[indice] = abrir_boca(cabeza) if indice in argumentos.boca_abierta else cabeza

    elegidas = [int(valor) for valor in argumentos.cabezas.split(",")]
    ancho = tira.shape[1] // argumentos.frames
    for indice, elegida in enumerate(elegidas):
        if elegida < 0:
            continue
        inicio = indice * ancho
        tira[:, inicio : inicio + ancho] = trasplantar(
            tira[:, inicio : inicio + ancho], cabezas[elegida], argumentos.borrar
        )
    Image.fromarray(tira).save(argumentos.salida)
    print(f"{argumentos.frames} frames -> {argumentos.salida}")


if __name__ == "__main__":
    main()
