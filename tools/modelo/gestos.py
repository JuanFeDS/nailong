"""Catálogo de expresiones de Nailong: ojos, bocas y emociones.

Los ojos y la boca miden pocos píxeles, así que no salen del sombreado 3D:
el modelo solo marca dónde va cada uno y aquí se dibujan con reglas de
píxeles, como en los sprites hechos a mano. Cada dibujo recibe la región que
ocupa en el cuadro y la pinta; lo que no usa vuelve a ser piel.

Una emoción es una combinación de ojos, boca y extras 3D (párpados, lágrimas,
sonrojo, sudor). La mirada mueve las pupilas dentro de los ojos sin mover la
cabeza. Agregar un gesto nuevo es agregar su dibujo aquí.
"""

from collections import Counter
from collections.abc import Callable

import numpy as np

from paleta import a_rgb

Region = set[tuple[int, int]]

COLORES = {
    "borde": "#1b2317",
    "iris": "#5f9e54",
    "iris_claro": "#72c85c",
    "iris_oscuro": "#315a2c",
    "brillo": "#f5f4eb",
    "blanco": "#f5f4eb",
    # Colores de la boca abierta del sprite 2D de saludo: línea gris arriba,
    # como la sonrisa, e interior suave color durazno. Nada oscuro ni saturado:
    # con gris alrededor parecía labios pintados, con café chocolate y con rojo labial.
    "linea": "#697661",
    "labio": "#e26721",
    "interior": "#f19f5f",
    "lengua": "#f89f94",
    # La lengua afuera va un poco más intensa para que se vea sobre la piel.
    "lengua_afuera": "#f0644d",
    "lengua_brillo": "#f89f94",
    "diente": "#fceab7",
    # Fondo de la boca bien abierta: más oscuro que el interior durazno para
    # que la sonrisa grande se lea contra la piel amarilla.
    "garganta": "#a8402e",
    "corazon": "#c83630",
    "corazon_claro": "#f89f94",
    "agua": "#73eff7",
}


class Lienzo:
    """Ayuda a dibujar sobre una región: conoce su caja y el color de la piel alrededor."""

    def __init__(self, salida: np.ndarray, pixeles: Region):
        self.salida = salida
        self.pixeles = pixeles
        filas = [y for y, _ in pixeles]
        columnas = [x for _, x in pixeles]
        self.arriba, self.abajo = min(filas), max(filas)
        self.izquierda, self.derecha = min(columnas), max(columnas)
        self.ancho = self.derecha - self.izquierda + 1
        self.alto = self.abajo - self.arriba + 1
        # La piel es el color más común en el anillo de píxeles que rodea la
        # región; un solo píxel de referencia puede caer en un contorno cuando
        # la cabeza está girada y manchar el ojo cerrado.
        alto, ancho = salida.shape[:2]
        anillo = {
            (y + dy, x + dx) for y, x in pixeles for dy in (-1, 0, 1) for dx in (-1, 0, 1)
            if 0 <= y + dy < alto and 0 <= x + dx < ancho
        } - set(pixeles)
        colores = Counter(tuple(salida[y, x, :3]) for y, x in anillo if salida[y, x, 3])
        centro = (self.izquierda + self.derecha) // 2
        respaldo = tuple(salida[max(self.arriba - 1, 0), centro, :3])
        self.piel = np.array(colores.most_common(1)[0][0] if colores else respaldo, dtype=salida.dtype)

    def borrar(self):
        """Devuelve toda la región al color de la piel."""
        for y, x in self.pixeles:
            self.salida[y, x, :3] = self.piel

    def poner(self, y: int, x: int, color: str):
        alto, ancho = self.salida.shape[:2]
        if 0 <= y < alto and 0 <= x < ancho and self.salida[y, x, 3]:
            self.salida[y, x, :3] = a_rgb(COLORES[color])

    def fila(self, y: int, desde: int, hasta: int, color: str):
        for x in range(desde, hasta + 1):
            self.poner(y, x, color)


# ---------------------------------------------------------------- ojos
# Cada dibujo de ojo recibe el lado en pantalla (-1 izquierdo, 1 derecho) para
# los gestos asimétricos como el guiño o las cejas.


# Hacia dónde miran las pupilas, en píxeles de pantalla: (horizontal, vertical).
MIRADAS = {
    "centro": (0, 0),
    "izquierda": (-1, 0),
    "derecha": (1, 0),
    "arriba": (0, -1),
    "abajo": (0, 1),
    "arriba_izquierda": (-1, -1),
    "arriba_derecha": (1, -1),
    "abajo_izquierda": (-1, 1),
    "abajo_derecha": (1, 1),
}


def ojo_abierto(lienzo: Lienzo, lado: int, brillos: int = 1, mirada: str = "centro"):
    """El ojo de los sprites 2D: borde arriba, pupila con brillo, iris verde y base oscura.

    La pupila se corre dentro del ojo según la mirada, y el brillo la acompaña,
    así el personaje puede mirar a un lado sin mover la cabeza.
    """
    c = lienzo
    dx, dy = MIRADAS[mirada]
    centro = (c.izquierda + c.derecha) / 2
    pupila = {int(np.floor(centro - 0.5)), int(np.floor(centro + 0.5))} if c.ancho >= 4 else {round(centro)}
    corrimiento = max(c.izquierda - min(pupila), min(dx, c.derecha - max(pupila)))
    pupila = {x + corrimiento for x in pupila}
    alto_pupila = max(c.abajo - 2 - c.arriba, 1)
    tope = min(max(c.arriba + 1 + dy, c.arriba + 1), c.abajo - alto_pupila)
    filas_pupila = set(range(tope, tope + alto_pupila))
    columna_brillo = max(pupila) + 1 if max(pupila) + 1 <= c.derecha else min(pupila) - 1
    filas_brillo = {tope, tope + 1}
    # Asoma el blanco del ojo del lado contrario a donde mira; de frente, del
    # lado de afuera de la cara, como en las referencias.
    lado_blanco = -dx if dx else lado
    columna_blanco = c.izquierda if lado_blanco < 0 else c.derecha
    filas_blanco = set(range(c.arriba + 1, c.abajo - 1)) if c.ancho >= 4 and c.alto >= 4 else set()
    for y, x in c.pixeles:
        esquina = x in (c.izquierda, c.derecha) and c.ancho >= 4
        if y == c.arriba:
            color = "iris_oscuro" if esquina else "borde"
        elif x == columna_blanco and y in filas_blanco and x not in pupila:
            color = "blanco"
        elif y == c.abajo and c.alto >= 4:
            color = "iris_oscuro"
        elif x == columna_brillo and y in filas_brillo and c.alto >= 4:
            color = "brillo"
        elif x in pupila and y in filas_pupila:
            color = "borde"
        elif y == c.abajo - 1 and c.alto >= 4:
            color = "iris_claro"
        elif x in (c.izquierda, c.derecha):
            color = "iris_oscuro"
        else:
            color = "iris"
        c.poner(y, x, color)
    if brillos > 1:
        # Ojos brillantes de emoción: un segundo brillo abajo, del otro lado de la pupila.
        x = min(pupila) - 1 if columna_brillo > max(pupila) else max(pupila) + 1
        c.poner(c.abajo - 1, min(max(x, c.izquierda), c.derecha), "brillo")


def ojos_abiertos(c: Lienzo, lado: int, mirada: str = "centro"):
    ojo_abierto(c, lado, mirada=mirada)


def ojos_brillantes(c: Lienzo, lado: int, mirada: str = "centro"):
    ojo_abierto(c, lado, brillos=2, mirada=mirada)


def ojos_felices(c: Lienzo, lado: int, mirada: str = "centro"):
    """Cerrados de felicidad: un arco como ^."""
    c.borrar()
    medio = (c.arriba + c.abajo) // 2
    c.fila(medio, c.izquierda + 1, c.derecha - 1, "borde")
    c.poner(medio + 1, c.izquierda, "borde")
    c.poner(medio + 1, c.derecha, "borde")


def ojos_parpadeo(c: Lienzo, lado: int, mirada: str = "centro"):
    """Cerrados al parpadear: una línea recta."""
    c.borrar()
    c.fila((c.arriba + c.abajo + 1) // 2, c.izquierda, c.derecha, "borde")


def ojos_dormidos(c: Lienzo, lado: int, mirada: str = "centro"):
    """Cerrados y relajados: un arco hacia abajo como ‿."""
    c.borrar()
    medio = (c.arriba + c.abajo + 1) // 2
    c.fila(medio, c.izquierda + 1, c.derecha - 1, "borde")
    c.poner(medio - 1, c.izquierda, "borde")
    c.poner(medio - 1, c.derecha, "borde")


def ojos_apretados(c: Lienzo, lado: int, mirada: str = "centro"):
    """Apretados con fuerza: > en el ojo izquierdo y < en el derecho."""
    c.borrar()
    medio = (c.arriba + c.abajo) // 2
    pasos = max(medio - c.arriba, 1)
    # Cada flecha se pega al lado de adentro de su ojo, hacia el centro de la
    # cara; pegadas al lado de afuera los ojos se ven muy separados.
    for fila in range(c.arriba, c.abajo + 1):
        avance = pasos - abs(fila - medio)
        x = c.derecha - pasos + avance if lado < 0 else c.izquierda + pasos - avance
        c.poner(fila, x, "borde")


def ojos_sorprendidos(c: Lienzo, lado: int, mirada: str = "centro"):
    """Muy abiertos: blancos, con la pupila pequeña y un borde oscuro."""
    for y, x in c.pixeles:
        borde = y in (c.arriba, c.abajo) or x in (c.izquierda, c.derecha)
        esquina = y in (c.arriba, c.abajo) and x in (c.izquierda, c.derecha)
        c.poner(y, x, "iris_oscuro" if esquina else "borde" if borde else "blanco")
    # El ojo crece un píxel hacia arriba para verse más abierto.
    c.fila(c.arriba - 1, c.izquierda + 1, c.derecha - 1, "borde")
    c.fila(c.arriba, c.izquierda + 1, c.derecha - 1, "blanco")
    dx, dy = MIRADAS[mirada]
    x = min(max((c.izquierda + c.derecha) // 2 + dx, c.izquierda + 1), c.derecha - 1)
    y = min(max((c.arriba + c.abajo) // 2 + dy, c.arriba), c.abajo - 1)
    c.poner(y, x, "borde")


def ojos_enojados(c: Lienzo, lado: int, mirada: str = "centro"):
    """Ojo abierto con el párpado cortado en diagonal y una ceja que baja hacia el centro."""
    ojo_abierto(c, lado, mirada=mirada)
    interior = c.derecha if lado < 0 else c.izquierda
    paso = -1 if lado < 0 else 1
    # El corte del párpado: tapa la esquina de arriba hacia el centro de la cara.
    c.poner(c.arriba, interior, "borde")
    c.poner(c.arriba + 1, interior, "borde")
    c.poner(c.arriba, interior + paso, "borde")
    # Ceja inclinada: alta afuera y baja adentro.
    for i in range(c.ancho):
        x = interior + paso * i
        c.poner(c.arriba - 1 - (i * 2) // max(c.ancho - 1, 1), x, "borde")


def ojos_corazon(c: Lienzo, lado: int, mirada: str = "centro"):
    """Corazones rojos de enamorado."""
    c.borrar()
    ancho = max(c.ancho, 5)
    alto = max(c.alto, 5)
    izquierda = (c.izquierda + c.derecha) // 2 - ancho // 2
    arriba = c.arriba - (alto - c.alto) // 2
    for fila in range(alto):
        for columna in range(ancho):
            x = (columna + 0.5) / ancho * 2.4 - 1.2
            y = 1.1 - (fila + 0.5) / alto * 2.4
            if (x * x + y * y - 1) ** 3 - x * x * y**3 <= 0:
                color = "corazon_claro" if (fila, columna) == (1, 1) else "corazon"
                c.poner(arriba + fila, izquierda + columna, color)


def ojos_mareados(c: Lienzo, lado: int, mirada: str = "centro"):
    """Una X en cada ojo."""
    c.borrar()
    lado_x = min(c.ancho, c.alto) - 1
    for i in range(lado_x + 1):
        c.poner(c.arriba + i, c.izquierda + i, "borde")
        c.poner(c.arriba + i, c.izquierda + lado_x - i, "borde")


def ojos_llorosos(c: Lienzo, lado: int, mirada: str = "centro"):
    """Abiertos, brillantes y con agua acumulada abajo."""
    ojo_abierto(c, lado, brillos=2, mirada=mirada)
    c.fila(c.abajo, c.izquierda, c.derecha, "agua")


def ojos_guino(c: Lienzo, lado: int, mirada: str = "centro"):
    """Guiño: el ojo izquierdo abierto y el derecho cerrado de felicidad."""
    if lado < 0:
        ojo_abierto(c, lado, mirada=mirada)
    else:
        ojos_felices(c, lado)


def ojos_locos(c: Lienzo, lado: int, mirada: str = "centro"):
    """Ojos desviados, cada uno mirando para otro lado: uno arriba y otro de costado."""
    ojo_abierto(c, lado, mirada="arriba_izquierda" if lado < 0 else "derecha")


def ojos_arriba(c: Lienzo, lado: int, mirada: str = "centro"):
    """Mirando hacia arriba, pensativo."""
    ojo_abierto(c, lado, mirada="arriba")


def ojos_abajo(c: Lienzo, lado: int, mirada: str = "centro"):
    """Mirando hacia abajo con timidez: la pupila baja y el borde de arriba se engrosa."""
    ojo_abierto(c, lado, mirada="abajo")
    c.fila(c.arriba + 1, c.izquierda + 1, c.derecha - 1, "borde")


def ojos_incredulos(c: Lienzo, lado: int, mirada: str = "arriba"):
    """Ojazos redondos y blancos con el iris chiquito pegado arriba, de incredulidad.

    Es la cara de "¿en serio?" de las referencias: todo el ojo blanco con un
    borde fino, y el iris verde con la pupila mirando hacia arriba.
    """
    # El ojo crece un píxel hacia arriba, como en sorprendidos, para verse redondo.
    arriba = c.arriba - 1
    for y in range(arriba, c.abajo + 1):
        for x in range(c.izquierda, c.derecha + 1):
            esquina = y in (arriba, c.abajo) and x in (c.izquierda, c.derecha)
            if esquina:
                continue
            borde = y in (arriba, c.abajo) or x in (c.izquierda, c.derecha)
            c.poner(y, x, "borde" if borde else "blanco")
    dx, dy = MIRADAS[mirada]
    centro = (c.izquierda + c.derecha) // 2 + max(-1, min(dx, 1))
    # Con la mirada arriba el iris toca el borde de arriba; si no, queda al centro.
    fila = arriba + 1 if dy < 0 else (arriba + c.abajo) // 2
    # Iris redondo: una fila con la pupila al centro y el aro verde a los lados,
    # y debajo la curva del aro, dejando ver el blanco a los costados.
    for x in range(centro - 1, centro + 2):
        if c.izquierda < x < c.derecha:
            c.poner(fila, x, "borde" if x == centro else "iris")
    if fila + 1 < c.abajo:
        c.poner(fila + 1, centro, "iris")


OJOS: dict[str, Callable[..., None]] = {
    "abiertos": ojos_abiertos,
    "brillantes": ojos_brillantes,
    "felices": ojos_felices,
    "parpadeo": ojos_parpadeo,
    "dormidos": ojos_dormidos,
    "apretados": ojos_apretados,
    "sorprendidos": ojos_sorprendidos,
    "enojados": ojos_enojados,
    "corazon": ojos_corazon,
    "mareados": ojos_mareados,
    "llorosos": ojos_llorosos,
    "guino": ojos_guino,
    "locos": ojos_locos,
    "arriba": ojos_arriba,
    "abajo": ojos_abajo,
    "incredulos": ojos_incredulos,
}


# ---------------------------------------------------------------- bocas


def boca_sonrisa(c: Lienzo):
    """Línea gris con las puntas un píxel más arriba."""
    c.borrar()
    c.fila(c.abajo, c.izquierda + 1, c.derecha - 1, "linea")
    c.poner(c.abajo - 1, c.izquierda, "linea")
    c.poner(c.abajo - 1, c.derecha, "linea")


def boca_pequena(c: Lienzo):
    """Boquita en reposo: un pliegue corto, como en las referencias."""
    c.borrar()
    centro = (c.izquierda + c.derecha) // 2
    c.fila(c.arriba + 1, centro - 1, centro + 1, "linea")


def boca_mohin(c: Lienzo):
    """Boquita fruncida hacia abajo, de enfurruñado."""
    c.borrar()
    centro = (c.izquierda + c.derecha) // 2
    c.fila(c.arriba + 1, centro - 1, centro + 1, "linea")
    c.poner(c.arriba + 2, centro - 2, "linea")
    c.poner(c.arriba + 2, centro + 2, "linea")


def boca_triste(c: Lienzo):
    """Línea gris con las puntas un píxel más abajo."""
    c.borrar()
    c.fila(c.arriba, c.izquierda + 1, c.derecha - 1, "linea")
    c.poner(c.arriba + 1, c.izquierda, "linea")
    c.poner(c.arriba + 1, c.derecha, "linea")


def boca_sonrisa_abierta(c: Lienzo):
    """Sonrisa con la boca abierta: puntas arriba, interior oscuro y lengua abajo.

    Las filas se cuentan desde arriba porque la marca de la boca es muy baja y
    la boca abierta necesita bajar más allá de ella.
    """
    c.borrar()
    i, d, y = c.izquierda, c.derecha, c.arriba
    c.poner(y, i, "linea")
    c.poner(y, d, "linea")
    c.fila(y + 1, i + 1, d - 1, "interior")
    c.fila(y + 2, i + 2, d - 2, "interior")
    c.fila(y + 2, i + 3, d - 3, "lengua")
    c.fila(y + 3, i + 2, d - 2, "labio")


def boca_risa(c: Lienzo):
    """Carcajada: una D con la parte de arriba recta, interior oscuro y la lengua abajo.

    Termina en la lengua rosada y no en una línea: así no baja hasta la sombra
    de la barbilla, donde lo oscuro se leería como barba.
    """
    c.borrar()
    i, d, y = c.izquierda, c.derecha, c.arriba
    c.fila(y, i, d, "linea")
    c.fila(y + 1, i, d, "interior")
    c.fila(y + 2, i + 1, d - 1, "interior")
    c.fila(y + 3, i + 2, d - 2, "lengua")


def boca_sorpresa(c: Lienzo):
    """Una O pequeña y redonda."""
    c.borrar()
    centro = (c.izquierda + c.derecha) // 2
    c.fila(c.arriba, centro - 1, centro, "linea")
    c.fila(c.arriba + 1, centro - 1, centro, "interior")
    c.poner(c.arriba + 1, centro - 2, "labio")
    c.poner(c.arriba + 1, centro + 1, "labio")
    c.fila(c.arriba + 2, centro - 1, centro, "labio")


def boca_grito(c: Lienzo):
    """Boca muy abierta hacia abajo, de llanto o susto: una D al revés."""
    c.borrar()
    i, d, y = c.izquierda, c.derecha, c.arriba
    c.fila(y, i + 2, d - 2, "linea")
    c.fila(y + 1, i + 1, d - 1, "interior")
    c.fila(y + 2, i, d, "interior")
    c.fila(y + 3, i + 1, d - 1, "lengua")
    c.poner(y + 3, i, "labio")
    c.poner(y + 3, d, "labio")


def boca_dientes(c: Lienzo):
    """Sonrisa amplia mostrando los dientes."""
    c.borrar()
    i, d, y = c.izquierda, c.derecha, c.arriba
    c.poner(y, i, "linea")
    c.poner(y, d, "linea")
    c.fila(y + 1, i + 1, d - 1, "diente")
    c.poner(y + 1, i, "labio")
    c.poner(y + 1, d, "labio")
    c.fila(y + 2, i + 1, d - 1, "labio")


def boca_gatuna(c: Lienzo):
    """Boca de gatito, como ω."""
    c.borrar()
    centro = (c.izquierda + c.derecha) // 2
    for x in (c.izquierda, centro, c.derecha):
        c.poner(c.abajo - 1, x, "linea")
    for x in (c.izquierda + 1, centro - 1 if centro - 1 > c.izquierda else centro, centro + 1, c.derecha - 1):
        c.poner(c.abajo, x, "linea")


def boca_lengua(c: Lienzo):
    """Sonrisa con la lengua afuera: redondeada, con una rayita al centro."""
    boca_sonrisa(c)
    centro = (c.izquierda + c.derecha) // 2
    y = c.abajo + 1
    c.fila(y, centro - 1, centro + 1, "lengua_afuera")
    c.poner(y, centro - 1, "lengua_brillo")
    c.fila(y + 1, centro - 1, centro + 1, "lengua_afuera")
    c.poner(y + 1, centro, "labio")
    c.poner(y + 2, centro, "lengua_afuera")


def boca_lengua_grande(c: Lienzo):
    """Boca muy abierta con los dientes de arriba y la lengua colgando, como en la referencia."""
    c.borrar()
    i, d, y = c.izquierda, c.derecha, c.arriba
    centro = (i + d) // 2
    c.fila(y, i + 1, d - 1, "linea")
    c.fila(y + 1, i, d, "diente")
    c.fila(y + 2, i, d, "interior")
    for fila, (desde, hasta) in enumerate([(centro - 2, centro + 2), (centro - 2, centro + 2), (centro - 2, centro + 2), (centro - 1, centro + 1)]):
        c.fila(y + 2 + fila, desde, hasta, "lengua_afuera")
    c.poner(y + 3, centro - 1, "lengua_brillo")
    c.poner(y + 3, centro, "labio")
    c.poner(y + 4, centro, "labio")


def boca_lengua_lado(c: Lienzo):
    """Sonrisa con la lengua asomando por un costado."""
    boca_sonrisa(c)
    x = c.derecha - 1
    c.fila(c.abajo + 1, x - 1, x, "lengua_afuera")
    c.poner(c.abajo + 1, x - 1, "lengua_brillo")
    c.poner(c.abajo + 2, x, "lengua_afuera")


def boca_ondulada(c: Lienzo):
    """Boca nerviosa en zigzag."""
    c.borrar()
    for i, x in enumerate(range(c.izquierda, c.derecha + 1)):
        c.poner(c.abajo - (i % 2), x, "linea")


def boca_enojada(c: Lienzo):
    """Boca apretada de enojo: línea recta con las puntas hacia abajo."""
    c.borrar()
    c.fila(c.arriba + 1, c.izquierda + 1, c.derecha - 1, "linea")
    c.poner(c.abajo, c.izquierda, "linea")
    c.poner(c.abajo, c.derecha, "linea")


def boca_puchero(c: Lienzo):
    """Boca chiquita y fruncida."""
    c.borrar()
    centro = (c.izquierda + c.derecha) // 2
    c.fila(c.abajo, centro - 1, centro, "linea")


def boca_colmillos(c: Lienzo):
    """Sonrisa de vampiro: la sonrisa de siempre con dos colmillos blancos colgando."""
    boca_sonrisa(c)
    centro = (c.izquierda + c.derecha) // 2
    for x in (centro - 1, centro + 1):
        c.poner(c.abajo + 1, x, "diente")


def boca_sonrisa_grande(c: Lienzo):
    """Sonrisota en D con la boca bien abierta, como en las fotos del personaje.

    Es más ancha que la marca de la boca: las comisuras suben un píxel por
    fuera, arriba queda el fondo oscuro y abajo la lengua rosada.
    """
    c.borrar()
    i, d, y = c.izquierda, c.derecha, c.arriba
    c.poner(y, i - 1, "linea")
    c.poner(y, d + 1, "linea")
    c.fila(y, i, d, "garganta")
    c.poner(y + 1, i, "garganta")
    c.poner(y + 1, d, "garganta")
    c.fila(y + 1, i + 1, d - 1, "lengua")
    c.fila(y + 2, i + 1, d - 1, "lengua")
    c.fila(y + 3, i + 2, d - 2, "labio")


def boca_vampiro(c: Lienzo):
    """Sonrisota de vampiro, con un colmillo blanco colgando en cada esquina."""
    boca_sonrisa_grande(c)
    c.poner(c.arriba, c.izquierda, "diente")
    c.poner(c.arriba, c.derecha, "diente")


def boca_bostezo(c: Lienzo):
    """Bostezo: un óvalo alto y oscuro que crece hacia abajo."""
    c.borrar()
    centro = (c.izquierda + c.derecha) // 2
    c.fila(c.arriba, centro - 1, centro, "linea")
    for y in range(c.arriba + 1, c.arriba + 4):
        c.fila(y, centro - 1, centro, "interior")
        c.poner(y, centro - 2, "labio")
        c.poner(y, centro + 1, "labio")
    c.fila(c.arriba + 3, centro - 1, centro, "lengua")
    c.fila(c.arriba + 4, centro - 1, centro, "labio")


BOCAS: dict[str, Callable[[Lienzo], None]] = {
    "colmillos": boca_colmillos,
    "vampiro": boca_vampiro,
    "sonrisa_grande": boca_sonrisa_grande,
    "sonrisa": boca_sonrisa,
    "pequena": boca_pequena,
    "mohin": boca_mohin,
    "triste": boca_triste,
    "sonrisa_abierta": boca_sonrisa_abierta,
    "risa": boca_risa,
    "sorpresa": boca_sorpresa,
    "grito": boca_grito,
    "dientes": boca_dientes,
    "gatuna": boca_gatuna,
    "lengua": boca_lengua,
    "lengua_grande": boca_lengua_grande,
    "lengua_lado": boca_lengua_lado,
    "ondulada": boca_ondulada,
    "enojada": boca_enojada,
    "puchero": boca_puchero,
    "bostezo": boca_bostezo,
}


# ---------------------------------------------------------------- emociones
# Cada emoción combina ojos, boca y extras 3D. Una pose puede cambiar solo los
# ojos o solo la boca en un cuadro, por ejemplo para parpadear o hablar.

ANIMOS = {
    "neutral": {"ojos": "abiertos", "boca": "pequena", "extras": []},
    "inexpresivo": {"ojos": "abiertos", "boca": "pequena", "extras": [], "mirada": "arriba"},
    "murcielago": {"ojos": "abiertos", "boca": "colmillos", "extras": []},
    "vampiro": {"ojos": "abiertos", "boca": "vampiro", "extras": [], "mirada": "derecha"},
    "sonriente": {"ojos": "abiertos", "boca": "sonrisa_grande", "extras": [], "mirada": "arriba_derecha"},
    "incredulo": {"ojos": "incredulos", "boca": "mohin", "extras": [], "mirada": "arriba"},
    "enfurrunado": {"ojos": "abiertos", "boca": "mohin", "extras": [], "mirada": "arriba_derecha"},
    "loco": {"ojos": "locos", "boca": "lengua_grande", "extras": []},
    "feliz": {"ojos": "abiertos", "boca": "sonrisa", "extras": []},
    "contento": {"ojos": "felices", "boca": "sonrisa", "extras": []},
    "alegre": {"ojos": "felices", "boca": "sonrisa_abierta", "extras": ["sonrojo"]},
    "risa": {"ojos": "felices", "boca": "risa", "extras": ["sonrojo"]},
    "emocionado": {"ojos": "brillantes", "boca": "sonrisa_abierta", "extras": ["sonrojo"]},
    "orgulloso": {"ojos": "felices", "boca": "dientes", "extras": []},
    "enamorado": {"ojos": "corazon", "boca": "sonrisa", "extras": ["sonrojo"]},
    "tierno": {"ojos": "abiertos", "boca": "gatuna", "extras": ["sonrojo"]},
    "travieso": {"ojos": "guino", "boca": "lengua", "extras": []},
    "antojado": {"ojos": "brillantes", "boca": "lengua", "extras": []},
    "burla": {"ojos": "apretados", "boca": "lengua_grande", "extras": []},
    "picaro": {"ojos": "felices", "boca": "lengua_lado", "extras": ["sonrojo"]},
    "sorprendido": {"ojos": "sorprendidos", "boca": "sorpresa", "extras": []},
    "asustado": {"ojos": "sorprendidos", "boca": "ondulada", "extras": ["sudor"]},
    "nervioso": {"ojos": "abiertos", "boca": "ondulada", "extras": ["sudor"]},
    "pensativo": {"ojos": "arriba", "boca": "puchero", "extras": []},
    "avergonzado": {"ojos": "abajo", "boca": "ondulada", "extras": ["sonrojo"]},
    "triste": {"ojos": "abiertos", "boca": "triste", "extras": ["parpados", "lagrima"]},
    "conmovido": {"ojos": "llorosos", "boca": "sonrisa", "extras": ["sonrojo"]},
    "llorando": {"ojos": "apretados", "boca": "grito", "extras": ["lagrimas"]},
    "enojado": {"ojos": "enojados", "boca": "enojada", "extras": []},
    "berrinche": {"ojos": "apretados", "boca": "enojada", "extras": ["sonrojo"]},
    "cansado": {"ojos": "parpadeo", "boca": "bostezo", "extras": []},
    "dormido": {"ojos": "dormidos", "boca": "puchero", "extras": []},
    "mareado": {"ojos": "mareados", "boca": "ondulada", "extras": []},
}


def resolver(animo: str, ojos: str | None = None, boca: str | None = None, mirada: str | None = None) -> dict:
    """Devuelve la combinación del ánimo, con ojos, boca o mirada cambiados si se piden."""
    eleccion = dict(ANIMOS[animo])
    eleccion["ojos"] = ojos or eleccion["ojos"]
    eleccion["boca"] = boca or eleccion["boca"]
    eleccion["mirada"] = mirada or eleccion.get("mirada", "centro")
    return eleccion


def dibujar_ojos(salida: np.ndarray, regiones: list[Region], forma: str, mirada: str = "centro"):
    """Dibuja los ojos, sabiendo cuál queda a la izquierda y cuál a la derecha en pantalla."""
    ordenadas = sorted(regiones, key=lambda region: min(x for _, x in region))
    for indice, region in enumerate(ordenadas):
        lado = -1 if indice == 0 and len(ordenadas) > 1 else 1
        OJOS[forma](Lienzo(salida, region), lado, mirada)


def dibujar_boca(salida: np.ndarray, regiones: list[Region], forma: str):
    """Dibuja la boca con todas las formas empezando en la misma línea.

    La marca de la boca es más alta de lo que mide una boca cerrada, para dejar
    sitio a las abiertas, y su borde de arriba queda a la altura de los ojos.
    Por eso todas las bocas arrancan en su penúltima fila, un píxel bajo los
    ojos como en los sprites 2D, y las abiertas crecen hacia abajo desde ahí.
    """
    for region in regiones:
        lienzo = Lienzo(salida, region)
        lienzo.arriba = lienzo.abajo - 1
        lienzo.alto = 2
        BOCAS[forma](lienzo)
