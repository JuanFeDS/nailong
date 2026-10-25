"""Colores finales de cada material, tomados de los sprites dibujados a mano.

Cada rampa va de oscuro a claro: el primer color es el contorno y los demás
son los tonos de sombra a luz que el render elige según cuánta luz recibe
cada píxel.
"""

RAMPAS = {
    "piel": ["#a05022", "#e26721", "#faa426", "#fdcb32", "#fcd45d"],
    "panza": ["#e26721", "#fcd45d", "#fceab7", "#fceab7", "#fceab7"],
    "palma": ["#e26721", "#f19f5f", "#f89f94", "#f89f94", "#fceab7"],
    "garra": ["#672f1b", "#672f1b", "#672f1b", "#6c4e24", "#996b4c"],
    "ojo": ["#5f9e54", "#5f9e54", "#5f9e54", "#5f9e54", "#5f9e54"],
    "boca": ["#697661", "#697661", "#697661", "#697661", "#697661"],
    "parpado": ["#a05022", "#e26721", "#faa426", "#fdcb32", "#fcd45d"],
    "lagrima": ["#41a6f6", "#73eff7", "#73eff7", "#73eff7", "#73eff7"],
    "mejilla": ["#f0644d", "#f89f94", "#f89f94", "#f89f94", "#f89f94"],
    "sudor": ["#41a6f6", "#73eff7", "#73eff7", "#f5f4eb", "#f5f4eb"],
    "cresta": ["#1b2317", "#315a2c", "#3d823b", "#50923b", "#5f9e54"],
    "gorra": ["#1d2b53", "#29366f", "#3b5dc9", "#41a6f6", "#41a6f6"],
    "visera": ["#1d2b53", "#29366f", "#29366f", "#3b5dc9", "#3b5dc9"],
    "galleta": ["#4a2414", "#672f1b", "#8f4f2a", "#b8743f", "#d29a5c"],
    "ropa": ["#3b1f5c", "#5d3a9b", "#8a63d2", "#b18cf0", "#cbb2f5"],
    "tina": ["#333c57", "#566c86", "#94b0c2", "#c3d4dd", "#f4f4f4"],
    "agua": ["#2b6fb5", "#41a6f6", "#73eff7", "#a6f6fa", "#a6f6fa"],
    "espuma": ["#94b0c2", "#f4f4f4", "#f4f4f4", "#ffffff", "#ffffff"],
    "papel": ["#94b0c2", "#d8dde6", "#f4f4f4", "#ffffff", "#ffffff"],
    "lapiz": ["#7a1f3d", "#b13e53", "#ef4a5a", "#ff7b84", "#ff9ea4"],
    "libro": ["#1b3a4b", "#257179", "#38b764", "#5fd38a", "#a7f070"],
    "madera": ["#4a2a1a", "#7a4a2a", "#a0683d", "#c48a52", "#d9a86c"],
    "maceta": ["#5c2a1e", "#a0442a", "#c8643c", "#e08352", "#eda06e"],
    "planta": ["#1b4a2a", "#257d3a", "#38b764", "#71d65a", "#a7f070"],
    "regadera": ["#1b3a4b", "#2b6f80", "#3fa3b5", "#6cd0dc", "#a6eef4"],
    "morado": ["#1e0f2e", "#3b1f5c", "#5d3a9b", "#7a52c0", "#9a72dc"],
    "negro": ["#0b0b12", "#1a1a24", "#2b2b38", "#3c3c4c", "#4c4c60"],
    "calabaza": ["#5c1f08", "#b8400c", "#e8600f", "#f58a2a", "#f9a84a"],
    "sabana": ["#7d879c", "#c9d0de", "#e9edf4", "#ffffff", "#ffffff"],
    "rojo": ["#3d0a10", "#7a1420", "#b8202c", "#d8343a", "#e85048"],
    "dorado": ["#5c3a0a", "#a0700f", "#d8a528", "#f2cf5a", "#fbe7a0"],
}

# Rasgos pequeños de la cara: ganan el píxel aunque cubran solo parte de él,
# para que ojos y boca no desaparezcan al reducir a la resolución final.
# Van de mayor a menor prioridad: si dos compiten por un píxel, gana el primero.
DETALLES = ["lagrima", "sudor", "boca", "ojo", "mejilla"]

# Umbrales de luz que separan los tonos de sombra a luz (sin contar el contorno).
UMBRALES_LUZ = [0.42, 0.62, 0.86]


def a_rgb(hexadecimal: str) -> tuple[int, int, int]:
    valor = hexadecimal.lstrip("#")
    return tuple(int(valor[indice : indice + 2], 16) for indice in (0, 2, 4))
