"""Objetos nuevos de la sala dibujados en pixel art."""

from PIL import Image

from pincel import Lienzo

MADERA = ("#f0b064", "#d07a34", "#9a4c22")
TELA_SOFA = ("#7fd6cf", "#3fa7a8", "#2a7a80")
HOJA = ("#9be05a", "#5cb83a", "#357a2a")
MACETA = ("#f2905a", "#d0603a", "#9a3a26")
DORADO = ("#ffe07a", "#e0a838", "#a86a1e")


def sofa() -> Image.Image:
    """Sofá de tres puestos con respaldo, brazos y patas de madera."""
    lienzo = Lienzo(76, 46)
    claro, medio, oscuro = TELA_SOFA
    lienzo.redondo(6, 2, 69, 26, 6, medio)
    lienzo.rect(8, 3, 67, 5, claro)
    for x in (27, 48):
        lienzo.rect(x, 6, x, 22, oscuro)
    lienzo.redondo(8, 22, 67, 37, 4, claro)
    lienzo.rect(8, 33, 67, 37, medio)
    for x in (27, 48):
        lienzo.rect(x, 23, x, 32, medio)
    for x0 in (0, 64):
        lienzo.redondo(x0, 14, x0 + 11, 39, 4, medio)
        lienzo.rect(x0 + 2, 15, x0 + 9, 17, claro)
        lienzo.rect(x0 + 1, 35, x0 + 10, 39, oscuro)
    for x0 in (3, 69):
        lienzo.rect(x0, 40, x0 + 3, 45, MADERA[2])
        lienzo.rect(x0, 40, x0 + 1, 42, MADERA[1])
    return lienzo.terminar()


def cojines() -> Image.Image:
    """Montón de dos cojines en el suelo."""
    lienzo = Lienzo(34, 22)
    lienzo.redondo(0, 6, 21, 21, 5, "#e8482c")
    lienzo.rect(3, 8, 17, 9, "#ff7a56")
    lienzo.rect(2, 18, 19, 20, "#a82a1e")
    lienzo.punto(10, 13, "#a82a1e")
    lienzo.redondo(13, 0, 33, 17, 5, "#ffd04a")
    lienzo.rect(16, 2, 30, 3, "#fff09a")
    lienzo.rect(15, 14, 31, 16, "#d09a26")
    lienzo.punto(23, 8, "#d09a26")
    return lienzo.terminar()


def mesa_centro() -> Image.Image:
    """Mesa de centro baja con una taza encima."""
    lienzo = Lienzo(50, 30)
    claro, medio, oscuro = MADERA
    lienzo.redondo(0, 8, 49, 20, 3, claro)
    lienzo.rect(3, 9, 46, 10, "#ffd49a")
    lienzo.rect(0, 17, 49, 21, medio)
    lienzo.rect(2, 21, 47, 22, oscuro)
    for x0 in (3, 43):
        lienzo.rect(x0, 22, x0 + 3, 29, oscuro)
    lienzo.rect(10, 22, 39, 23, oscuro)
    lienzo.redondo(30, 0, 39, 11, 2, "#f4f0e0")
    lienzo.rect(32, 1, 37, 2, "#e8341c")
    lienzo.rect(39, 3, 41, 7, "#f4f0e0")
    lienzo.redondo(8, 9, 24, 13, 1, "#2f9be8")
    lienzo.rect(9, 9, 23, 10, "#7cc4f4")
    return lienzo.terminar()


def televisor() -> Image.Image:
    """Televisor de pantalla plana sobre un mueble bajo."""
    lienzo = Lienzo(48, 50)
    claro, medio, oscuro = MADERA
    lienzo.redondo(2, 0, 45, 29, 3, "#2a2a36")
    lienzo.rect(5, 3, 42, 25, "#3f8fc0")
    lienzo.rect(5, 3, 42, 6, "#6cc0e8")
    lienzo.poligono([(8, 24), (16, 6), (20, 6), (12, 24)], "#6cc0e8")
    lienzo.rect(5, 21, 42, 25, "#2f6f9a")
    lienzo.rect(21, 29, 26, 33, "#2a2a36")
    lienzo.redondo(0, 33, 47, 49, 2, medio)
    lienzo.rect(1, 33, 46, 35, claro)
    lienzo.rect(4, 38, 22, 46, oscuro)
    lienzo.rect(25, 38, 43, 46, oscuro)
    lienzo.rect(12, 41, 14, 42, claro)
    lienzo.rect(33, 41, 35, 42, claro)
    lienzo.punto(43, 27, "#e8341c")
    return lienzo.terminar()


def planta_grande() -> Image.Image:
    """Costilla de Adán en una maceta grande de barro."""
    lienzo = Lienzo(40, 62)
    claro, medio, oscuro = HOJA
    hojas = [(2, 14, 20, 30), (20, 8, 38, 24), (8, 0, 26, 16), (18, 24, 36, 40), (0, 28, 16, 42), (12, 18, 28, 34)]
    for x0, y0, x1, y1 in hojas:
        lienzo.elipse(x0, y0, x1, y1, medio)
        lienzo.elipse(x0 + 2, y0 + 1, x1 - 5, y1 - 6, claro)
        centro_x, centro_y = (x0 + x1) // 2, (y0 + y1) // 2
        lienzo.linea([(centro_x, centro_y), (20, 44)], oscuro)
    lienzo.linea([(20, 30), (20, 44)], oscuro, 2)
    terracota_claro, terracota, terracota_oscuro = MACETA
    lienzo.poligono([(8, 44), (32, 44), (29, 61), (11, 61)], terracota)
    lienzo.rect(7, 42, 33, 47, terracota_claro)
    lienzo.rect(7, 47, 33, 48, terracota_oscuro)
    lienzo.rect(24, 49, 27, 59, terracota_oscuro)
    return lienzo.terminar()


def cuadro() -> Image.Image:
    """Cuadro de pared con un atardecer en el mar y marco dorado."""
    lienzo = Lienzo(44, 32)
    claro, medio, oscuro = DORADO
    lienzo.rect(0, 0, 43, 31, medio)
    lienzo.rect(1, 1, 42, 2, claro)
    lienzo.rect(1, 29, 42, 30, oscuro)
    lienzo.rect(4, 4, 39, 27, "#ff9a4a")
    lienzo.rect(4, 4, 39, 9, "#ff6b4a")
    lienzo.elipse(16, 10, 27, 21, "#ffe07a")
    lienzo.rect(4, 17, 39, 27, "#2f7fc0")
    lienzo.rect(4, 17, 39, 18, "#ffb05a")
    for y, x0, x1 in ((20, 14, 29), (23, 17, 26), (25, 8, 13), (22, 31, 36)):
        lienzo.rect(x0, y, x1, y, "#7cc4f4")
    return lienzo.terminar()


def planta_colgante() -> Image.Image:
    """Maceta colgada de un gancho con hojas que caen."""
    lienzo = Lienzo(28, 46)
    claro, medio, oscuro = HOJA
    lienzo.rect(13, 0, 14, 2, "#5a4a40")
    for desde, hasta in (((13, 2), (4, 16)), ((14, 2), (23, 16)), ((13, 2), (13, 16))):
        lienzo.linea([desde, hasta], "#e8d0a0")
    lienzo.redondo(4, 15, 23, 25, 3, "#f4f0e0")
    lienzo.rect(5, 16, 22, 17, "#ffffff")
    lienzo.rect(5, 22, 22, 24, "#c8c0a8")
    for x0, largo in ((3, 18), (8, 26), (15, 14), (21, 22)):
        for paso in range(0, largo, 4):
            y = 22 + paso
            lienzo.elipse(x0 + (paso // 4) % 2 * 2 - 1, y, x0 + 4 + (paso // 4) % 2 * 2, y + 4, medio if paso % 8 else claro)
        lienzo.linea([(x0 + 2, 22), (x0 + 2, 22 + largo)], oscuro)
    lienzo.elipse(6, 10, 14, 17, medio)
    lienzo.elipse(13, 9, 22, 17, claro)
    return lienzo.terminar()


OBJETOS = {
    "sofa": sofa,
    "cushions": cojines,
    "coffeetable": mesa_centro,
    "tv": televisor,
    "bigplant": planta_grande,
    "painting": cuadro,
    "hangingplant": planta_colgante,
}
