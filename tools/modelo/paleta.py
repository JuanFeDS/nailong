"""Colores finales de cada material, tomados de los sprites dibujados a mano.

Cada rampa va de oscuro a claro: el primer color es el contorno y los demás
son los tonos de sombra a luz que el render elige según cuánta luz recibe
cada píxel.
"""

RAMPAS = {
    "piel": ["#a05022", "#e26721", "#faa426", "#fdcb32", "#fcd45d"],
    "panza": ["#e26721", "#fcd45d", "#fceab7", "#fceab7", "#fceab7"],
    "palma": ["#c83630", "#f0644d", "#f89f94", "#f89f94", "#f89f94"],
    "garra": ["#672f1b", "#672f1b", "#672f1b", "#6c4e24", "#996b4c"],
    "ojo": ["#5f9e54", "#5f9e54", "#5f9e54", "#5f9e54", "#5f9e54"],
    "boca": ["#697661", "#697661", "#697661", "#697661", "#697661"],
    "parpado": ["#a05022", "#e26721", "#faa426", "#fdcb32", "#fcd45d"],
    "lagrima": ["#41a6f6", "#73eff7", "#73eff7", "#73eff7", "#73eff7"],
    "gorra": ["#1d2b53", "#29366f", "#3b5dc9", "#41a6f6", "#41a6f6"],
    "visera": ["#1d2b53", "#29366f", "#29366f", "#3b5dc9", "#3b5dc9"],
}

# Rasgos pequeños de la cara: ganan el píxel aunque cubran solo parte de él,
# para que ojos y boca no desaparezcan al reducir a la resolución final.
# Van de mayor a menor prioridad: si dos compiten por un píxel, gana el primero.
DETALLES = ["lagrima", "boca", "ojo"]

# Los ojos miden pocos píxeles, así que no salen del sombreado 3D: se dibujan
# como en los sprites hechos a mano: borde oscuro arriba, pupila negra en la
# parte alta con un brillo a su derecha, iris verde a los lados, una franja
# verde clara abajo y la base verde oscura.
OJO = {
    "borde": "#1b2317",
    "pupila": "#1b2317",
    "iris": "#5f9e54",
    "iris_claro": "#72c85c",
    "iris_oscuro": "#315a2c",
    "brillo": "#f5f4eb",
}

# Umbrales de luz que separan los tonos de sombra a luz (sin contar el contorno).
UMBRALES_LUZ = [0.42, 0.62, 0.86]


def a_rgb(hexadecimal: str) -> tuple[int, int, int]:
    valor = hexadecimal.lstrip("#")
    return tuple(int(valor[indice : indice + 2], 16) for indice in (0, 2, 4))
