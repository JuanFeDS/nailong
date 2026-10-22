"""Animaciones de Nailong como datos: ángulos de cada hueso en cada cuadro.

Una animación nueva es solo una función que devuelve la pose de un cuadro;
no hace falta dibujar nada. Los ángulos están en grados y siguen los ejes
locales de cada hueso en Blender.
"""

from math import cos, pi, sin

Pose = dict[str, dict]


def quieto(fase: float, animo: str) -> Pose:
    respiro = sin(fase * 2 * pi)
    triste = animo == "triste"
    return {
        "raiz": {"lift": 0.01 * respiro},
        "cabeza": {"rot": (14 if triste else -3 + 2 * respiro, 0, 0)},
        "brazo.R": {"rot": (0, -4 if triste else 6 * respiro, 0)},
        "brazo.L": {"rot": (0, 4 if triste else -6 * respiro, 0)},
        "cola": {"rot": (0, 0, 8 * respiro)},
    }


def caminar(fase: float, animo: str) -> Pose:
    """Ciclo de caminata: piernas y brazos opuestos, rebote del cuerpo."""
    angulo = fase * 2 * pi
    paso = sin(angulo)
    triste = animo == "triste"
    amplitud = 18 if triste else 28
    return {
        "raiz": {"lift": (0.02 if triste else 0.05) * abs(cos(angulo))},
        "cuerpo": {"rot": (0, 0, 4 * paso)},
        "cabeza": {"rot": (14 if triste else -2, 0, -3 * paso)},
        "pierna.R": {"rot": (amplitud * paso, 0, 0)},
        "pierna.L": {"rot": (-amplitud * paso, 0, 0)},
        "brazo.R": {"rot": (-amplitud * paso, 0, 0)},
        "brazo.L": {"rot": (amplitud * paso, 0, 0)},
        "cola": {"rot": (0, 0, 12 * paso)},
    }


ANIMACIONES = {"quieto": quieto, "caminar": caminar}
