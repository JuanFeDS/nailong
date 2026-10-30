"""Objetos nuevos del patio dibujados en pixel art."""

from PIL import Image

from pincel import Lienzo

MADERA = ("#f0b064", "#d07a34", "#9a4c22")
HIERRO = ("#5a5e6e", "#3a3c48", "#24242e")
PIEDRA = ("#d8d4c8", "#a8a498", "#78746c")
FLORES = ("#e8341c", "#ffd04a", "#f4f0e0", "#ff6bb0")


def banca() -> Image.Image:
    """Banca de parque con listones de madera y patas de hierro."""
    lienzo = Lienzo(66, 40)
    claro, medio, oscuro = MADERA
    hierro_claro, hierro, hierro_oscuro = HIERRO
    for x0 in (5, 56):
        lienzo.rect(x0, 2, x0 + 4, 39, hierro)
        lienzo.rect(x0, 2, x0 + 1, 39, hierro_claro)
        lienzo.rect(x0 - 2, 36, x0 + 6, 39, hierro_oscuro)
    for y in (2, 9):
        lienzo.redondo(0, y, 65, y + 5, 2, medio)
        lienzo.rect(1, y, 64, y + 1, claro)
    for y in (20, 25):
        lienzo.rect(0, y, 65, y + 4, claro if y == 20 else medio)
    lienzo.rect(0, 29, 65, 31, oscuro)
    lienzo.rect(4, 31, 61, 32, hierro_oscuro)
    return lienzo.terminar()


def macetas() -> Image.Image:
    """Tres macetas de barro con flores de colores."""
    lienzo = Lienzo(46, 32)
    macetas_dibujo = ((0, 14, 15, FLORES[0]), (16, 8, 14, FLORES[1]), (31, 12, 15, FLORES[3]))
    for x0, alto_tallo, ancho, color in macetas_dibujo:
        centro = x0 + ancho // 2
        lienzo.linea([(centro, 20), (centro, 20 - alto_tallo)], "#357a2a")
        lienzo.elipse(centro - 5, 14 - alto_tallo // 2, centro - 1, 18 - alto_tallo // 2, "#5cb83a")
        lienzo.elipse(centro + 1, 16 - alto_tallo // 3, centro + 5, 20 - alto_tallo // 3, "#5cb83a")
        cima = 20 - alto_tallo
        for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3)):
            lienzo.elipse(centro + dx - 2, cima + dy - 2, centro + dx + 2, cima + dy + 2, color)
        lienzo.elipse(centro - 1, cima - 1, centro + 1, cima + 1, "#ffe07a")
        lienzo.poligono([(x0, 20), (x0 + ancho - 1, 20), (x0 + ancho - 3, 31), (x0 + 2, 31)], "#d0603a")
        lienzo.rect(x0 - 1, 19, x0 + ancho, 22, "#f2905a")
        lienzo.rect(x0 + ancho - 5, 23, x0 + ancho - 4, 29, "#9a3a26")
    return lienzo.terminar()


def bebedero() -> Image.Image:
    """Bebedero de pájaros de piedra con agua."""
    lienzo = Lienzo(32, 46)
    claro, medio, oscuro = PIEDRA
    lienzo.elipse(0, 2, 31, 14, medio)
    lienzo.elipse(3, 3, 28, 10, "#4fa8d8")
    lienzo.rect(8, 4, 16, 5, "#9ad8f4")
    lienzo.rect(0, 8, 31, 9, claro)
    lienzo.poligono([(2, 9), (29, 9), (22, 17), (9, 17)], medio)
    lienzo.rect(12, 16, 19, 38, medio)
    lienzo.rect(12, 16, 13, 38, claro)
    lienzo.rect(18, 16, 19, 38, oscuro)
    lienzo.redondo(6, 37, 25, 45, 2, medio)
    lienzo.rect(7, 37, 24, 38, claro)
    lienzo.rect(7, 43, 24, 44, oscuro)
    lienzo.elipse(19, 0, 25, 5, "#e8341c")
    lienzo.punto(26, 2, "#ffb000")
    lienzo.punto(23, 1, "#24242e")
    return lienzo.terminar()


def farol() -> Image.Image:
    """Farol de jardín con poste de hierro y luz cálida."""
    lienzo = Lienzo(20, 74)
    hierro_claro, hierro, hierro_oscuro = HIERRO
    lienzo.poligono([(2, 6), (17, 6), (13, 0), (6, 0)], hierro)
    lienzo.rect(3, 6, 16, 22, hierro_oscuro)
    lienzo.rect(5, 8, 14, 20, "#ffd04a")
    lienzo.rect(6, 9, 9, 17, "#fff09a")
    lienzo.rect(9, 8, 10, 20, hierro_oscuro)
    lienzo.rect(2, 22, 17, 24, hierro)
    lienzo.rect(8, 24, 11, 68, hierro)
    lienzo.rect(8, 24, 8, 68, hierro_claro)
    lienzo.rect(4, 66, 15, 73, hierro_oscuro)
    lienzo.rect(5, 66, 14, 67, hierro)
    return lienzo.terminar()


OBJETOS = {
    "bench": banca,
    "flowerpots": macetas,
    "birdbath": bebedero,
    "lamppost": farol,
}
