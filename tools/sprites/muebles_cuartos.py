"""Puertas y muebles fijos de los cuartos comprables, dibujados en pixel art."""

from PIL import Image

from pincel import Lienzo

MADERA = ("#f0b064", "#d07a34", "#9a4c22")
METAL = ("#f4f4f0", "#c8ccd4", "#8a909c")
LOZA = ("#ffffff", "#e4ecf0", "#a8b8c4")


def _puerta(marco: str, marco_oscuro: str, dibujar_letrero) -> Image.Image:
    """Puerta interior de madera con marco de color y un letrero que indica el cuarto."""
    lienzo = Lienzo(36, 62)
    claro, medio, oscuro = MADERA
    lienzo.rect(0, 0, 35, 61, marco)
    lienzo.rect(0, 0, 35, 2, marco_oscuro)
    lienzo.rect(4, 4, 31, 61, medio)
    lienzo.rect(4, 4, 31, 5, claro)
    for x0, y0, y1 in ((7, 22, 34), (20, 22, 34), (7, 40, 56), (20, 40, 56)):
        lienzo.rect(x0, y0, x0 + 8, y1, oscuro)
        lienzo.rect(x0 + 1, y0 + 1, x0 + 7, y1 - 1, claro)
    lienzo.elipse(25, 35, 29, 39, "#ffd04a")
    lienzo.redondo(8, 7, 27, 19, 2, "#f4f0e0")
    dibujar_letrero(lienzo)
    return lienzo.terminar()


def _letrero_cama(lienzo: Lienzo):
    lienzo.rect(11, 13, 24, 16, "#e8482c")
    lienzo.rect(11, 11, 15, 13, "#f4a0a0")
    lienzo.rect(11, 16, 11, 17, "#9a4c22")
    lienzo.rect(24, 10, 24, 17, "#9a4c22")


def _letrero_olla(lienzo: Lienzo):
    lienzo.redondo(12, 12, 23, 17, 2, "#5a5e6e")
    lienzo.rect(10, 12, 25, 12, "#3a3c48")
    lienzo.rect(16, 9, 19, 10, "#3a3c48")


def _letrero_gota(lienzo: Lienzo):
    lienzo.poligono([(17, 8), (13, 14), (22, 14)], "#2f9be8")
    lienzo.elipse(13, 11, 22, 18, "#2f9be8")
    lienzo.rect(15, 13, 16, 14, "#9ad8f4")


def _letrero_estrella(lienzo: Lienzo):
    lienzo.poligono([(17, 8), (19, 12), (24, 12), (20, 15), (22, 19), (17, 16), (13, 19), (15, 15), (11, 12), (16, 12)], "#ffb000")


def puerta_dormitorio() -> Image.Image:
    """Puerta al dormitorio, marco rosa y una cama en el letrero."""
    return _puerta("#e87a9a", "#b84a6a", _letrero_cama)


def puerta_cocina() -> Image.Image:
    """Puerta a la cocina, marco crema y una olla en el letrero."""
    return _puerta("#e8c87a", "#b8984a", _letrero_olla)


def puerta_bano() -> Image.Image:
    """Puerta al baño, marco azul y una gota en el letrero."""
    return _puerta("#5aa8e0", "#2a78b0", _letrero_gota)


def puerta_juegos() -> Image.Image:
    """Puerta al cuarto de juegos, marco verde y una estrella en el letrero."""
    return _puerta("#6cc84a", "#3a9a2a", _letrero_estrella)


def puerta_salida() -> Image.Image:
    """Puerta para volver a la sala, con una flecha en el letrero."""
    def flecha(lienzo: Lienzo):
        lienzo.rect(14, 12, 24, 14, "#9a4c22")
        lienzo.poligono([(10, 13), (15, 8), (15, 18)], "#9a4c22")
    return _puerta("#c8a078", "#986848", flecha)


def mesita_noche() -> Image.Image:
    """Mesita de noche con cajón y un despertador."""
    lienzo = Lienzo(28, 38)
    claro, medio, oscuro = MADERA
    lienzo.redondo(2, 0, 13, 10, 3, "#e8341c")
    lienzo.elipse(4, 2, 11, 8, "#f4f0e0")
    lienzo.rect(7, 4, 7, 5, "#24242e")
    lienzo.rect(8, 5, 9, 5, "#24242e")
    lienzo.rect(0, 10, 27, 14, claro)
    lienzo.rect(1, 14, 26, 33, medio)
    lienzo.rect(4, 17, 23, 23, oscuro)
    lienzo.rect(5, 18, 22, 22, claro)
    lienzo.rect(12, 20, 15, 20, oscuro)
    lienzo.rect(4, 26, 23, 30, oscuro)
    for x0 in (2, 22):
        lienzo.rect(x0, 33, x0 + 3, 37, oscuro)
    return lienzo.terminar()


def nevera() -> Image.Image:
    """Nevera de dos puertas con imanes."""
    lienzo = Lienzo(36, 68)
    claro, medio, oscuro = METAL
    lienzo.redondo(0, 0, 35, 67, 4, medio)
    lienzo.rect(2, 2, 33, 4, claro)
    lienzo.rect(0, 24, 35, 25, oscuro)
    lienzo.rect(28, 8, 30, 20, oscuro)
    lienzo.rect(28, 30, 30, 46, oscuro)
    lienzo.rect(3, 26, 4, 64, claro)
    lienzo.elipse(8, 32, 13, 37, "#e8341c")
    lienzo.rect(15, 40, 21, 46, "#ffd04a")
    lienzo.elipse(9, 9, 14, 14, "#2f9be8")
    lienzo.rect(2, 64, 33, 67, oscuro)
    return lienzo.terminar()


def estufa() -> Image.Image:
    """Estufa con cuatro quemadores, horno y una olla."""
    lienzo = Lienzo(44, 50)
    claro, medio, oscuro = METAL
    lienzo.rect(0, 12, 43, 18, "#3a3c48")
    for x0 in (4, 24):
        lienzo.elipse(x0, 13, x0 + 14, 17, "#24242e")
    lienzo.redondo(24, 0, 39, 14, 2, "#e8482c")
    lienzo.rect(26, 1, 37, 2, "#ff7a56")
    lienzo.rect(22, 3, 24, 5, "#a82a1e")
    lienzo.rect(39, 3, 41, 5, "#a82a1e")
    lienzo.rect(0, 18, 43, 49, medio)
    lienzo.rect(0, 18, 43, 22, claro)
    for x in (6, 14, 30, 38):
        lienzo.elipse(x - 2, 19, x + 2, 21, oscuro)
    lienzo.redondo(5, 25, 38, 45, 2, oscuro)
    lienzo.rect(8, 28, 35, 42, "#3a3c48")
    lienzo.rect(10, 30, 20, 31, "#5a5e6e")
    lienzo.rect(8, 25, 35, 26, claro)
    return lienzo.terminar()


def tina() -> Image.Image:
    """Tina con patas, espuma y patito de hule."""
    lienzo = Lienzo(72, 44)
    claro, medio, oscuro = LOZA
    lienzo.rect(4, 0, 7, 12, "#c8ccd4")
    lienzo.rect(4, 0, 13, 3, "#c8ccd4")
    lienzo.elipse(6, 14, 16, 22, "#ffffff")
    lienzo.elipse(14, 10, 26, 20, "#ffffff")
    lienzo.elipse(24, 12, 34, 20, "#ffffff")
    lienzo.elipse(48, 9, 56, 17, "#ffd04a")
    lienzo.elipse(53, 6, 59, 12, "#ffd04a")
    lienzo.rect(59, 9, 61, 10, "#ff9a2a")
    lienzo.punto(56, 8, "#24242e")
    lienzo.redondo(0, 16, 71, 38, 10, medio)
    lienzo.rect(4, 16, 67, 19, claro)
    lienzo.rect(6, 33, 65, 36, oscuro)
    for x0 in (8, 58):
        lienzo.rect(x0, 37, x0 + 5, 43, "#e0a838")
    return lienzo.terminar()


def lavamanos() -> Image.Image:
    """Lavamanos de pedestal con espejo redondo encima."""
    lienzo = Lienzo(32, 70)
    claro, medio, oscuro = LOZA
    lienzo.elipse(4, 0, 27, 22, "#e0a838")
    lienzo.elipse(7, 3, 24, 19, "#9ad8f4")
    lienzo.rect(10, 6, 12, 10, "#ffffff")
    lienzo.rect(14, 26, 17, 32, "#c8ccd4")
    lienzo.rect(14, 26, 21, 28, "#c8ccd4")
    lienzo.redondo(0, 31, 31, 41, 4, medio)
    lienzo.rect(2, 31, 29, 33, claro)
    lienzo.poligono([(8, 41), (23, 41), (20, 64), (11, 64)], medio)
    lienzo.rect(11, 42, 12, 63, claro)
    lienzo.rect(19, 42, 20, 63, oscuro)
    lienzo.redondo(7, 63, 24, 69, 2, oscuro)
    return lienzo.terminar()


def maquinita() -> Image.Image:
    """Máquina de arcade con pantalla, palanca y botones."""
    lienzo = Lienzo(40, 72)
    lienzo.redondo(0, 0, 39, 71, 3, "#e8341c")
    lienzo.rect(2, 2, 37, 4, "#ff7a56")
    lienzo.rect(4, 6, 35, 14, "#24242e")
    lienzo.rect(8, 8, 31, 12, "#ffd04a")
    lienzo.rect(4, 17, 35, 39, "#24242e")
    lienzo.rect(7, 20, 32, 36, "#2f6f9a")
    lienzo.rect(10, 30, 14, 33, "#f4f0e0")
    lienzo.rect(18, 24, 20, 26, "#ffd04a")
    lienzo.rect(24, 28, 28, 31, "#7dd33a")
    lienzo.poligono([(0, 42), (39, 42), (39, 50), (0, 50)], "#a82a1e")
    lienzo.rect(9, 38, 10, 44, "#3a3c48")
    lienzo.elipse(7, 35, 12, 40, "#2f9be8")
    lienzo.elipse(20, 43, 24, 47, "#ffd04a")
    lienzo.elipse(27, 43, 31, 47, "#7dd33a")
    lienzo.rect(15, 56, 24, 62, "#24242e")
    lienzo.rect(18, 58, 21, 59, "#ffd04a")
    return lienzo.terminar()


def tobogan() -> Image.Image:
    """Tobogán pequeño de plástico con escalera."""
    lienzo = Lienzo(66, 52)
    lienzo.rect(6, 4, 9, 51, "#2f9be8")
    lienzo.rect(20, 4, 23, 51, "#2f9be8")
    for y in range(12, 50, 9):
        lienzo.rect(9, y, 20, y + 2, "#7cc4f4")
    lienzo.rect(4, 2, 25, 6, "#ffd04a")
    lienzo.poligono([(22, 4), (30, 4), (64, 44), (64, 51), (56, 51), (22, 12)], "#e8482c")
    lienzo.poligono([(24, 5), (29, 5), (62, 44), (58, 44)], "#ff7a56")
    lienzo.rect(56, 49, 65, 51, "#a82a1e")
    return lienzo.terminar()


OBJETOS = {
    "door_bedroom": puerta_dormitorio,
    "door_kitchen": puerta_cocina,
    "door_bathroom": puerta_bano,
    "door_playroom": puerta_juegos,
    "exitdoor": puerta_salida,
    "nightstand": mesita_noche,
    "fridge": nevera,
    "stove": estufa,
    "bathtub": tina,
    "sink": lavamanos,
    "arcade": maquinita,
    "slide": tobogan,
}
