"""Animaciones de Nailong como datos: ángulos de cada hueso en cada cuadro.

Una animación nueva es solo una función que devuelve la pose de un cuadro;
no hace falta dibujar nada. Los ángulos están en grados y siguen los ejes
locales de cada hueso en Blender. Como las poses son fórmulas de la fase, se
pueden sacar tantos cuadros como se quiera y los intermedios salen solos.
"""

from math import cos, pi, sin, sqrt

Pose = dict[str, dict]


# Secuencia del "quieto" de los sprites 2D: de pie relajado, mira hacia arriba
# con los brazos abiertos, cierra los ojos de felicidad y saluda. El último
# cuadro es también el saludo que el juego usa al enviar algo.
# En Z, los brazos se abren hacia afuera con valores positivos en el derecho y
# negativos en el izquierdo. Girar el antebrazo en X negativo dobla el codo.
# La cabeza: X asiente (negativo mira arriba), Y voltea a los lados y Z la ladea.
SECUENCIA_QUIETO = [
    {
        "cabeza": {"rot": (-4, -10, 8)},
        "antebrazo.R": {"rot": (-25, 0, 0)},
        "antebrazo.L": {"rot": (-25, 0, 0)},
        "cola": {"rot": (0, 0, 6)},
    },
    {
        "raiz": {"lift": 0.02},
        "cabeza": {"rot": (-16, 14, 2)},
        "brazo.R": {"rot": (-35, 0, 55)},
        "brazo.L": {"rot": (-35, 0, -55)},
        "antebrazo.R": {"rot": (-30, 0, 0)},
        "antebrazo.L": {"rot": (-30, 0, 0)},
        "cola": {"rot": (0, 0, -6)},
    },
    {
        "cara": "contento",
        "cabeza": {"rot": (-6, 0, -8)},
        "brazo.R": {"rot": (5, 0, 0)},
        "brazo.L": {"rot": (5, 0, 0)},
        "antebrazo.R": {"rot": (-35, 0, 0)},
        "antebrazo.L": {"rot": (-35, 0, 0)},
        "cola": {"rot": (0, 0, 6)},
    },
    {
        "cabeza": {"rot": (-8, -18, 10)},
        "antebrazo.R": {"rot": (-25, 0, 0)},
        "brazo.L": {"rot": (-20, 0, -70)},
        "antebrazo.L": {"rot": (-40, 0, -30)},
        "cola": {"rot": (0, 0, -6)},
    },
]


CARAS_QUIETO_CANSADO = [
    {"cara": "cansado", "boca": "puchero"}, {"cara": "cansado"}, {"cara": "dormido"}, {"cara": "cansado", "boca": "pequena"},
]


def quieto(fase: float, animo: str) -> Pose:
    """De pie: la secuencia del 2D si está bien, cabizbajo y respirando si está triste o cansado."""
    if animo in ("triste", "cansado"):
        respiro = sin(fase * 2 * pi)
        return {
            **(gesto(fase, CARAS_QUIETO_CANSADO) if animo == "cansado" else {}),
            "raiz": {"lift": 0.01 * respiro},
            "cabeza": {"rot": (12, 0, 0)},
            "brazo.R": {"rot": (8, 0, -4)},
            "brazo.L": {"rot": (8, 0, 4)},
            "antebrazo.R": {"rot": (-15, 0, 0)},
            "antebrazo.L": {"rot": (-15, 0, 0)},
            "cola": {"rot": (0, 0, 4 * respiro)},
        }
    cuadro = SECUENCIA_QUIETO[int(fase * len(SECUENCIA_QUIETO)) % len(SECUENCIA_QUIETO)]
    return {hueso: dict(valores) if isinstance(valores, dict) else valores for hueso, valores in cuadro.items()}


def caminar(fase: float, animo: str) -> Pose:
    """Ciclo de caminata con el ritmo de los sprites 2D.

    Alterna dos momentos: agachado, con una pierna pateando hacia atrás en el
    aire, y estirado, con un paso amplio y las dos piernas en el suelo. Los
    brazos van abiertos y se balancean, y el cuerpo se inclina hacia adelante.
    En las piernas, girar en X positivo las lleva hacia atrás.
    """
    angulo = fase * 2 * pi
    paso = sin(angulo)  # ±1 en el paso amplio
    pasada = cos(angulo)  # ±1 cuando una pierna patea hacia atrás
    triste = animo == "triste"
    zancada = 18 if triste else 38
    patada = 15 if triste else 65
    balanceo = 20 if triste else 40
    abiertos = 5 if triste else 12
    # Aplastar y estirar: el cuerpo se achata al agacharse y se alarga al subir,
    # conservando el volumen, para que el rebote tenga peso.
    estiramiento = 1 + (0.01 if triste else 0.03) * abs(paso) - (0.02 if triste else 0.04) * abs(pasada)
    ancho = 1 / sqrt(estiramiento)
    return {
        "raiz": {"lift": (0.015 if triste else 0.04) * abs(paso)},
        "cuerpo": {"rot": (4 if triste else 9, 0, 5 * paso), "escala": (ancho, estiramiento, ancho)},
        "cabeza": {"rot": (12 if triste else -7 + 4 * abs(pasada), 7 * paso, -4 * paso)},
        # Se levanta la pierna que avanza (la que gira hacia adelante); la que está
        # apoyada empuja hacia atrás. Al revés, el paso se ve en reversa.
        "pierna.R": {"rot": (zancada * paso + patada * max(-pasada, 0), 0, 0), "lift": -0.1 * max(-pasada, 0)},
        "pierna.L": {"rot": (-zancada * paso + patada * max(pasada, 0), 0, 0), "lift": -0.1 * max(pasada, 0)},
        "brazo.R": {"rot": (-balanceo * paso, 0, abiertos)},
        "brazo.L": {"rot": (balanceo * paso, 0, -abiertos)},
        # El codo se dobla más cuando el brazo va hacia adelante.
        "antebrazo.R": {"rot": (-25 - 25 * max(paso, 0), 0, 0)},
        "antebrazo.L": {"rot": (-25 - 25 * max(-paso, 0), 0, 0)},
        "cola": {"rot": (0, 0, 15 * paso)},
    }


def mirar(fase: float, animo: str) -> Pose:
    """Voltea la cabeza a un lado y al otro, como mirando alrededor, y parpadea al pasar por el centro."""
    angulo = fase * 2 * pi
    giro = sin(angulo)
    triste = animo == "triste"
    return {
        **({"ojos": "parpadeo"} if 0.45 <= fase < 0.55 else {}),
        # Los ojos se adelantan hacia donde gira la cabeza, como hace cualquiera al voltear.
        "mirada": "derecha" if cos(angulo) > 0.3 else "izquierda" if cos(angulo) < -0.3 else "centro",
        "raiz": {"lift": 0.01 * abs(giro)},
        # Al voltear también ladea un poco la cabeza, que es más natural que un giro plano.
        "cabeza": {"rot": (12 if triste else -4 - 4 * abs(giro), (25 if triste else 45) * giro, 8 * giro)},
        "brazo.R": {"rot": (0, 0, 4 * max(giro, 0))},
        "brazo.L": {"rot": (0, 0, -4 * max(-giro, 0))},
        "antebrazo.R": {"rot": (-25, 0, 0)},
        "antebrazo.L": {"rot": (-25, 0, 0)},
        "cola": {"rot": (0, 0, -10 * giro)},
    }


# Recorrido de la mirada: mira a los lados, parpadea, mira arriba y abajo.
RECORRIDO_MIRADA = ["centro", "derecha", "derecha", "centro", "izquierda", "arriba_izquierda", "arriba", "abajo"]


def ojear(fase: float, animo: str) -> Pose:
    """Mueve solo los ojos de un lado a otro, con la cabeza quieta."""
    cuadro = int(fase * len(RECORRIDO_MIRADA)) % len(RECORRIDO_MIRADA)
    return {
        "mirada": RECORRIDO_MIRADA[cuadro],
        **({"ojos": "parpadeo"} if cuadro == 3 else {}),
        "cabeza": {"rot": (12 if animo == "triste" else -4, 0, 4)},
        "antebrazo.R": {"rot": (-25, 0, 0)},
        "antebrazo.L": {"rot": (-25, 0, 0)},
    }


def hablar(fase: float, animo: str) -> Pose:
    """Abre y cierra la boca como si hablara, gesticulando con la cabeza y un brazo."""
    angulo = fase * 2 * pi
    cuadro = int(fase * 8) % 8
    triste = animo == "triste"
    return {
        # La boca se abre en cuadros alternos y parpadea una vez por ciclo.
        "boca": "sonrisa_abierta" if cuadro % 2 == 0 else None,
        **({"ojos": "parpadeo"} if cuadro == 5 else {}),
        "raiz": {"lift": 0.01 * abs(sin(angulo * 2))},
        "cabeza": {"rot": ((12 if triste else -6) + 4 * sin(angulo * 2), 10 * sin(angulo), 6 * sin(angulo))},
        "brazo.R": {"rot": (-20 - 15 * max(sin(angulo), 0), 0, 15)},
        "antebrazo.R": {"rot": (-50 - 20 * max(sin(angulo), 0), 0, 0)},
        "antebrazo.L": {"rot": (-25, 0, 0)},
        "cola": {"rot": (0, 0, 8 * sin(angulo))},
    }


def retrato(fase: float, animo: str) -> Pose:
    """Pose neutra de frente, con la cabeza un poco ladeada, para mostrar la cara."""
    return {
        "cabeza": {"rot": (-4, 0, 6)},
        "antebrazo.R": {"rot": (-25, 0, 0)},
        "antebrazo.L": {"rot": (-25, 0, 0)},
    }


# ---------------------------------------------------------------- gestos
# Los brazos de Nailong son cortos: la mano llega a la panza, a los cachetes y
# justo por encima de los hombros, no más. Estos ángulos se buscaron midiendo
# dónde queda la mano. Se escriben para el brazo izquierdo; espejo() da el derecho.

MANOS_PANZA = ((-20, 0, 60), (0, 0, -20))
MANOS_CACHETES = ((-80, 0, -100), (0, 0, -20))
MANOS_ARRIBA = ((-120, 0, 50), (0, 0, -20))
MANOS_SORPRESA = ((-60, 0, -70), (-40, 0, -30))
MANOS_ABAJO_ATRAS = ((25, 0, -10), (-10, 0, 0))
MANOS_ESTIRADAS = ((-110, 0, 30), (-10, 0, 0))
MANOS_HURRA = ((-30, 0, -90), (0, 0, -30))
MANOS_ESCONDIDAS = ((60, 0, -105), (0, 0, -60))
MANOS_APLAUSO_ABIERTAS = ((-90, 0, -90), (0, 0, 0))
MANOS_APLAUSO_JUNTAS = ((-120, 0, -90), (0, 0, -30))


def espejo(rotacion):
    x, y, z = rotacion
    return (x, -y, -z)


def brazos(postura, mezcla: float = 1.0) -> Pose:
    """Pone los dos brazos en una postura, mezclándola con la de reposo (0 a 1)."""
    (brazo, antebrazo) = postura
    reposo_antebrazo = (-25, 0, 0)
    brazo = tuple(v * mezcla for v in brazo)
    antebrazo = tuple(r + (v - r) * mezcla for v, r in zip(antebrazo, reposo_antebrazo))
    return {
        "brazo.L": {"rot": brazo},
        "antebrazo.L": {"rot": antebrazo},
        "brazo.R": {"rot": espejo(brazo)},
        "antebrazo.R": {"rot": espejo(antebrazo)},
    }


def un_brazo(lado: str, postura, mezcla: float) -> Pose:
    """Como brazos(), pero solo para el brazo de un lado ("L" o "R")."""
    pose = brazos(postura, mezcla)
    return {hueso: valores for hueso, valores in pose.items() if hueso.endswith(lado)}


def mezclar_brazos(desde, hasta, t: float) -> Pose:
    """Pasa los dos brazos de una postura a otra (t de 0 a 1)."""
    postura = tuple(tuple(a + (b - a) * t for a, b in zip(p, q)) for p, q in zip(desde, hasta))
    return brazos(postura)


def reir(fase: float, animo: str) -> Pose:
    """Carcajada: se agarra la panza, echa la cabeza atrás y rebota."""
    angulo = fase * 2 * pi
    rebote = abs(sin(angulo * 2))
    return {
        "cara": "risa",
        "boca": "risa" if int(fase * 8) % 2 == 0 else "sonrisa_abierta",
        "raiz": {"lift": 0.035 * rebote},
        "cuerpo": {"rot": (-6, 0, 4 * sin(angulo * 2)), "escala": (1 + 0.02 * (1 - rebote), 1 - 0.03 * (1 - rebote), 1 + 0.02 * (1 - rebote))},
        "cabeza": {"rot": (-12 + 4 * sin(angulo * 2), 0, 6 * sin(angulo))},
        **brazos(MANOS_PANZA),
        "cola": {"rot": (0, 0, 15 * sin(angulo * 2))},
    }


def sorprenderse(fase: float, animo: str) -> Pose:
    """Brinca del susto con los brazos arriba y se queda con la boca abierta."""
    if fase < 0.125:
        return {"cabeza": {"rot": (-4, 0, 0)}, **brazos(MANOS_SORPRESA, 0)}
    salto = max(0.0, sin((fase - 0.125) / 0.5 * pi)) if fase < 0.625 else 0.0
    mezcla = min(1.0, (fase - 0.125) / 0.125)
    return {
        "cara": "sorprendido",
        "raiz": {"lift": 0.12 * salto},
        "cuerpo": {"rot": (-10 * mezcla, 0, 0), "escala": (1 - 0.03 * salto, 1 + 0.05 * salto, 1 - 0.03 * salto)},
        "cabeza": {"rot": (-12 * mezcla, 0, 0)},
        **brazos(MANOS_SORPRESA, mezcla),
        "pierna.R": {"rot": (-15 * salto, 0, 0)},
        "pierna.L": {"rot": (-15 * salto, 0, 0)},
        "cola": {"rot": (0, 0, 0)},
    }


def enojarse(fase: float, animo: str) -> Pose:
    """Patalea con los brazos tiesos hacia atrás, la cabeza gacha y temblando de rabia."""
    angulo = fase * 2 * pi
    temblor = sin(angulo * 4)
    return {
        "cara": "enojado",
        "raiz": {"lift": 0.02 * abs(sin(angulo))},
        "cuerpo": {"rot": (8, 0, 3 * temblor)},
        "cabeza": {"rot": (6, 4 * temblor, 0)},
        **brazos(MANOS_ABAJO_ATRAS),
        "pierna.R": {"rot": (-20 * max(0, sin(angulo)), 0, 0), "lift": -0.06 * max(0, sin(angulo))},
        "pierna.L": {"rot": (-20 * max(0, -sin(angulo)), 0, 0), "lift": -0.06 * max(0, -sin(angulo))},
        "cola": {"rot": (0, 0, 20 * temblor)},
    }


def celebrar(fase: float, animo: str) -> Pose:
    """Salta de alegría con las manos arriba."""
    angulo = fase * 2 * pi
    salto = abs(sin(angulo))
    return {
        "cara": "emocionado" if salto > 0.5 else "alegre",
        "raiz": {"lift": 0.12 * salto},
        "cuerpo": {"rot": (-4, 0, 0), "escala": (1 + 0.04 * (1 - salto), 1 - 0.06 * (1 - salto) + 0.04 * salto, 1 + 0.04 * (1 - salto))},
        "cabeza": {"rot": (-10, 0, 5 * sin(angulo * 2))},
        **brazos(MANOS_ARRIBA, 0.6 + 0.4 * salto),
        "pierna.R": {"rot": (-25 * salto, 0, 0)},
        "pierna.L": {"rot": (-25 * salto, 0, 0)},
        "cola": {"rot": (0, 0, 20 * sin(angulo * 2))},
    }


def bostezar(fase: float, animo: str) -> Pose:
    """Se estira con los brazos arriba, bosteza y termina parpadeando de sueño."""
    estiramiento = sin(min(fase / 0.75, 1.0) * pi)
    return {
        "cara": "cansado",
        "ojos": "parpadeo" if fase < 0.75 else "dormidos",
        "boca": "bostezo" if 0.125 <= fase < 0.75 else "puchero",
        "cuerpo": {"rot": (-8 * estiramiento, 0, 0), "escala": (1 - 0.02 * estiramiento, 1 + 0.05 * estiramiento, 1 - 0.02 * estiramiento)},
        "cabeza": {"rot": (-16 * estiramiento + 6 * (1 - estiramiento), 0, 4 * estiramiento)},
        **brazos(MANOS_ESTIRADAS, estiramiento),
    }


def avergonzarse(fase: float, animo: str) -> Pose:
    """Baja la cabeza sonrojado, junta las manos al frente y se balancea."""
    angulo = fase * 2 * pi
    return {
        "cara": "avergonzado",
        "cuerpo": {"rot": (4, 0, 4 * sin(angulo))},
        "cabeza": {"rot": (14, 15, 8 + 3 * sin(angulo))},
        **brazos(MANOS_PANZA),
        "pierna.R": {"rot": (0, 0, 0), "lift": -0.02 * max(0, sin(angulo))},
        "cola": {"rot": (0, 0, 10 * sin(angulo))},
    }


def llorar(fase: float, animo: str) -> Pose:
    """Llora a moco tendido con las manos en los cachetes, sollozando."""
    angulo = fase * 2 * pi
    sollozo = abs(sin(angulo * 2))
    return {
        "cara": "llorando",
        "boca": "grito" if sollozo > 0.4 else "triste",
        "raiz": {"lift": 0.02 * sollozo},
        "cuerpo": {"rot": (2, 0, 3 * sin(angulo * 4))},
        "cabeza": {"rot": (-10 + 4 * sollozo, 0, 5 * sin(angulo))},
        **brazos(MANOS_CACHETES),
        "cola": {"rot": (0, 0, 5 * sin(angulo * 4))},
    }


# ---------------------------------------------------------------- acciones


def suave(t: float) -> float:
    """Curva que arranca y frena despacio entre 0 y 1, para que nada se mueva en seco."""
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def aplastar(cuanto: float) -> tuple[float, float, float]:
    """Escala del cuerpo que lo achata (positivo) o lo estira (negativo) sin cambiar su volumen."""
    alto = 1 - cuanto
    ancho = 1 / sqrt(alto)
    return (ancho, alto, ancho)


def gesto(fase: float, secuencia: list[dict]) -> dict:
    """Elige el gesto de la cara del cuadro actual dentro de una secuencia.

    Cada paso puede cambiar ánimo ("cara"), ojos, boca, mirada y extras, así
    la cara actúa junto con el cuerpo en vez de quedarse fija.
    """
    return dict(secuencia[int(fase * len(secuencia)) % len(secuencia)])


CARAS_CORRER = [
    {"cara": "emocionado", "boca": "sonrisa_abierta"},
    {"cara": "emocionado", "boca": "risa"},
    {"cara": "alegre"},
    {"cara": "emocionado", "boca": "risa", "mirada": "derecha"},
    {"cara": "emocionado", "boca": "sonrisa_abierta", "mirada": "derecha"},
    {"cara": "emocionado", "ojos": "parpadeo", "boca": "risa"},
    {"cara": "alegre", "extras": ["sudor"]},
    {"cara": "emocionado", "boca": "risa", "extras": ["sudor"]},
]


def correr(fase: float, animo: str) -> Pose:
    """Carrera: más inclinado y rápido que la caminata, con los dos pies en el aire en cada zancada.

    Los brazos van doblados en ángulo y bombean al revés de las piernas.
    """
    angulo = fase * 2 * pi
    paso = sin(angulo)
    pasada = cos(angulo)
    vuelo = abs(paso)
    return {
        **gesto(fase, CARAS_CORRER),
        "raiz": {"lift": 0.09 * vuelo},
        "cuerpo": {"rot": (18, 0, 6 * paso), "escala": aplastar(0.06 * (1 - vuelo) - 0.04 * vuelo)},
        "cabeza": {"rot": (-14, 6 * paso, -4 * paso)},
        "pierna.R": {"rot": (55 * paso + 80 * max(-pasada, 0), 0, 0), "lift": -0.14 * max(-pasada, 0)},
        "pierna.L": {"rot": (-55 * paso + 80 * max(pasada, 0), 0, 0), "lift": -0.14 * max(pasada, 0)},
        "brazo.R": {"rot": (-60 * paso, 0, 18)},
        "brazo.L": {"rot": (60 * paso, 0, -18)},
        "antebrazo.R": {"rot": (-75, 0, 0)},
        "antebrazo.L": {"rot": (-75, 0, 0)},
        "cola": {"rot": (-10, 0, 20 * paso)},
    }


def saltar(fase: float, animo: str) -> Pose:
    """Salto con preparación: se agacha, sale estirado, recoge las piernas arriba y cae aplastándose."""
    if fase < 0.2:  # se agacha para tomar impulso
        carga = suave(fase / 0.2)
        return {
            # Se concentra antes de saltar: aprieta los ojos y la boca.
            "cara": "feliz" if carga < 0.5 else "berrinche",
            "boca": "puchero",
            "raiz": {"lift": -0.06 * carga},
            "cuerpo": {"rot": (14 * carga, 0, 0), "escala": aplastar(0.1 * carga)},
            "cabeza": {"rot": (6 * carga, 0, 0)},
            "pierna.R": {"rot": (-30 * carga, 0, 0)},
            "pierna.L": {"rot": (-30 * carga, 0, 0)},
            **brazos(MANOS_ABAJO_ATRAS, carga),
            "cola": {"rot": (-10 * carga, 0, 0)},
        }
    if fase < 0.8:  # en el aire: sube estirado y recoge las piernas en lo alto
        t = (fase - 0.2) / 0.6
        altura = sin(t * pi)
        return {
            # En lo alto abre grande la boca y mira hacia arriba; al bajar ya sonríe.
            "cara": "emocionado" if altura > 0.8 else "alegre",
            "boca": "risa" if altura > 0.8 else "sonrisa_abierta",
            "mirada": "arriba" if t < 0.5 else "centro",
            "raiz": {"lift": 0.32 * altura},
            "cuerpo": {"rot": (-8 * altura, 0, 0), "escala": aplastar(-0.07 * (1 - altura) - 0.02)},
            "cabeza": {"rot": (-14 * altura, 0, 0)},
            "pierna.R": {"rot": (-45 * altura, 0, 0), "lift": -0.08 * altura},
            "pierna.L": {"rot": (-45 * altura, 0, 0), "lift": -0.08 * altura},
            **brazos(MANOS_HURRA, 0.5 + 0.5 * altura),
            "cola": {"rot": (20 * altura, 0, 0)},
        }
    caida = 1 - suave((fase - 0.8) / 0.2)  # aterriza aplastado y se recupera
    return {
        "cara": "risa" if caida > 0.5 else "contento",
        "raiz": {"lift": -0.05 * caida},
        "cuerpo": {"rot": (10 * caida, 0, 0), "escala": aplastar(0.1 * caida)},
        "cabeza": {"rot": (4 * caida, 0, 0)},
        "pierna.R": {"rot": (-25 * caida, 0, 0)},
        "pierna.L": {"rot": (-25 * caida, 0, 0)},
        **brazos(MANOS_SORPRESA, 0.4 * caida),
        "cola": {"rot": (-8 * caida, 0, 0)},
    }


def dormir(fase: float, animo: str) -> Pose:
    """Dormido sentado como en el sprite 2D: recostado, piernas al frente y la cabeza caída a un lado.

    Respira lento, y la cabeza cabecea un poco con cada respiración.
    """
    respiro = sin(fase * 2 * pi)
    return {
        "cara": "dormido",
        # La burbuja de la nariz se infla al soltar el aire y se desinfla al tomarlo.
        "boca": "bostezo" if 0.4 <= fase < 0.55 else "puchero" if respiro > 0 else "pequena",
        "objetos": ["burbuja_grande"] if respiro < -0.3 else ["burbuja_chica"] if respiro < 0.5 else [],
        "raiz": {"lift": -0.34},
        "cuerpo": {"rot": (-18 + 2 * respiro, 0, 0), "escala": aplastar(-0.025 * respiro)},
        # La cabeza cae hacia adelante y de lado, contra el recostado del cuerpo.
        "cabeza": {"rot": (16 + 4 * respiro, 10, 22 - 3 * respiro)},
        "pierna.R": {"rot": (-80, 0, -25)},
        "pierna.L": {"rot": (-80, 0, 25)},
        **brazos(MANOS_PANZA, 0.8),
        "cola": {"rot": (-30, 0, 25)},
    }


def escondido(fase: float, animo: str) -> Pose:
    """Camina de puntitas escondiendo algo detrás de la espalda, mirando a los lados con cara pícara."""
    angulo = fase * 2 * pi
    paso = sin(angulo)
    pasada = cos(angulo)
    mirando = pasada > 0.4 or pasada < -0.4
    return {
        # Ojea a un lado y al otro, como cuidando que nadie lo vea, nervioso; al
        # frente sonríe pícaro con la lengua de fuera.
        "cara": "nervioso" if mirando else "picaro",
        "boca": "lengua_lado" if mirando else None,
        "mirada": "derecha" if pasada > 0.4 else "izquierda" if pasada < -0.4 else "centro",
        "raiz": {"lift": 0.02 * abs(paso)},
        "cuerpo": {"rot": (12, 0, 4 * paso), "escala": aplastar(0.03)},
        "cabeza": {"rot": (8, 20 * pasada, -5 * paso)},
        # Pasos cortos y levantando mucho la rodilla, como quien no quiere hacer ruido.
        "pierna.R": {"rot": (20 * paso - 35 * max(-pasada, 0), 0, 0), "lift": -0.07 * max(-pasada, 0)},
        "pierna.L": {"rot": (-20 * paso - 35 * max(pasada, 0), 0, 0), "lift": -0.07 * max(pasada, 0)},
        **brazos(MANOS_ESCONDIDAS),
        "cola": {"rot": (0, 0, 10 * paso)},
    }


def saludar(fase: float, animo: str) -> Pose:
    """Saluda con la mano en alto moviéndola de lado a lado, como el sprite 2D de hola."""
    angulo = fase * 2 * pi
    vaiven = cos(angulo * 2)
    return {
        **gesto(fase, [
            {"cara": "feliz"}, {"cara": "feliz", "boca": "sonrisa_abierta"}, {"cara": "alegre"}, {"cara": "alegre"},
            {"cara": "emocionado"}, {"cara": "alegre"}, {"cara": "feliz", "ojos": "parpadeo"}, {"cara": "feliz", "boca": "sonrisa_abierta"},
        ]),
        "raiz": {"lift": 0.01 * abs(vaiven)},
        "cuerpo": {"rot": (-3, 0, -4)},
        "cabeza": {"rot": (-8, -12, 10 + 3 * vaiven)},
        "brazo.L": {"rot": (-30, 0, -90)},
        # El antebrazo es el que se mueve, de lado a lado sobre el codo.
        "antebrazo.L": {"rot": (-10, 0, -30 + 30 * vaiven)},
        "antebrazo.R": {"rot": (-25, 0, 0)},
        "cola": {"rot": (0, 0, 10 * vaiven)},
    }


def tocar_puerta(fase: float, animo: str) -> Pose:
    """Golpea la puerta dos veces con el puño a la altura de la cara y luego se queda escuchando."""
    golpe = fase < 0.5
    toque = max(0.0, -cos(fase * 8 * pi)) if golpe else 0.0
    escucha = suave((fase - 0.5) / 0.15) if not golpe else 0.0
    return {
        **gesto(fase, [
            {"cara": "feliz", "mirada": "derecha"}, {"cara": "feliz", "boca": "sonrisa_abierta", "mirada": "derecha"},
            {"cara": "feliz", "mirada": "derecha"}, {"cara": "alegre"},
            # Nadie abre: se queda escuchando, luego pone cara de "¿hola?".
            {"cara": "pensativo", "mirada": "arriba_derecha"}, {"cara": "pensativo", "ojos": "parpadeo"},
            {"cara": "incredulo"}, {"cara": "incredulo", "boca": "ondulada"},
        ]),
        "cuerpo": {"rot": (4 + 6 * toque, 0, 0)},
        "cabeza": {"rot": (-6 + 6 * escucha, 0, 4 + 12 * escucha)},
        # Golpea con el brazo izquierdo hacia adelante y un poco afuera, para que
        # en la vista de lado el puño se asome por delante del hocico, donde va
        # la puerta: dobla el codo y lo estira en cada toque.
        "brazo.L": {"rot": (-60 + 10 * toque + 30 * escucha, 0, -90)},
        "antebrazo.L": {"rot": (-80 + 80 * toque + 20 * escucha, 0, -30)},
        "antebrazo.R": {"rot": (-25, 0, 0)},
        "cola": {"rot": (0, 0, 6 * toque)},
    }


def bailar(fase: float, animo: str) -> Pose:
    """Baile de lado a lado: mece la cadera, sube un brazo y luego el otro, y la cabeza va al ritmo."""
    angulo = fase * 2 * pi
    lado = sin(angulo)
    rebote = abs(sin(angulo * 2))
    return {
        **gesto(fase, [
            {"cara": "contento"}, {"cara": "alegre"}, {"cara": "risa"}, {"cara": "travieso"},
            {"cara": "contento"}, {"cara": "alegre", "mirada": "izquierda"}, {"cara": "risa"}, {"cara": "picaro"},
        ]),
        "raiz": {"lift": 0.03 * rebote},
        "cuerpo": {"rot": (0, 15 * lado, 10 * lado), "escala": aplastar(0.04 * (1 - rebote))},
        "cabeza": {"rot": (-6 + 4 * rebote, -10 * lado, -14 * lado)},
        # Sube el brazo del lado hacia donde se mece y baja el otro.
        **un_brazo("L", MANOS_HURRA, max(lado, 0)),
        **un_brazo("R", MANOS_HURRA, max(-lado, 0)),
        "pierna.R": {"rot": (-30 * max(lado, 0), 0, 0), "lift": -0.05 * max(lado, 0)},
        "pierna.L": {"rot": (-30 * max(-lado, 0), 0, 0), "lift": -0.05 * max(-lado, 0)},
        "cola": {"rot": (0, 0, -25 * lado)},
    }


def aplaudir(fase: float, animo: str) -> Pose:
    """Aplaude emocionado frente al pecho dando saltitos."""
    angulo = fase * 2 * pi
    junta = abs(sin(angulo * 2))
    return {
        # Al juntar las manos cierra los ojos de gusto.
        "cara": "risa" if junta > 0.7 else "emocionado",
        "boca": "risa" if junta > 0.7 else "sonrisa_abierta",
        "raiz": {"lift": 0.03 * abs(sin(angulo))},
        "cuerpo": {"rot": (-2, 0, 0)},
        "cabeza": {"rot": (-10, 0, 5 * sin(angulo))},
        **mezclar_brazos(MANOS_APLAUSO_ABIERTAS, MANOS_APLAUSO_JUNTAS, junta),
        "cola": {"rot": (0, 0, 12 * sin(angulo * 2))},
    }


MANOS_COMER = ((-105, 0, -60), (0, 0, 0))
MANOS_LAVAR = ((-15, 0, 52), (0, 0, 15))
MANOS_PANZA_ARRIBA = ((-15, 0, 60), (-20, 0, 0))
MANOS_PANZA_ABAJO = ((0, 0, 60), (0, 0, 0))

# Comer como el sprite 2D: mira la galleta con antojo, abre la boca, la muerde
# y mastica con los ojitos cerrados de gusto.
CARAS_COMER = [
    {"cara": "antojado", "mirada": "abajo", "objetos": ["galleta"]},
    {"cara": "sorprendido", "boca": "bostezo", "mirada": "abajo", "objetos": ["galleta"]},
    {"cara": "burla", "boca": "dientes", "objetos": ["galleta_mordida"]},
    {"cara": "contento", "boca": "puchero", "objetos": ["galleta_mordida"]},
    {"cara": "contento", "boca": "ondulada", "objetos": ["galleta_mordida"]},
    {"cara": "contento", "boca": "puchero", "extras": ["sonrojo"], "objetos": ["galleta_mordida"]},
    {"cara": "contento", "boca": "gatuna", "extras": ["sonrojo"], "objetos": ["galleta_mordida"]},
    {"cara": "feliz", "mirada": "abajo", "objetos": ["galleta_mordida"]},
]


def comer(fase: float, animo: str) -> Pose:
    """Come una galleta con las dos manos: la cabeza baja a morder y luego mastica."""
    cuadro = int(fase * len(CARAS_COMER)) % len(CARAS_COMER)
    mordisco = 1.0 if cuadro in (1, 2) else 0.0
    masticar = sin(fase * 2 * pi * 4) if cuadro >= 3 else 0.0
    return {
        **gesto(fase, CARAS_COMER),
        "raiz": {"lift": 0.01 * abs(masticar)},
        "cuerpo": {"rot": (4 + 4 * mordisco, 0, 0), "escala": aplastar(0.02 * abs(masticar))},
        # Agacha la cabeza para morder y la mueve al masticar.
        "cabeza": {"rot": (-4 + 16 * mordisco + 3 * masticar, 0, 5 * masticar)},
        **brazos(MANOS_COMER),
        "cola": {"rot": (0, 0, 10 * masticar)},
    }


CARAS_LAVAR = [
    {"cara": "neutral", "mirada": "abajo", "boca": "puchero"},
    {"cara": "neutral", "mirada": "abajo", "boca": "lengua_lado"},
    {"cara": "neutral", "mirada": "abajo", "boca": "lengua_lado"},
    {"cara": "neutral", "ojos": "parpadeo", "boca": "puchero"},
    {"cara": "feliz", "mirada": "abajo", "boca": "puchero", "extras": ["sudor"]},
    {"cara": "neutral", "mirada": "abajo", "boca": "lengua_lado", "extras": ["sudor"]},
    {"cara": "orgulloso"},
    {"cara": "contento", "boca": "sonrisa_abierta"},
]


def lavar_ropa(fase: float, animo: str) -> Pose:
    """Restriega la ropa en la tina, agachado, concentrado con la lengua de fuera."""
    angulo = fase * 2 * pi
    restriega = sin(angulo * 2)
    brazo_l, antebrazo_l = MANOS_LAVAR
    pose = {
        **gesto(fase, CARAS_LAVAR),
        "objetos": ["tina", "ropa", "espuma_a" if restriega > 0 else "espuma_b"],
        "raiz": {"lift": 0.01 * abs(restriega)},
        "cuerpo": {"rot": (25, 0, 4 * restriega)},
        "cabeza": {"rot": (6 - 14 * (fase >= 0.75), 0, 4 * restriega)},
        # Las manos van y vienen al revés una de la otra sobre la ropa.
        "brazo.L": {"rot": (brazo_l[0] - 18 * restriega, 0, brazo_l[2])},
        "antebrazo.L": {"rot": antebrazo_l},
        "brazo.R": {"rot": espejo((brazo_l[0] + 18 * restriega, 0, brazo_l[2]))},
        "antebrazo.R": {"rot": espejo(antebrazo_l)},
        "pierna.R": {"rot": (-10, 0, 8)},
        "pierna.L": {"rot": (-10, 0, -8)},
        "cola": {"rot": (10, 0, 12 * restriega)},
    }
    return pose


CARAS_BARRIGA = [
    {"cara": "contento"},
    {"cara": "contento", "boca": "gatuna", "extras": ["sonrojo"]},
    {"cara": "tierno", "ojos": "felices"},
    {"cara": "dormido", "boca": "pequena", "extras": ["sonrojo"]},
    {"cara": "contento", "boca": "sonrisa_abierta"},
    {"cara": "feliz", "mirada": "abajo"},
    {"cara": "feliz", "ojos": "parpadeo", "mirada": "abajo"},
    {"cara": "alegre"},
]


def barriga(fase: float, animo: str) -> Pose:
    """Satisfecho después de comer: se soba la barriga en círculos, echado hacia atrás."""
    angulo = fase * 2 * pi
    vuelta = sin(angulo * 2)
    # Las manos dan vueltas sobre la panza, cada una a destiempo de la otra.
    arriba_l = 0.5 + 0.5 * vuelta
    arriba_r = 0.5 - 0.5 * vuelta
    def mano(t):
        return tuple(tuple(a + (b - a) * t for a, b in zip(p, q)) for p, q in zip(MANOS_PANZA_ABAJO, MANOS_PANZA_ARRIBA))
    (brazo_l, antebrazo_l), (brazo_r, antebrazo_r) = mano(arriba_l), mano(arriba_r)
    return {
        **gesto(fase, CARAS_BARRIGA),
        "raiz": {"lift": 0.01 * abs(sin(angulo))},
        # Se echa para atrás sacando la panza, que se infla un poco.
        "cuerpo": {"rot": (-8, 0, 4 * sin(angulo)), "escala": (1.04, 0.99, 1.04)},
        "cabeza": {"rot": (-10, 6 * sin(angulo), 8 * sin(angulo))},
        "brazo.L": {"rot": brazo_l},
        "antebrazo.L": {"rot": antebrazo_l},
        "brazo.R": {"rot": espejo(brazo_r)},
        "antebrazo.R": {"rot": espejo(antebrazo_r)},
        "cola": {"rot": (0, 0, 10 * sin(angulo))},
    }


MANOS_ESCRIBIR = ((-15, 0, 60), (0, 0, 0))
MANOS_LEER = ((-105, 0, -60), (0, 0, 0))
MANOS_PINTAR = ((-60, 0, 15), (-20, 0, -30))
MANOS_REGAR = ((0, 0, 30), (-40, 0, 0))
MANOS_RODILLAS = ((-30, 0, 30), (-20, 0, 0))


def sentado(inclinacion: float = 0.0) -> Pose:
    """Base para las acciones sentado en el piso: piernas al frente, espalda derecha."""
    return {
        "raiz": {"lift": -0.34},
        "cuerpo": {"rot": (inclinacion, 0, 0)},
        "pierna.R": {"rot": (-82, 0, -14)},
        "pierna.L": {"rot": (-82, 0, 14)},
        "cola": {"rot": (-30, 0, 20)},
    }


# La cabeza casi no gira hacia el lienzo: girada, los ojos se aplastan y se ve
# adormilado. El cuerpo se voltea apenas hacia el caballete y son los ojos los
# que miran; la lengua sale al centro, que a este tamaño se lee mejor.
CARAS_DIBUJAR = [
    {"cara": "neutral", "mirada": "derecha", "boca": "lengua", "objetos": ["pintura_1"]},
    {"cara": "neutral", "mirada": "derecha", "boca": "lengua", "objetos": ["pintura_1"]},
    {"cara": "feliz", "mirada": "derecha", "objetos": ["pintura_2"]},
    {"cara": "neutral", "mirada": "derecha", "boca": "lengua", "objetos": ["pintura_2"]},
    {"cara": "neutral", "ojos": "parpadeo", "boca": "lengua", "objetos": ["pintura_3"]},
    {"cara": "pensativo", "mirada": "derecha", "objetos": ["pintura_3"]},
    {"cara": "orgulloso", "objetos": ["pintura_3"]},
    {"cara": "alegre", "objetos": ["pintura_3"]},
]

# Posturas del brazo del pincel (izquierdo) y del de la paleta (derecho).
PINCEL_ARRIBA = ((-75, 0, 0), (0, 0, -30))
PINCEL_ABAJO = ((-30, 0, 0), (-40, 0, 0))
PINCEL_BARBILLA = ((-80, 0, -100), (0, 0, -20))
PALETA = ((-25, 0, 25), (-60, 0, 0))


def dibujar(fase: float, animo: str) -> Pose:
    """Pinta en el caballete volteado hacia él, con la paleta en la otra mano.

    Da pinceladas largas de arriba abajo mientras el cuadro se llena; luego da
    un paso atrás, lo mira con el pincel en la barbilla y lo alza orgulloso.
    """
    cuadro = int(fase * 8) % 8
    pinta = cuadro < 5
    # Pinceladas alternas: arriba en los cuadros pares, abajo en los impares.
    trazo = 1.0 if cuadro % 2 == 0 else 0.0
    piensa = 1.0 if cuadro == 5 else 0.0
    festeja = 1.0 if cuadro >= 6 else 0.0
    if pinta:
        brazo_pincel = mezclar_brazos(PINCEL_ABAJO, PINCEL_ARRIBA, trazo)
    elif piensa:
        brazo_pincel = brazos(PINCEL_BARBILLA)
    else:
        brazo_pincel = brazos(MANOS_HURRA)
    cara = gesto(fase, CARAS_DIBUJAR)
    cara["objetos"] = ["caballete", "pincel", "paleta", *cara["objetos"]]
    return {
        **cara,
        "raiz": {"lift": 0.03 * (cuadro == 7)},
        # Volteado hacia el caballete mientras pinta; al admirar se echa atrás y
        # vuelve el cuerpo hacia el jugador.
        "cuerpo": {"rot": (6 - 14 * (1 - pinta), -8 * pinta - 8 * piensa, -4 * pinta)},
        "cabeza": {"rot": (-2 - 8 * (1 - pinta), 4 * pinta, 4 * trazo * pinta - 6 * piensa)},
        **{hueso: valores for hueso, valores in brazo_pincel.items() if hueso.endswith("L")},
        **un_brazo("R", PALETA, 1.0),
        "pierna.R": {"rot": (8 * (1 - pinta), 0, 0)},
        "pierna.L": {"rot": (-8 * (1 - pinta), 0, 0)},
        "cola": {"rot": (0, 0, 10 * trazo * pinta + 20 * festeja)},
    }


CARAS_ESCRIBIR = [
    {"cara": "pensativo", "mirada": "arriba_izquierda", "objetos": []},
    {"cara": "pensativo", "mirada": "arriba", "objetos": []},
    {"cara": "feliz", "objetos": []},
    {"cara": "neutral", "mirada": "abajo", "boca": "lengua_lado", "objetos": ["renglones_1"]},
    {"cara": "neutral", "mirada": "abajo", "boca": "puchero", "objetos": ["renglones_2"]},
    {"cara": "neutral", "ojos": "parpadeo", "boca": "puchero", "objetos": ["renglones_2"]},
    {"cara": "neutral", "mirada": "abajo", "boca": "lengua_lado", "objetos": ["renglones_3"]},
    {"cara": "contento", "objetos": ["renglones_3"]},
]


def escribir(fase: float, animo: str) -> Pose:
    """Sentado con la libreta en las piernas: piensa, se le ocurre algo y escribe."""
    angulo = fase * 2 * pi
    cuadro = int(fase * 8) % 8
    escribe = cuadro in (3, 4, 6)
    trazo = sin(angulo * 6) if escribe else 0.0
    piensa = 1.0 if cuadro < 2 else 0.0
    cara = gesto(fase, CARAS_ESCRIBIR)
    cara["objetos"] = ["libreta", "lapiz", *cara["objetos"]]
    brazo, antebrazo = MANOS_ESCRIBIR
    return {
        **cara,
        **sentado(10 - 6 * piensa),
        "cabeza": {"rot": (14 - 22 * piensa, 10 * piensa, 6 * trazo + 8 * piensa)},
        # Mientras piensa se rasca la cabeza con el lápiz; al escribir lo mueve de lado a lado.
        "brazo.L": {"rot": (-100, 0, -95) if piensa else (brazo[0], 0, brazo[2] + 8 * trazo)},
        "antebrazo.L": {"rot": (-60, 0, -30) if piensa else antebrazo},
        **un_brazo("R", MANOS_ESCRIBIR, 1.0),
    }


CARAS_LEER = [
    {"cara": "neutral", "mirada": "abajo_izquierda", "objetos": ["pagina_der"]},
    {"cara": "neutral", "mirada": "abajo", "objetos": ["pagina_der"]},
    {"cara": "neutral", "mirada": "abajo_derecha", "objetos": ["pagina_der"]},
    {"cara": "sorprendido", "boca": "pequena", "mirada": "abajo_derecha", "objetos": ["pagina_der"]},
    {"cara": "risa", "objetos": ["pagina_der"]},
    {"cara": "alegre", "objetos": ["pagina_medio"]},
    {"cara": "neutral", "mirada": "abajo_izquierda", "objetos": ["pagina_izq"]},
    {"cara": "neutral", "ojos": "parpadeo", "objetos": ["pagina_izq"]},
]


def leer(fase: float, animo: str) -> Pose:
    """Sentado leyendo: los ojos recorren la página, algo le da risa y pasa la hoja."""
    cuadro = int(fase * 8) % 8
    risa = 1.0 if cuadro == 4 else 0.0
    cara = gesto(fase, CARAS_LEER)
    cara["objetos"] = ["libro", *cara["objetos"]]
    return {
        **cara,
        **sentado(4 - 6 * risa),
        "raiz": {"lift": -0.34 + 0.02 * risa},
        "cabeza": {"rot": (12 - 16 * risa, 0, 3 * (cuadro % 3 - 1) + 6 * risa)},
        **brazos(MANOS_LEER),
        "cola": {"rot": (-30, 0, 20 + 15 * risa)},
    }


CARAS_ESPERAR = [
    {"cara": "neutral"},
    {"cara": "neutral", "mirada": "izquierda"},
    {"cara": "neutral", "mirada": "derecha"},
    {"cara": "inexpresivo"},
    {"cara": "cansado"},
    {"cara": "enfurrunado"},
    {"cara": "neutral", "ojos": "parpadeo", "boca": "ondulada"},
    {"cara": "pensativo", "mirada": "arriba_izquierda"},
]


def esperar(fase: float, animo: str) -> Pose:
    """Sentado esperando: balancea los pies, mira a los lados, bosteza y se aburre."""
    angulo = fase * 2 * pi
    cuadro = int(fase * 8) % 8
    balanceo = sin(angulo * 2)
    bostezo = 1.0 if cuadro == 4 else 0.0
    mira = {1: 25, 2: -25}.get(cuadro, 0)
    return {
        **gesto(fase, CARAS_ESPERAR),
        **sentado(-4 * bostezo),
        "cabeza": {"rot": (4 - 14 * bostezo + 8 * (cuadro == 5), mira, 6 * balanceo + 10 * (cuadro == 5))},
        # Balancea los pies uno y otro, como quien no tiene nada que hacer.
        "pierna.R": {"rot": (-82 + 14 * balanceo, 0, -14)},
        "pierna.L": {"rot": (-82 - 14 * balanceo, 0, 14)},
        **(brazos(MANOS_ESTIRADAS, 0.6) if bostezo else brazos(MANOS_RODILLAS)),
        "cola": {"rot": (-30, 0, 20 + 10 * balanceo)},
    }


CARAS_CULTIVAR = [
    {"cara": "feliz", "mirada": "abajo_derecha", "objetos": ["brote"]},
    {"cara": "contento", "objetos": ["brote", "gotas_a"]},
    {"cara": "feliz", "mirada": "abajo_derecha", "objetos": ["brote", "gotas_b"]},
    {"cara": "feliz", "mirada": "abajo_derecha", "objetos": ["planta", "gotas_a"]},
    {"cara": "sorprendido", "mirada": "abajo_derecha", "objetos": ["planta", "gotas_b"]},
    {"cara": "emocionado", "mirada": "abajo_derecha", "objetos": ["planta"]},
    {"cara": "emocionado", "objetos": ["flor"]},
    {"cara": "enamorado", "objetos": ["flor"]},
]


def cultivar(fase: float, animo: str) -> Pose:
    """Riega una maceta y la planta crece hasta dar flor; se emociona al verla."""
    cuadro = int(fase * 8) % 8
    riega = cuadro in (1, 2, 3, 4)
    vaiven = sin(fase * 2 * pi * 4) if riega else 0.0
    festeja = 1.0 if cuadro >= 6 else 0.0
    cara = gesto(fase, CARAS_CULTIVAR)
    cara["objetos"] = ["maceta", "regadera", *cara["objetos"]]
    brazo, antebrazo = MANOS_REGAR
    return {
        **cara,
        "raiz": {"lift": 0.03 * festeja * (cuadro == 7)},
        "cuerpo": {"rot": (10 - 12 * festeja, 0, -6)},
        "cabeza": {"rot": (14 - 20 * festeja, -15, 6 * vaiven - 8 * festeja)},
        # Al regar sube el brazo y la regadera se inclina sobre la maceta.
        "brazo.L": {"rot": (brazo[0] - (30 + 6 * vaiven) * riega, 0, brazo[2])},
        "antebrazo.L": {"rot": antebrazo},
        **un_brazo("R", MANOS_CACHETES, festeja),
        "cola": {"rot": (0, 0, 6 * vaiven + 18 * festeja)},
    }


# Brazos abiertos como en la foto del fantasma: uno en alto haciendo "¡bu!" y
# el otro de lado con la cubeta de dulces.
MANOS_CUBETA = ((0, 0, -75), (-20, 0, 60))
MANOS_BU = ((0, 0, -90), (-20, 0, 30))

CARAS_TRUCO = [
    {"cara": "feliz"}, {"cara": "alegre"}, {"cara": "risa"}, {"cara": "alegre"},
    {"cara": "travieso"}, {"cara": "alegre"}, {"cara": "feliz", "ojos": "parpadeo"}, {"cara": "emocionado"},
]


def truco_o_trato(fase: float, animo: str) -> Pose:
    """Pide dulces con la cubeta de calabaza: se mece y agita el brazo libre."""
    angulo = fase * 2 * pi
    meneo = sin(angulo * 2)
    cara = gesto(fase, CARAS_TRUCO)
    cara["objetos"] = ["cubeta"]
    brazo_bu, antebrazo_bu = MANOS_BU
    return {
        **cara,
        "raiz": {"lift": 0.02 * abs(meneo)},
        "cuerpo": {"rot": (0, 0, 6 * meneo)},
        "cabeza": {"rot": (-6, 0, 8 * meneo)},
        "brazo.L": {"rot": MANOS_CUBETA[0]},
        "antebrazo.L": {"rot": MANOS_CUBETA[1]},
        "brazo.R": {"rot": espejo((brazo_bu[0], 0, brazo_bu[2] + 15 * meneo))},
        "antebrazo.R": {"rot": espejo((antebrazo_bu[0] - 15 * meneo, 0, antebrazo_bu[2]))},
        "pierna.R": {"rot": (-10 * max(meneo, 0), 0, 0), "lift": -0.03 * max(meneo, 0)},
        "pierna.L": {"rot": (-10 * max(-meneo, 0), 0, 0), "lift": -0.03 * max(-meneo, 0)},
        "cola": {"rot": (0, 0, 20 * meneo)},
    }

# Brazos abiertos sosteniendo la capa, como en la foto del vampiro.
MANOS_CAPA = ((-25, 0, -90), (-10, 0, -20))


def capa_abierta(fase: float, animo: str) -> Pose:
    """El vampiro abre la capa de golpe y se ríe con los colmillos de fuera."""
    angulo = fase * 2 * pi
    cuadro = int(fase * 8) % 8
    abre = min(1.0, cuadro / 2)
    risa = sin(angulo * 2)
    return {
        **gesto(fase, [
            {"cara": "vampiro", "boca": "colmillos"}, {"cara": "vampiro", "boca": "colmillos"},
            {"cara": "vampiro"}, {"cara": "vampiro", "mirada": "centro"},
            {"cara": "vampiro", "ojos": "felices"}, {"cara": "vampiro", "ojos": "felices"},
            {"cara": "vampiro", "mirada": "izquierda"}, {"cara": "vampiro", "ojos": "parpadeo"},
        ]),
        "raiz": {"lift": 0.015 * abs(risa) * abre},
        "cuerpo": {"rot": (-4 * abre, 0, 3 * risa * abre)},
        "cabeza": {"rot": (-8 * abre, -10, 6 * risa * abre)},
        **brazos(MANOS_CAPA, abre),
        "pierna.R": {"rot": (-8 * abre, 0, -4)},
        "cola": {"rot": (0, 0, 15 * risa)},
    }

def regar(fase: float, animo: str) -> Pose:
    """Riega con la regadera sin maceta propia, para el huerto del juego que ya dibuja sus plantas."""
    pose = cultivar(fase, animo)
    pose["objetos"] = [objeto for objeto in pose["objetos"] if objeto in ("regadera", "gotas_a", "gotas_b")]
    if pose.get("cara") == "enamorado":
        pose["cara"] = "alegre"
    return pose

ANIMACIONES = {
    "quieto": quieto,
    "caminar": caminar,
    "mirar": mirar,
    "hablar": hablar,
    "ojear": ojear,
    "retrato": retrato,
    "reir": reir,
    "sorprenderse": sorprenderse,
    "enojarse": enojarse,
    "celebrar": celebrar,
    "bostezar": bostezar,
    "avergonzarse": avergonzarse,
    "llorar": llorar,
    "correr": correr,
    "saltar": saltar,
    "dormir": dormir,
    "escondido": escondido,
    "saludar": saludar,
    "tocar_puerta": tocar_puerta,
    "bailar": bailar,
    "aplaudir": aplaudir,
    "comer": comer,
    "lavar_ropa": lavar_ropa,
    "barriga": barriga,
    "dibujar": dibujar,
    "escribir": escribir,
    "leer": leer,
    "esperar": esperar,
    "cultivar": cultivar,
    "truco_o_trato": truco_o_trato,
    "capa_abierta": capa_abierta,
    "regar": regar,
}
