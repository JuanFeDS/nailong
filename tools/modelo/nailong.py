"""Construye el modelo 3D de Nailong en Blender: cuerpo, esqueleto y ranuras.

El cuerpo es una superficie definida por sus siluetas: el ancho visto de
frente y cuánto sobresale hacia adelante y hacia atrás visto de perfil, a cada
altura. La cabeza es un óvalo aparte, alargado hacia adelante, apoyado sobre
el cuerpo como en los sprites 2D. El esqueleto deforma el cuerpo. Brazos, piernas y cola son
volúmenes suaves que se funden como plastilina (metaballs). Las garras, las
variantes de ojos y boca y las prendas son piezas aparte pegadas a un hueso,
que se muestran u ocultan según la combinación pedida.

Medidas en unidades de Blender: Z hacia arriba, Nailong mira hacia -Y y los
pies tocan Z = 0. La altura total ronda las 2 unidades.
"""

from dataclasses import dataclass, field
from math import cos, pi, radians, sin, sqrt

import bpy
import numpy as np
from mathutils import Euler, Matrix, Vector


@dataclass
class Modelo:
    """Referencias al modelo construido que necesitan el render y las poses."""

    esqueleto: bpy.types.Object
    # Extras 3D de la cara (párpados, lágrimas, sonrojo, sudor), cada uno con sus piezas.
    extras: dict[str, list[bpy.types.Object]] = field(default_factory=dict)
    prendas: dict[str, list[bpy.types.Object]] = field(default_factory=dict)
    # Objetos que una acción saca en escena: comida, ropa para lavar, la tina...
    objetos: dict[str, list[bpy.types.Object]] = field(default_factory=dict)
    crestas: list[bpy.types.Object] = field(default_factory=list)
    # La cabeza con sus marcas de ojos y boca, para esconderla bajo la sábana.
    cabeza: list[bpy.types.Object] = field(default_factory=list)


# Disfraces que tapan la cabeza: con ellos las crestas se esconden, si no las
# atravesarían. La sábana del fantasma tapa la cabeza entera, que se esconde.
TAPAN_CRESTAS = {"calabaza", "fantasma", "murcielago", "spiderman", "pollito"}
TAPAN_CABEZA = {"fantasma", "spiderman"}


# Cada material lleva un color plano único que el render usa como identificador.
# La paleta final de cada material vive en paleta.py, no aquí.
MATERIALES = [
    "piel",
    "panza",
    "palma",
    "garra",
    "ojo",
    "boca",
    "parpado",
    "lagrima",
    "mejilla",
    "sudor",
    "cresta",
    "gorra",
    "visera",
    "galleta",
    "ropa",
    "tina",
    "agua",
    "espuma",
    "papel",
    "lapiz",
    "libro",
    "madera",
    "maceta",
    "planta",
    "regadera",
    "morado",
    "negro",
    "calabaza",
    "sabana",
    "rojo",
    "dorado",
    "cobija",
    "azul",
    "pollo",
]

HUESOS = {
    # nombre: (cabeza, cola, padre)
    "raiz": ((0, 0, 0), (0, 0, 0.3), None),
    "cuerpo": ((0, 0, 0.3), (0, 0, 0.99), "raiz"),
    "cabeza": ((0, -0.08, 0.99), (0, -0.08, 1.76), "cuerpo"),
    "brazo.R": ((-0.37, -0.04, 0.77), (-0.51, -0.15, 0.64), "cuerpo"),
    "brazo.L": ((0.37, -0.04, 0.77), (0.51, -0.15, 0.64), "cuerpo"),
    "antebrazo.R": ((-0.51, -0.15, 0.64), (-0.58, -0.36, 0.58), "brazo.R"),
    "antebrazo.L": ((0.51, -0.15, 0.64), (0.58, -0.36, 0.58), "brazo.L"),
    "pierna.R": ((-0.21, 0, 0.46), (-0.23, -0.02, 0.04), "raiz"),
    "pierna.L": ((0.21, 0, 0.46), (0.23, -0.02, 0.04), "raiz"),
    "cola": ((0, 0.26, 0.42), (0, 0.84, 0.28), "cuerpo"),
}

# Siluetas del cuerpo: (altura, medio ancho de frente, hacia adelante, hacia atrás).
# Por encima de la última fila el cuerpo se cierra en una cúpula, escondida
# dentro de la cabeza.
PERFIL = [
    # El cuerpo termina por encima del suelo para que se vean las piernas.
    (0.28, 0.28, 0.25, 0.24),
    (0.36, 0.37, 0.34, 0.32),
    (0.48, 0.41, 0.39, 0.35),
    (0.63, 0.42, 0.39, 0.35),
    (0.78, 0.4, 0.36, 0.33),
    # Hombros caídos: el cuerpo se afina hacia la cabeza en vez de terminar plano.
    (0.88, 0.35, 0.33, 0.3),
    (0.95, 0.28, 0.29, 0.26),
]
ALTO_CUPULA = 0.2
# Exponente de la sección: 2 es una elipse; más alto la hace más cuadrada.
REDONDEZ = 2.15

# Cabeza: una sola superficie lisa. De frente es redonda; de perfil es un
# frijol, con un hocico que sobresale hacia adelante bajo los ojos y una frente
# que se recoge hacia arriba. Su parte baja queda sobre el cuerpo y dibuja la
# barbilla en U. (altura, medio ancho de frente, hacia adelante, hacia atrás).
PERFIL_CABEZA = [
    (0.86, 0.0, 0.0, 0.0),
    (0.9, 0.28, 0.3, 0.24),
    (0.97, 0.39, 0.46, 0.34),
    (1.05, 0.44, 0.57, 0.39),
    (1.13, 0.465, 0.62, 0.42),
    (1.2, 0.475, 0.62, 0.44),
    (1.28, 0.475, 0.56, 0.45),
    (1.36, 0.465, 0.5, 0.45),
    (1.45, 0.44, 0.46, 0.44),
    (1.54, 0.39, 0.41, 0.4),
    (1.62, 0.31, 0.33, 0.32),
    (1.68, 0.2, 0.21, 0.2),
    (1.71, 0.0, 0.0, 0.0),
]
FILAS, COLUMNAS = 90, 64

# Extremidades como volúmenes que se funden: (centro, radios, rotación en grados).
# Brazos cortos y gruesos que salen justo bajo la cabeza, en dos piezas que se
# doblan en el codo, con la mano hacia adelante para que se vean la palma rosada
# y las garras. Las dos piezas comparten una bola en el codo para que no se abra
# un hueco al doblarlo.
CODO = Vector((0.51, -0.15, 0.64))
BRAZO = [
    ((0.37, -0.04, 0.77), (0.13, 0.13, 0.13), (0, 0, 0)),
    ((0.45, -0.09, 0.7), (0.125, 0.125, 0.13), (-20, 35, 0)),
    (tuple(CODO), (0.115, 0.115, 0.115), (0, 0, 0)),
]
ANTEBRAZO = [
    (tuple(CODO), (0.115, 0.115, 0.115), (0, 0, 0)),
    ((0.55, -0.22, 0.6), (0.115, 0.125, 0.11), (-50, 20, 0)),
    ((0.57, -0.3, 0.58), (0.115, 0.105, 0.105), (0, 0, 0)),
]
# Centro de la mano; los dedos apuntan desde el codo hacia aquí.
MANO = Vector((0.57, -0.3, 0.58))
# Piernas cortas y gruesas, separadas, que asoman bajo la panza como en los sprites 2D.
PIERNA = [
    ((0.21, -0.01, 0.37), (0.19, 0.2, 0.15), (0, 0, 0)),
    ((0.22, -0.02, 0.19), (0.165, 0.175, 0.15), (0, 0, 0)),
    ((0.23, -0.08, 0.06), (0.18, 0.24, 0.07), (0, 0, 0)),
]
# Cola de dinosaurio: gruesa en la base, sale casi horizontal hacia atrás y se
# afina en cuatro tramos hasta una punta que sube un poco.
COLA = [
    ((0, 0.3, 0.4), (0.17, 0.2, 0.15), (15, 0, 0)),
    ((0, 0.48, 0.33), (0.12, 0.17, 0.1), (8, 0, 0)),
    ((0, 0.65, 0.28), (0.075, 0.13, 0.065), (0, 0, 0)),
    ((0, 0.8, 0.28), (0.035, 0.09, 0.032), (-12, 0, 0)),
]

# Crestitas verdes en fila por detrás de la cabeza, de arriba hacia la nuca:
# (altura donde van, radios a lo ancho, a lo largo y de grosor).
CRESTAS = [
    (1.52, (0.06, 0.07, 0.045)),
    (1.35, (0.068, 0.08, 0.05)),
    (1.18, (0.065, 0.075, 0.048)),
]

RESOLUCION = 0.02
# Radio de la superficie de un metaball respecto a su radio de influencia.
ALCANCE_METABALL = 0.575


def color_identificador(indice: int) -> tuple[float, float, float, float]:
    """Devuelve un color plano distinto para cada material, legible tras el render.

    El rojo distingue hasta 16 materiales; el verde dice en qué tanda de 16 va,
    así caben más sin que dos colores queden tan cerca que se confundan.
    """
    return ((indice % 16 + 1) * 12 / 255, (indice // 16) * 0.3, 0.0, 1.0)


def crear_materiales() -> dict[str, bpy.types.Material]:
    materiales = {}
    for indice, nombre in enumerate(MATERIALES):
        material = bpy.data.materials.new(nombre)
        material.diffuse_color = color_identificador(indice)
        materiales[nombre] = material
    return materiales


def elipsoide(nombre, centro, radios, material=None, rotacion=(0, 0, 0), segmentos=32):
    """Crea un elipsoide suave con las transformaciones ya aplicadas."""
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segmentos, ring_count=segmentos // 2)
    objeto = bpy.context.object
    objeto.name = nombre
    objeto.scale = radios
    objeto.rotation_euler = [radians(angulo) for angulo in rotacion]
    objeto.location = centro
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.shade_smooth()
    if material:
        objeto.data.materials.append(material)
    return objeto


def orientado(nombre, centro, radios, normal, material, giro=0.0):
    """Crea un elipsoide cuyo eje Z sigue la normal de la superficie."""
    objeto = elipsoide(nombre, (0, 0, 0), radios, material)
    rotacion = Vector(normal).to_track_quat("Z", "Y").to_matrix().to_4x4()
    objeto.data.transform(Matrix.Translation(centro) @ rotacion @ Matrix.Rotation(radians(giro), 4, "Z"))
    return objeto


def trazo(nombre, puntos, grosor, material):
    """Crea un trazo curvo con volumen, para bocas."""
    curva = bpy.data.curves.new(nombre, "CURVE")
    curva.dimensions = "3D"
    curva.bevel_depth = grosor
    curva.bevel_resolution = 2
    linea = curva.splines.new("BEZIER")
    linea.bezier_points.add(len(puntos) - 1)
    for punto, coordenada in zip(linea.bezier_points, puntos):
        punto.co = coordenada
        punto.handle_left_type = punto.handle_right_type = "AUTO"
    curva.materials.append(material)
    objeto = bpy.data.objects.new(nombre, curva)
    bpy.context.collection.objects.link(objeto)
    return objeto


def fundir(volumenes, nombre: str, espejo: int = 1) -> bpy.types.Object:
    """Funde los volúmenes (centro, radios, rotación) en una sola malla continua.

    Con espejo = -1 los refleja al otro lado, para la extremidad derecha.
    """
    datos = bpy.data.metaballs.new(nombre)
    datos.resolution = datos.render_resolution = RESOLUCION
    for (x, y, z), radios, (giro_x, giro_y, giro_z) in volumenes:
        elemento = datos.elements.new()
        elemento.type = "ELLIPSOID"
        elemento.co = (x * espejo, y, z)
        elemento.radius = max(radios) / ALCANCE_METABALL
        elemento.size_x, elemento.size_y, elemento.size_z = (radio / max(radios) for radio in radios)
        angulos = (giro_x, giro_y * espejo, giro_z * espejo)
        elemento.rotation = Euler([radians(angulo) for angulo in angulos]).to_quaternion()
    bola = bpy.data.objects.new(nombre, datos)
    bpy.context.collection.objects.link(bola)
    bpy.ops.object.select_all(action="DESELECT")
    bola.select_set(True)
    bpy.context.view_layer.objects.active = bola
    bpy.ops.object.convert(target="MESH")
    cuerpo = bpy.context.object
    cuerpo.name = nombre
    bpy.ops.object.shade_smooth()
    return cuerpo


def interpolar(alturas, valores, consultas):
    """Interpolación cúbica monótona (PCHIP): curvas suaves que no se pasan de largo."""
    alturas, valores = np.asarray(alturas, float), np.asarray(valores, float)
    pasos = np.diff(alturas)
    pendientes = np.diff(valores) / pasos
    derivadas = np.zeros_like(valores)
    for indice in range(1, len(valores) - 1):
        izquierda, derecha = pendientes[indice - 1], pendientes[indice]
        if izquierda * derecha > 0:
            peso_1 = 2 * pasos[indice] + pasos[indice - 1]
            peso_2 = pasos[indice] + 2 * pasos[indice - 1]
            derivadas[indice] = (peso_1 + peso_2) / (peso_1 / izquierda + peso_2 / derecha)
    tramo = np.clip(np.searchsorted(alturas, consultas) - 1, 0, len(pasos) - 1)
    t = (consultas - alturas[tramo]) / pasos[tramo]
    h = pasos[tramo]
    return (
        (2 * t**3 - 3 * t**2 + 1) * valores[tramo]
        + (t**3 - 2 * t**2 + t) * h * derivadas[tramo]
        + (-2 * t**3 + 3 * t**2) * valores[tramo + 1]
        + (t**3 - t**2) * h * derivadas[tramo + 1]
    )


def secciones() -> list[tuple[float, float, float, float]]:
    """Calcula ancho, frente y espalda en cada fila del cuerpo, cerrándolo en cúpula."""
    columnas = list(zip(*PERFIL))
    base, tope = PERFIL[0][0], PERFIL[-1][0]
    alto_cuerpo = tope - base
    total = alto_cuerpo + ALTO_CUPULA
    resultado = []
    for indice in range(FILAS):
        recorrido = indice / (FILAS - 1) * total
        if recorrido <= alto_cuerpo:
            z = base + recorrido
            ancho, frente, atras = (float(interpolar(columnas[0], columnas[k], np.array([z]))[0]) for k in (1, 2, 3))
        else:
            # La cúpula usa un cuarto de elipse para cerrar el cuerpo sin pico.
            angulo = (recorrido - alto_cuerpo) / ALTO_CUPULA * pi / 2
            z = tope + ALTO_CUPULA * sin(angulo)
            factor = cos(angulo)
            _, ancho, frente, atras = PERFIL[-1]
            ancho, frente, atras = ancho * factor, frente * factor, atras * factor
        resultado.append((z, ancho, frente, atras))
    return resultado


def superelipse(angulo: float, redondez: float) -> tuple[float, float]:
    coseno, seno = cos(angulo), sin(angulo)
    exponente = 2 / redondez
    return (
        (abs(coseno) ** exponente) * (1 if coseno >= 0 else -1),
        (abs(seno) ** exponente) * (1 if seno >= 0 else -1),
    )


def levantar(nombre: str, filas, redondez: float) -> bpy.types.Object:
    """Crea una malla cerrada a partir de secciones (altura, ancho, frente, espalda)."""
    vertices, caras = [], []
    for z, ancho, frente, atras in filas:
        for columna in range(COLUMNAS):
            x, y = superelipse(columna / COLUMNAS * 2 * pi, redondez)
            vertices.append((x * ancho, y * (atras if y > 0 else frente), z))
    for fila in range(len(filas) - 1):
        for columna in range(COLUMNAS):
            siguiente = (columna + 1) % COLUMNAS
            a, b = fila * COLUMNAS + columna, fila * COLUMNAS + siguiente
            caras.append((a, b, b + COLUMNAS, a + COLUMNAS))
    if filas[0][1] > 0:
        vertices.append((0, 0, filas[0][0] - 0.02))
        fondo = len(vertices) - 1
        caras += [((columna + 1) % COLUMNAS, columna, fondo) for columna in range(COLUMNAS)]

    malla = bpy.data.meshes.new(nombre)
    malla.from_pydata(vertices, [], caras)
    malla.validate()
    objeto = bpy.data.objects.new(nombre, malla)
    bpy.context.collection.objects.link(objeto)
    for poligono in malla.polygons:
        poligono.use_smooth = True
    malla.update()
    return objeto


def construir_tronco(materiales) -> bpy.types.Object:
    """Levanta el cuerpo fila por fila a partir de las siluetas y le pinta la panza."""
    tronco = levantar("tronco", secciones(), REDONDEZ)
    malla = tronco.data
    for nombre in ("piel", "panza"):
        malla.materials.append(materiales[nombre])
    for cara in malla.polygons:
        centro, normal = cara.center, cara.normal
        panza = (centro.x / 0.27) ** 2 + ((centro.z - 0.6) / 0.28) ** 2 < 1 and normal.y < -0.3
        cara.material_index = 1 if panza else 0
    return tronco


def construir_cabeza(materiales) -> bpy.types.Object:
    """Levanta la cabeza fila por fila a partir de su perfil, con la cúpula cerrada arriba y abajo."""
    alturas, anchos, frentes, atrases = (np.array(columna) for columna in zip(*PERFIL_CABEZA))
    # Más filas cerca de los extremos para que cierren redondos y no en punta.
    t = (1 - np.cos(np.linspace(0, pi, FILAS))) / 2
    consultas = alturas[0] + (alturas[-1] - alturas[0]) * t
    filas = [
        (float(z), float(a), float(f), float(b))
        for z, a, f, b in zip(
            consultas,
            interpolar(alturas, anchos, consultas),
            interpolar(alturas, frentes, consultas),
            interpolar(alturas, atrases, consultas),
        )
    ]
    cabeza = levantar("cabeza", filas, 2.0)
    cabeza.data.materials.append(materiales["piel"])
    return cabeza


def ejes_mano(lado: int) -> tuple[Vector, Vector, Vector, Vector]:
    """Centro de la mano, hacia dónde apuntan los dedos, hacia el costado y hacia la palma."""
    mano = Vector((MANO.x * lado, MANO.y, MANO.z))
    codo = Vector((CODO.x * lado, CODO.y, CODO.z))
    dedos = (mano - codo).normalized()
    costado = dedos.cross(Vector((0, 0, 1))).normalized()
    # La palma mira hacia abajo, un poco al frente y hacia el cuerpo, para que la
    # almohadilla rosada se vea desde el frente como en los sprites 2D.
    palma = Vector((-0.5 * lado, -0.5, -0.7)).normalized()
    return mano, dedos, costado, palma


def pintar_palma(antebrazo, materiales, lado: int):
    """Pinta la almohadilla rosada ovalada en la palma, del lado de abajo de la mano."""
    for nombre in ("piel", "palma"):
        antebrazo.data.materials.append(materiales[nombre])
    mano, dedos, _, palma = ejes_mano(lado)
    centro_almohadilla = mano + palma * 0.06 - dedos * 0.01
    for cara in antebrazo.data.polygons:
        cerca = (cara.center - centro_almohadilla).length < 0.075
        cara.material_index = 1 if cerca and cara.normal.dot(palma) > 0.35 else 0


def superficie(cuerpo, origen, direccion) -> tuple[Vector, Vector]:
    """Lanza un rayo contra el cuerpo y devuelve el punto y la normal donde choca."""
    acierto, punto, normal, _ = cuerpo.ray_cast(Vector(origen), Vector(direccion).normalized())
    if not acierto:
        raise ValueError(f"el rayo desde {origen} no toca el cuerpo")
    return punto, normal


def crear_esqueleto() -> bpy.types.Object:
    datos = bpy.data.armatures.new("esqueleto")
    esqueleto = bpy.data.objects.new("esqueleto", datos)
    bpy.context.collection.objects.link(esqueleto)
    bpy.context.view_layer.objects.active = esqueleto
    bpy.ops.object.mode_set(mode="EDIT")
    for nombre, (cabeza, cola, padre) in HUESOS.items():
        hueso = datos.edit_bones.new(nombre)
        hueso.head, hueso.tail = cabeza, cola
        # El eje X local de cada hueso queda paralelo al X del mundo, así girar
        # en X siempre balancea hacia adelante y atrás, apunte adonde apunte.
        hueso.align_roll(Vector((1, 0, 0)).cross(hueso.vector).normalized())
        if padre:
            hueso.parent = datos.edit_bones[padre]
    bpy.ops.object.mode_set(mode="OBJECT")
    for hueso in esqueleto.pose.bones:
        hueso.rotation_mode = "XYZ"
    return esqueleto


def deformar(tronco, esqueleto):
    """El cuerpo mueve la parte baja del tronco y la cabeza la alta, con transición suave."""
    cuerpo = tronco.vertex_groups.new(name="cuerpo")
    cabeza = tronco.vertex_groups.new(name="cabeza")
    for vertice in tronco.data.vertices:
        mezcla = min(max((vertice.co.z - 0.9) / 0.12, 0), 1)
        mezcla = mezcla * mezcla * (3 - 2 * mezcla)
        cuerpo.add([vertice.index], 1 - mezcla, "REPLACE")
        cabeza.add([vertice.index], mezcla, "REPLACE")
    tronco.parent = esqueleto
    modificador = tronco.modifiers.new("esqueleto", "ARMATURE")
    modificador.object = esqueleto


def pegar(objetos, esqueleto, hueso):
    """Pega piezas rígidas a un hueso sin moverlas de donde fueron modeladas."""
    bpy.context.view_layer.update()
    matriz_hueso = esqueleto.matrix_world @ esqueleto.pose.bones[hueso].matrix
    matriz_cola = matriz_hueso @ Matrix.Translation((0, esqueleto.data.bones[hueso].length, 0))
    for objeto in objetos:
        objeto.parent = esqueleto
        objeto.parent_type = "BONE"
        objeto.parent_bone = hueso
        objeto.matrix_parent_inverse = matriz_cola.inverted()


def construir_extremidades(m) -> dict[str, list[bpy.types.Object]]:
    """Brazos con palma rosada y garras, piernas con garras y la cola."""
    piezas = {"cola": [fundir(COLA, "cola")]}
    piezas["cola"][0].data.materials.append(m["piel"])
    for lado, sufijo in ((-1, "R"), (1, "L")):
        brazo = fundir(BRAZO, f"brazo_{sufijo}", lado)
        brazo.data.materials.append(m["piel"])
        antebrazo = fundir(ANTEBRAZO, f"antebrazo_{sufijo}", lado)
        pintar_palma(antebrazo, m, lado)
        # Tres uñas cortas y redondas en el borde de abajo de la mano, como en los
        # pies: separadas lo suficiente para que cada una caiga en su propio píxel
        # y apuntando hacia abajo para no alargar la silueta en una raya.
        mano, dedos, costado, _ = ejes_mano(lado)
        abajo = (dedos * 0.6 + Vector((0, 0, -1))).normalized()
        garras_mano = []
        for dedo in (-1, 0, 1):
            origen = mano + abajo * 0.5 + costado * (0.08 * dedo)
            punto, normal = superficie(antebrazo, origen, -abajo)
            garras_mano.append(orientado(f"garra_mano_{sufijo}_{dedo}", punto, (0.026, 0.024, 0.034), abajo, m["garra"]))
        piezas[f"brazo.{sufijo}"] = [brazo]
        piezas[f"antebrazo.{sufijo}"] = [antebrazo, *garras_mano]

        pierna = fundir(PIERNA, f"pierna_{sufijo}", lado)
        pierna.data.materials.append(m["piel"])
        garras_pie = []
        for dedo in (-1, 0, 1):
            punto, normal = superficie(pierna, (0.23 * lado + 0.08 * dedo, -2, 0.04), (0, 1, 0))
            garras_pie.append(orientado(f"garra_pie_{sufijo}_{dedo}", punto, (0.035, 0.03, 0.04), normal, m["garra"]))
        piezas[f"pierna.{sufijo}"] = [pierna, *garras_pie]
    return piezas


def construir_crestas(cabeza, m) -> list[bpy.types.Object]:
    """Pone las crestitas sobre la parte de atrás de la cabeza, medio hundidas en ella."""
    crestas = []
    for indice, (altura, radios) in enumerate(CRESTAS):
        punto, normal = superficie(cabeza, (0, 2, altura), (0, -1, 0))
        crestas.append(orientado(f"cresta_{indice}", punto + normal * 0.015, radios, normal, m["cresta"]))
    return crestas


def construir_cara(cabeza, m) -> tuple[list[bpy.types.Object], dict[str, list[bpy.types.Object]]]:
    """Crea las marcas de ojos y boca y los extras 3D de la cara.

    Las marcas solo dicen dónde van los ojos y la boca; su forma la dibuja el
    render según el gesto de cada cuadro (ver gestos.py). Los ojos van en la
    mitad baja de la cara y no muy separados, dejando una frente amplia, que es
    lo que le da la expresión tierna de los sprites 2D.
    """
    marcas, ojos = [], []
    for lado in (-1, 1):
        punto, normal = superficie(cabeza, (0.2 * lado, -2, 1.23), (0, 1, 0))
        marcas.append(orientado(f"ojo_{lado}", punto, (0.095, 0.085, 0.03), normal, m["ojo"]))
        ojos.append((punto, normal))
    punto, normal = superficie(cabeza, (0, -2, 1.09), (0, 1, 0))
    marcas.append(orientado("boca", punto, (0.12, 0.065, 0.02), normal, m["boca"]))

    def lagrima(lado):
        punto_ojo, normal_ojo = ojos[0 if lado < 0 else 1]
        centro = punto_ojo + normal_ojo * 0.05 + Vector((0.06 * lado, 0, -0.14))
        return elipsoide(f"lagrima_{lado}", centro, (0.03, 0.025, 0.045), m["lagrima"])

    mejillas = []
    for lado in (-1, 1):
        punto, normal = superficie(cabeza, (0.33 * lado, -2, 1.12), (0, 1, 0))
        mejillas.append(orientado(f"mejilla_{lado}", punto + normal * 0.005, (0.07, 0.04, 0.015), normal, m["mejilla"]))
    punto, normal = superficie(cabeza, (2, -0.15, 1.5), (-1, 0, 0))
    sudor = elipsoide("sudor", punto + normal * 0.04, (0.035, 0.03, 0.055), m["sudor"])

    extras = {
        "parpados": [
            orientado(f"parpado_{lado}", punto_ojo + normal_ojo * 0.02 + Vector((0, 0, 0.07)), (0.12, 0.055, 0.05), normal_ojo, m["parpado"], 18 * lado)
            for lado, (punto_ojo, normal_ojo) in zip((-1, 1), ojos)
        ],
        "lagrima": [lagrima(1)],
        "lagrimas": [lagrima(-1), lagrima(1)],
        "sonrojo": mejillas,
        "sudor": [sudor],
    }
    return marcas, extras


def seccion(perfil, z: float) -> tuple[float, float, float]:
    """Medio ancho, frente y espalda de un perfil (cuerpo o cabeza) a cierta altura."""
    alturas, anchos, frentes, atrases = (np.array(columna) for columna in zip(*perfil))
    return tuple(float(interpolar(alturas, valores, np.array([z]))[0]) for valores in (anchos, frentes, atrases))


def cono(nombre, base, punta, radio_base, radio_punta, material, aplanar=1.0):
    """Un cono (o tronco de cono) de la base a la punta; aplanar < 1 lo achata de lado."""
    base, punta = Vector(base), Vector(punta)
    bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=radio_base, radius2=radio_punta, depth=(punta - base).length)
    objeto = bpy.context.object
    objeto.name = nombre
    rotacion = (punta - base).to_track_quat("Z", "Y").to_matrix().to_4x4()
    objeto.data.transform(Matrix.Translation((base + punta) / 2) @ rotacion @ Matrix.Diagonal((aplanar, 1, 1, 1)))
    bpy.ops.object.shade_smooth()
    objeto.data.materials.append(material)
    return objeto


def recortar(objeto, quitar):
    """Borra de una malla las caras cuyo centro cumple la condición (huecos, ventanas)."""
    import bmesh

    bm = bmesh.new()
    bm.from_mesh(objeto.data)
    bmesh.ops.delete(bm, geom=[cara for cara in bm.faces if quitar(cara.calc_center_median())], context="FACES")
    bm.to_mesh(objeto.data)
    bm.free()
    objeto.data.update()
    return objeto


def funda(nombre, alturas, medida, material):
    """Una tela que envuelve a Nailong, levantada fila por fila.

    medida(z) da (medio ancho, frente, espalda) de la tela a cada altura; así
    se arman el traje de calabaza, la túnica, la sábana y las capuchas.
    """
    filas = [(z, *medida(z)) for z in alturas]
    objeto = levantar(nombre, filas, 2.0)
    objeto.data.materials.append(material)
    return objeto


def holgado(perfil, z, holgura):
    """La sección de un perfil a esa altura, con holgura alrededor."""
    ancho, frente, atras = seccion(perfil, min(max(z, perfil[0][0]), perfil[-1][0]))
    return ancho + holgura, frente + holgura, atras + holgura


def capucha(nombre, material, desde, cara=True):
    """Capucha ceñida a la cabeza desde cierta altura hasta arriba, con la cara al aire."""
    tope = PERFIL_CABEZA[-1][0]
    alturas = list(np.linspace(desde, tope + 0.035, 22))
    def medida(z):
        if z >= tope:
            return 0.0, 0.0, 0.0
        cierre = max(0.0, (z - (tope - 0.12)) / 0.15)  # redondea la coronilla
        ancho, frente, atras = holgado(PERFIL_CABEZA, z, 0.035)
        factor = sqrt(max(0.0, 1 - cierre ** 2))
        return ancho * factor, frente * factor, atras * factor
    objeto = funda(nombre, alturas, medida, material)
    if cara:
        # Hueco ovalado para la cara: ojos, hocico y boca quedan al descubierto.
        recortar(objeto, lambda c: c.y < -0.1 and ((c.x / 0.36) ** 2 + ((c.z - 1.17) / 0.23) ** 2) < 1)
    return objeto


def tela(nombre, filas_de_puntos, exterior, interior):
    """Una tela de doble faz a partir de una grilla de puntos (filas de igual largo).

    Un lado lleva el color de afuera y el otro el del forro, como la capa del
    vampiro: negra por fuera y roja por dentro.
    """
    columnas = len(filas_de_puntos[0])
    vertices = [tuple(punto) for fila in filas_de_puntos for punto in fila]
    caras = [
        (f * columnas + c, f * columnas + c + 1, (f + 1) * columnas + c + 1, (f + 1) * columnas + c)
        for f in range(len(filas_de_puntos) - 1) for c in range(columnas - 1)
    ]
    malla = bpy.data.meshes.new(nombre)
    malla.from_pydata(vertices, [], caras)
    objeto = bpy.data.objects.new(nombre, malla)
    bpy.context.collection.objects.link(objeto)
    for poligono in malla.polygons:
        poligono.use_smooth = True
    objeto.data.materials.append(exterior)
    objeto.data.materials.append(interior)
    grosor = objeto.modifiers.new("grosor", "SOLIDIFY")
    grosor.thickness = 0.025
    grosor.offset = 1.0
    grosor.material_offset = 1
    bpy.context.view_layer.objects.active = objeto
    bpy.ops.object.modifier_apply(modifier=grosor.name)
    return objeto


def construir_vampiro(m) -> list[tuple[str, list[bpy.types.Object]]]:
    """Vampiro como en la foto: chaleco negro con camisa y moño, capa negra con
    forro rojo y cuello alto detrás de la cabeza.

    La espalda de la capa va con el cuerpo y cada costado con su brazo, así al
    abrir los brazos la capa se abre como en la pose clásica.
    """
    # Camisa blanca y chaleco negro escotado en V, que llega a media panza.
    camisa = funda("vampiro_camisa", list(np.linspace(0.7, 0.98, 8)), lambda z: holgado(PERFIL, z, 0.02), m["sabana"])
    chaleco = funda("vampiro_chaleco", list(np.linspace(0.44, 0.98, 18)), lambda z: holgado(PERFIL, z, 0.032), m["negro"])
    # Escote en V al frente y la punta del chaleco abajo.
    recortar(chaleco, lambda c: c.y < -0.1 and (abs(c.x) < (c.z - 0.72) * 0.9 or c.z < 0.5 - 0.1 * (1 - min(abs(c.x) / 0.3, 1))))
    botones = []
    for i, z in enumerate((0.66, 0.56)):
        punto, normal = superficie(chaleco, (0, -2, z), (0, 1, 0))
        botones.append(orientado(f"vampiro_boton_{i}", punto, (0.03, 0.03, 0.015), normal, m["dorado"]))
    punto, normal = superficie(camisa, (0, -2, 0.92), (0, 1, 0))
    mono = [
        cono(f"vampiro_mono_{lado}", punto + normal * 0.03, punto + normal * 0.03 + Vector((0.11 * lado, 0, 0)), 0.003, 0.055, m["rojo"], 0.5)
        for lado in (-1, 1)
    ] + [elipsoide("vampiro_broche", punto + normal * 0.05 + Vector((0, 0, 0.05)), (0.035, 0.02, 0.035), m["rojo"])]

    # Espalda de la capa, de los hombros casi al piso, abriéndose hacia abajo.
    filas = []
    for z in np.linspace(0.98, 0.18, 12):
        ancho, frente, atras = holgado(PERFIL, max(float(z), PERFIL[0][0]), 0.06)
        vuelo = 0.22 * ((0.98 - z) / 0.8) ** 1.3
        fila = []
        for angulo in np.linspace(radians(200), radians(-20), 16):
            x, y = cos(angulo), sin(angulo)
            fila.append((x * (ancho + vuelo), y * ((atras if y > 0 else frente) + vuelo), float(z)))
        filas.append(fila)
    espalda = tela("vampiro_capa", filas, m["negro"], m["rojo"])
    # Cuello alto: rodea la nuca por detrás de la cabeza y se abre hacia arriba.
    filas = []
    # Las filas van de arriba abajo, como en la espalda, para que el forro rojo
    # quede del lado de la cabeza.
    for z in np.linspace(1.3, 0.92, 6):
        t = (z - 0.92) / 0.38
        radio = 0.4 + 0.24 * t ** 1.5
        fila = [(cos(a) * radio, sin(a) * (radio * 0.85) + 0.04, float(z)) for a in np.linspace(radians(210), radians(-30), 16)]
        filas.append(fila)
    cuello = tela("vampiro_cuello", filas, m["negro"], m["rojo"])
    # Las puntas de adelante, que son las que se ven de frente junto a la
    # cabeza, son rojas por los dos lados: así se lee el forro como en la foto.
    for cara in cuello.data.polygons:
        if cara.center.y < 0.02:
            cara.material_index = 1

    # Costados de la capa, pegados a cada brazo: del hombro a la mano y al piso.
    costados = {}
    for lado, sufijo in ((-1, "R"), (1, "L")):
        hombro = Vector((0.3 * lado, 0.12, 0.95))
        mano = Vector((MANO.x * lado, MANO.y, MANO.z)) + Vector((0.04 * lado, 0.02, 0))
        filas = []
        for z_pie in np.linspace(0, 1, 8):
            arriba = hombro.lerp(mano, z_pie)
            abajo = Vector((0.42 * lado, 0.38, 0.2)).lerp(Vector((0.72 * lado, -0.12, 0.22)), z_pie)
            filas.append([tuple(arriba.lerp(abajo, t)) for t in np.linspace(0, 1, 8)])
        filas = [list(columna) for columna in zip(*filas)]
        costados[f"brazo.{sufijo}"] = [tela(f"vampiro_capa_{sufijo}", filas if lado > 0 else [fila[::-1] for fila in filas], m["negro"], m["rojo"])]

    return [("cuerpo", [camisa, chaleco, *botones, *mono, espalda, cuello]), *costados.items()]


def mangas_ajustadas(nombre, material, radios_brazo, radios_antebrazo):
    """Una manga sobre cada brazo y antebrazo, por hueso."""
    mangas = {}
    for lado, sufijo in ((-1, "R"), (1, "L")):
        hombro = Vector((BRAZO[0][0][0] * lado, BRAZO[0][0][1], BRAZO[0][0][2]))
        codo = Vector((CODO.x * lado, CODO.y, CODO.z))
        mano = Vector((MANO.x * lado, MANO.y, MANO.z))
        mangas[f"brazo.{sufijo}"] = [orientado(f"{nombre}_manga_{sufijo}", (hombro + codo) / 2 + Vector((0, 0, -0.03)), radios_brazo, codo - hombro, material)]
        mangas[f"antebrazo.{sufijo}"] = [orientado(f"{nombre}_puno_{sufijo}", codo + (mano - codo) * 0.4 + Vector((0, 0, -0.03)), radios_antebrazo, mano - codo, material)]
    return mangas


def construir_spiderman(m) -> list[tuple[str, list[bpy.types.Object]]]:
    """Traje rojo y azul con la máscara completa, ojos blancos grandes y telaraña.

    La máscara esconde la cabeza de Nailong (ver TAPAN_CABEZA), así que los ojos
    son lentes blancos pegados a la tela.
    """
    torso = funda("spiderman_torso", list(np.linspace(0.5, 0.99, 14)), lambda z: holgado(PERFIL, z, 0.03), m["rojo"])
    cadera = funda("spiderman_cadera", list(np.linspace(0.29, 0.52, 8)), lambda z: holgado(PERFIL, z, 0.025), m["azul"])
    telarana = [
        funda(f"spiderman_tela_{i}", [z - 0.012, z, z + 0.012], lambda zz: holgado(PERFIL, zz, 0.036), m["negro"])
        for i, z in enumerate((0.6, 0.72, 0.84))
    ]
    punto, normal = superficie(torso, (0, -2, 0.78), (0, 1, 0))
    araña = [
        orientado("spiderman_arana", punto + normal * 0.01, (0.075, 0.09, 0.02), normal, m["negro"]),
        *(
            barra(f"spiderman_pata_{lado}_{i}", punto + Vector((0.02 * lado, -0.03, 0.02 * (1 - i))),
                  punto + Vector((0.13 * lado, -0.05, 0.06 * (1 - i) + 0.02 * i)), 0.012, m["negro"])
            for lado in (-1, 1) for i in range(3)
        ),
    ]
    mascara = capucha("spiderman_mascara", m["rojo"], 0.95, cara=False)
    lentes = []
    for lado in (-1, 1):
        punto, normal = superficie(mascara, (0.22 * lado, -2, 1.3), (0, 1, 0))
        lentes.append(orientado(f"spiderman_lente_{lado}", punto + normal * 0.005, (0.16, 0.1, 0.03), normal, m["sabana"], -22 * lado))
    mangas = mangas_ajustadas("spiderman", m["rojo"], (0.23, 0.21, 0.25), (0.2, 0.21, 0.2))
    piernas = {}
    for lado, sufijo in ((-1, "R"), (1, "L")):
        piernas[f"pierna.{sufijo}"] = [
            elipsoide(f"spiderman_pierna_{sufijo}_{i}", (centro[0] * lado, centro[1], centro[2]), tuple(r * 1.13 for r in radios), m["azul"])
            for i, (centro, radios, _) in enumerate(PIERNA)
        ]
    return [("cuerpo", [torso, cadera, *telarana, *araña]), ("cabeza", [mascara, *lentes]), *mangas.items(), *piernas.items()]


def construir_pollito(m) -> list[tuple[str, list[bpy.types.Object]]]:
    """Mameluco de pollito: plumón amarillo claro, capucha con pico y mechón, alitas y patas naranjas."""
    cuerpo = funda("pollito_cuerpo", list(np.linspace(0.29, 0.99, 20)), lambda z: holgado(PERFIL, z, 0.045), m["pollo"])
    capucha_pollo = capucha("pollito_capucha", m["pollo"], 0.95)
    pico = cono("pollito_pico", (0, -0.58, 1.165), (0, -0.8, 1.14), 0.11, 0.03, m["calabaza"], 0.65)
    mechon = [
        cono(f"pollito_mechon_{i}", (0.05 * i, -0.02 + 0.03 * abs(i), 1.64), (0.1 * i, 0.0 + 0.03 * abs(i), 1.9 - 0.06 * abs(i)), 0.045, 0.01, m["pollo"])
        for i in (-1, 0, 1)
    ]
    alas = mangas_ajustadas("pollito", m["pollo"], (0.24, 0.22, 0.26), (0.21, 0.22, 0.21))
    patas = {}
    for lado, sufijo in ((-1, "R"), (1, "L")):
        centro, radios, _ = PIERNA[2]
        patas[f"pierna.{sufijo}"] = [elipsoide(f"pollito_pata_{sufijo}", (centro[0] * lado, centro[1] - 0.03, centro[2]), (radios[0] * 1.08, radios[1] * 1.12, radios[2] * 1.15), m["calabaza"])]
    return [("cuerpo", [cuerpo]), ("cabeza", [capucha_pollo, pico, *mechon]), *alas.items(), *patas.items()]


def construir_disfraces(m) -> dict[str, list[tuple[str, list[bpy.types.Object]]]]:
    """Mamelucos de Halloween de cuerpo entero: cada uno es una lista de (hueso, piezas).

    Son piezas grandes y de colores que contrastan con el amarillo, para que a
    64 píxeles se lean como disfraz y no como manchas.
    """
    # Calabaza: el cuerpo dentro de una calabaza gorda con gajos y cara tallada.
    def medida_calabaza(z):
        t = (z - 0.6) / 0.43
        redondo = sqrt(max(0.0, 1 - t * t))
        return 0.54 * redondo, 0.5 * redondo, 0.47 * redondo
    traje = funda("calabaza_traje", list(np.linspace(0.17, 1.03, 24)), medida_calabaza, m["calabaza"])
    for v in traje.data.vertices:
        gajo = 1 - 0.1 * abs(sin(4 * np.arctan2(v.co.y, v.co.x))) ** 0.7
        v.co.x, v.co.y = v.co.x * gajo, v.co.y * gajo
    traje.data.update()
    cara_calabaza = []
    for lado in (-1, 1):
        punto, normal = superficie(traje, (0.17 * lado, -2, 0.7), (0, 1, 0))
        cara_calabaza.append(cono(f"calabaza_ojo_{lado}", punto - Vector((0, 0, 0.05)), punto + Vector((0, 0, 0.06)), 0.08, 0.0, m["negro"], 0.25))
    for i, x in enumerate((-0.18, -0.06, 0.06, 0.18)):
        punto, normal = superficie(traje, (x, -2, 0.5 - 0.03 * (i % 2)), (0, 1, 0))
        cara_calabaza.append(orientado(f"calabaza_boca_{i}", punto, (0.07, 0.045, 0.02), normal, m["negro"], 25 * (1 if i % 2 else -1)))
    gorro_calabaza = capucha("calabaza_gorro", m["calabaza"], 1.42, cara=False)
    calabaza_gorro = [
        gorro_calabaza,
        barra("calabaza_tallo", (0, -0.02, 1.7), (0.05, 0.0, 1.86), 0.05, m["planta"]),
        orientado("calabaza_hoja", (0.14, -0.04, 1.8), (0.11, 0.05, 0.016), (0.3, -0.4, 1), m["planta"], 20),
    ]

    # Fantasma: una sábana en forma de campana que tapa todo, cabeza incluida,
    # con los ojos negros pintados encima y el borde ondulado a media pierna.
    # Mientras la lleva, la cabeza de Nailong se esconde (ver vestir), así la
    # sábana no tiene que seguirla cuando gira.
    tope_sabana, borde_sabana = 1.84, 0.33
    def medida_sabana(z):
        if z >= tope_sabana:
            return 0.0, 0.0, 0.0
        if z > 1.3:  # la cúpula sobre la cabeza
            factor = sqrt(max(0.0, 1 - ((z - 1.3) / (tope_sabana - 1.3)) ** 2))
            return 0.52 * factor, 0.68 * factor, 0.5 * factor
        # Cae casi recta hasta la cintura y se abre en campana cerca del borde.
        t = max(0.0, (0.75 - z) / (0.75 - borde_sabana))
        return 0.52 + 0.14 * t ** 1.6, 0.68 + 0.04 * t, 0.5 + 0.1 * t
    sabana = funda("sabana", list(np.linspace(borde_sabana, tope_sabana, 40)), medida_sabana, m["sabana"])
    recortar(sabana, lambda c: c.z < borde_sabana - 0.005)
    for v in sabana.data.vertices:
        if v.co.z < borde_sabana + 0.03:
            v.co.z += 0.045 * sin(7 * np.arctan2(v.co.y, v.co.x))
    sabana.data.update()
    ojos_sabana = []
    for lado in (-1, 1):
        punto, normal = superficie(sabana, (0.19 * lado, -2, 1.32), (0, 1, 0))
        ojos_sabana.append(orientado(f"sabana_ojo_{lado}", punto, (0.095, 0.135, 0.02), normal, m["negro"], 12 * lado))
    # Mangas: la tela cae sobre cada brazo y deja ver solo la mano.
    mangas = {}
    for lado, sufijo in ((-1, "R"), (1, "L")):
        hombro = Vector((BRAZO[0][0][0] * lado, BRAZO[0][0][1], BRAZO[0][0][2]))
        codo = Vector((CODO.x * lado, CODO.y, CODO.z))
        mano = Vector((MANO.x * lado, MANO.y, MANO.z))
        mangas[f"brazo.{sufijo}"] = [orientado(f"manga_{sufijo}", (hombro + codo) / 2 + Vector((0, 0, -0.03)), (0.17, 0.15, 0.12), codo - hombro, m["sabana"])]
        mangas[f"antebrazo.{sufijo}"] = [orientado(f"manga_puno_{sufijo}", codo + (mano - codo) * 0.35 + Vector((0, 0, -0.04)), (0.16, 0.14, 0.08), mano - codo, m["sabana"])]

    # Bruja: túnica acampanada con cinturón y el sombrero puntiagudo.
    def medida_tunica(z):
        ancho, frente, atras = holgado(PERFIL, z, 0.04)
        vuelo = 0.2 * max(0.0, (0.75 - z) / 0.55) ** 1.3
        return ancho + vuelo, frente + vuelo, atras + vuelo
    tunica = funda("bruja_tunica", list(np.linspace(0.2, 0.99, 20)), medida_tunica, m["morado"])
    cinturon = funda("bruja_cinturon", [0.6, 0.64, 0.68], lambda z: tuple(v + 0.012 for v in medida_tunica(z)), m["calabaza"])
    sombrero = [
        elipsoide("bruja_ala", (0, -0.04, 1.63), (0.66, 0.68, 0.04), m["morado"], (-8, 0, 6)),
        cono("bruja_copa", (0, -0.02, 1.62), (0.03, 0.06, 1.86), 0.32, 0.13, m["morado"]),
        cono("bruja_punta", (0.03, 0.06, 1.85), (0.22, 0.22, 1.98), 0.135, 0.012, m["morado"]),
        funda("bruja_banda", [1.65, 1.69, 1.73], lambda z: (0.335 - (z - 1.62) * 0.8,) * 3, m["calabaza"]),
    ]
    for pieza in sombrero[3:]:
        pieza.data.transform(Matrix.Translation((0.005, -0.01, 0)))

    # Murciélago: traje negro con la panza al aire, capucha con orejas y alas.
    traje_negro = funda("murcielago_traje", list(np.linspace(0.24, 0.99, 20)), lambda z: holgado(PERFIL, z, 0.025), m["negro"])
    recortar(traje_negro, lambda c: c.y < -0.15 and ((c.x / 0.24) ** 2 + ((c.z - 0.6) / 0.28) ** 2) < 1)
    capucha_negra = capucha("murcielago_capucha", m["negro"], 0.95)
    orejas = [cono(f"murcielago_oreja_{lado}", (0.22 * lado, -0.02, 1.55), (0.4 * lado, 0.0, 1.95), 0.14, 0.01, m["negro"], 0.35) for lado in (-1, 1)]
    alas = []
    for lado in (-1, 1):
        # Ala con el borde de abajo festoneado, plana y abierta detrás de la espalda.
        borde_alto = [(0.12, 0.95), (0.4, 1.08), (0.68, 1.12), (0.86, 1.02)]
        festones = [(0.86, 1.02), (0.72, 0.78), (0.58, 0.86), (0.44, 0.66), (0.3, 0.74), (0.14, 0.55)]
        contorno = borde_alto + festones[1:]
        vertices = [(x * lado, 0.3 + 0.12 * x, z) for x, z in contorno]
        malla = bpy.data.meshes.new(f"murcielago_ala_{lado}")
        malla.from_pydata(vertices, [], [list(range(len(vertices)))])
        ala = bpy.data.objects.new(malla.name, malla)
        bpy.context.collection.objects.link(ala)
        ala.data.materials.append(m["morado"])
        solido = ala.modifiers.new("grosor", "SOLIDIFY")
        solido.thickness = 0.03
        bpy.context.view_layer.objects.active = ala
        bpy.ops.object.modifier_apply(modifier=solido.name)
        alas.append(ala)

    return {
        "calabaza": [("cuerpo", [traje, *cara_calabaza]), ("cabeza", calabaza_gorro)],
        "fantasma": [("cuerpo", [sabana, *ojos_sabana]), *mangas.items()],
        "bruja": [("cuerpo", [tunica, cinturon]), ("cabeza", sombrero)],
        "murcielago": [("cuerpo", [traje_negro, *alas]), ("cabeza", [capucha_negra, *orejas])],
        "vampiro": construir_vampiro(m),
        "spiderman": construir_spiderman(m),
        "pollito": construir_pollito(m),
    }


def construir_gorra(m):
    copa = elipsoide("gorra_copa", (0, -0.08, 1.56), (0.6, 0.7, 0.32), m["gorra"], (-12, 0, 0))
    visera = elipsoide("gorra_visera", (0, -0.76, 1.62), (0.36, 0.25, 0.035), m["visera"], (-8, 0, 0))
    return [copa, visera]


def caja(nombre, centro, medidas, material, rotacion=(0, 0, 0)):
    """Crea una caja con sus medidas completas (ancho, fondo, alto) y rotación en grados."""
    bpy.ops.mesh.primitive_cube_add(size=1)
    objeto = bpy.context.object
    objeto.name = nombre
    objeto.scale = medidas
    objeto.rotation_euler = [radians(angulo) for angulo in rotacion]
    objeto.location = centro
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    objeto.data.materials.append(material)
    return objeto


def barra(nombre, inicio, fin, radio, material):
    """Un palito redondo de un punto a otro: patas, lápices, tallos."""
    inicio, fin = Vector(inicio), Vector(fin)
    return orientado(nombre, (inicio + fin) / 2, (radio, radio, (fin - inicio).length / 2), fin - inicio, material)


def cuenco(nombre, centro, radios, material):
    """Media esfera abierta hacia arriba, como una tina vista de lado."""
    objeto = elipsoide(nombre, (0, 0, 0), (1, 1, 1), material)
    malla = objeto.data
    import bmesh

    bm = bmesh.new()
    bm.from_mesh(malla)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z > 0.01], context="VERTS")
    bm.to_mesh(malla)
    bm.free()
    objeto.scale = radios
    objeto.location = centro
    bpy.ops.object.transform_apply(location=True, scale=True)
    return objeto


def acolchar(nombre, centro, radios, largo, material, bisel):
    """Tubo de sección ovalada a lo largo del cuerpo, con las puntas redondeadas como un edredón."""
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=1, depth=1)
    objeto = bpy.context.object
    objeto.name = nombre
    objeto.scale = (*radios, largo)
    objeto.location = centro
    bpy.ops.object.transform_apply(location=True, scale=True)
    redondeo = objeto.modifiers.new("bisel", "BEVEL")
    redondeo.width = bisel
    redondeo.segments = 4
    suavizado = objeto.modifiers.new("suave", "SUBSURF")
    suavizado.levels = 2
    suavizado.render_levels = 2
    bpy.context.view_layer.objects.active = objeto
    bpy.ops.object.modifier_apply(modifier=redondeo.name)
    bpy.ops.object.modifier_apply(modifier=suavizado.name)
    bpy.ops.object.shade_smooth()
    objeto.data.materials.append(material)
    return objeto


def construir_cobija(m) -> list[bpy.types.Object]:
    """Edredón para dormir acostado, modelado con Nailong de pie.

    Al acostarse de lado sobre el costado derecho, el +X del cuerpo queda hacia
    arriba: la cobija es un bulto ovalado que lo tapa de los pies al cuello y
    llega abajo hasta el colchón. En el cuello lleva el doblez de la sábana.
    """
    return [
        acolchar("cobija", (0.0, -0.04, 0.27), (0.56, 0.62), 1.4, m["cobija"], 0.16),
        acolchar("cobija_doblez", (0.0, -0.04, 0.95), (0.59, 0.65), 0.14, m["sabana"], 0.05),
    ]


def morder(objeto, centro, radio):
    """Le quita un mordisco redondo a un objeto."""
    bocado = elipsoide(f"{objeto.name}_bocado", centro, (radio,) * 3)
    corte = objeto.modifiers.new("mordisco", "BOOLEAN")
    corte.operation = "DIFFERENCE"
    corte.object = bocado
    bpy.context.view_layer.objects.active = objeto
    bpy.ops.object.modifier_apply(modifier=corte.name)
    bpy.data.objects.remove(bocado)
    return objeto


CENTRO_LIENZO = Vector((0.66, -0.6, 0.95))


def construir_objetos(cabeza, m) -> tuple[dict[str, list[bpy.types.Object]], dict[str, str]]:
    """Utilería de las acciones y el hueso al que va pegada cada pieza.

    La galleta va frente al pecho, donde quedan las manos al comer, y la cabeza
    se agacha para morderla. La tina va en el piso frente a los pies, con la
    ropa en el agua y dos tandas de espuma que se alternan al restregar.
    """
    centro_galleta = (0, -0.5, 0.98)
    galleta = elipsoide("galleta", centro_galleta, (0.11, 0.035, 0.11), m["galleta"])
    mordida = morder(elipsoide("galleta_mordida", centro_galleta, (0.11, 0.035, 0.11), m["galleta"]), (0.05, -0.5, 1.07), 0.065)

    tina = cuenco("tina", (0, -0.66, 0.36), (0.36, 0.26, 0.3), m["tina"])
    agua = elipsoide("agua", (0, -0.66, 0.33), (0.33, 0.23, 0.02), m["agua"])
    ropa = elipsoide("ropa", (0.02, -0.6, 0.36), (0.2, 0.13, 0.05), m["ropa"], (0, 8, 15))
    burbujas = {
        "espuma_a": [((-0.2, -0.78, 0.38), 0.05), ((0.17, -0.82, 0.36), 0.04), ((0.05, -0.5, 0.4), 0.045)],
        "espuma_b": [((-0.08, -0.84, 0.39), 0.05), ((0.24, -0.66, 0.4), 0.045), ((-0.22, -0.55, 0.37), 0.04)],
    }
    objetos = {
        "galleta": [galleta],
        "galleta_mordida": [mordida],
        "tina": [tina, agua],
        "ropa": [ropa],
        **{
            nombre: [elipsoide(f"{nombre}_{i}", centro, (radio,) * 3, m["espuma"]) for i, (centro, radio) in enumerate(lista)]
            for nombre, lista in burbujas.items()
        },
    }
    # Burbuja de nariz para dormir, en dos tamaños que se alternan al respirar.
    punto, normal = superficie(cabeza, (0.05, -2, 1.15), (0, 1, 0))
    for nombre, radio in (("burbuja_chica", 0.055), ("burbuja_grande", 0.11)):
        objetos[nombre] = [elipsoide(nombre, punto + normal * radio + Vector((radio * 0.6, 0, -radio * 0.3)), (radio,) * 3, m["agua"])]
    huesos = {"galleta": "cuerpo", "galleta_mordida": "cuerpo", "burbuja_chica": "cabeza", "burbuja_grande": "cabeza"}
    objetos["cobija"] = construir_cobija(m)
    huesos["cobija"] = "cuerpo"

    # Lápiz o pincel en la mano izquierda, saliendo entre los dedos.
    mano, dedos, _, palma = ejes_mano(1)
    punta = (dedos + palma * 0.8).normalized()
    objetos["lapiz"] = [barra("lapiz", mano - punta * 0.02, mano + punta * 0.13, 0.018, m["lapiz"])]
    huesos["lapiz"] = "antebrazo.L"

    # Caballete al costado izquierdo de Nailong, con el lienzo girado hacia él y
    # hacia el jugador; los trazos aparecen de a poco mientras pinta.
    # El lienzo mira hacia Nailong y la cámara de tres cuartos a la vez.
    giro = -50
    centro_lienzo = CENTRO_LIENZO
    frente_lienzo = Vector((-1, -0.85, 0)).normalized()
    derecha_lienzo = Vector((1, 0, 0))
    derecha_lienzo.rotate(Euler((0, 0, radians(giro))))
    atras = -frente_lienzo
    objetos["caballete"] = [
        caja("lienzo", centro_lienzo, (0.46, 0.035, 0.44), m["papel"], (0, 0, giro)),
        barra("pata_1", centro_lienzo - derecha_lienzo * 0.16 + atras * 0.03 + Vector((0, 0, 0.3)), centro_lienzo - derecha_lienzo * 0.24 + Vector((0, 0, -0.92)), 0.03, m["madera"]),
        barra("pata_2", centro_lienzo + derecha_lienzo * 0.16 + atras * 0.03 + Vector((0, 0, 0.3)), centro_lienzo + derecha_lienzo * 0.24 + Vector((0, 0, -0.92)), 0.03, m["madera"]),
        barra("pata_3", centro_lienzo + atras * 0.04 + Vector((0, 0, 0.28)), centro_lienzo + atras * 0.3 + Vector((0, 0, -0.92)), 0.03, m["madera"]),
        caja("repisa", centro_lienzo - frente_lienzo * -0.03 + Vector((0, 0, -0.26)), (0.54, 0.08, 0.04), m["madera"], (0, 0, giro)),
    ]
    trazos = [
        ((-0.12, 0.1), 0.08, "planta"), ((0.1, 0.09), 0.07, "lapiz"), ((-0.03, -0.07), 0.09, "libro"),
        ((0.14, -0.1), 0.06, "regadera"), ((-0.15, -0.12), 0.05, "lapiz"),
    ]
    for tanda in range(1, 4):
        objetos[f"pintura_{tanda}"] = [
            orientado(f"pintura_{tanda}_{i}", centro_lienzo + frente_lienzo * 0.018 + derecha_lienzo * x + Vector((0, 0, z)),
                      (radio, radio * 0.8, 0.008), frente_lienzo, m[color])
            for i, ((x, z), radio, color) in enumerate(trazos[: tanda + 2 if tanda < 3 else len(trazos)])
        ]

    # Libreta sobre las piernas al escribir, con renglones que se van llenando.
    # La hoja se inclina hacia el jugador para que se vea lo que escribe.
    centro_libreta = Vector((0, -0.52, 0.55))
    inclinacion = 45
    arriba_hoja = Vector((0, cos(radians(inclinacion)), sin(radians(inclinacion))))
    normal_hoja = Vector((0, -sin(radians(inclinacion)), cos(radians(inclinacion))))
    objetos["libreta"] = [
        caja("libreta_tapa", centro_libreta - normal_hoja * 0.014, (0.38, 0.28, 0.016), m["libro"], (inclinacion, 0, 0)),
        caja("libreta_hoja", centro_libreta, (0.34, 0.25, 0.012), m["papel"], (inclinacion, 0, 0)),
    ]
    for tanda in range(1, 4):
        objetos[f"renglones_{tanda}"] = [
            caja(f"renglon_{tanda}_{i}", centro_libreta + arriba_hoja * (0.07 - 0.06 * i) + normal_hoja * 0.01 + Vector((-0.02 * (i % 2), 0, 0)),
                 (0.22 - 0.05 * (i % 2), 0.025, 0.006), m["garra"], (inclinacion, 0, 0))
            for i in range(tanda)
        ]
    huesos.update({nombre: "cuerpo" for nombre in objetos if nombre.startswith(("libreta", "renglones"))})

    # Libro abierto frente al pecho: tapas hacia el jugador, hojas hacia Nailong,
    # y una hoja suelta en tres posiciones para pasar la página.
    lomo = Vector((0, -0.5, 0.97))
    objetos["libro"] = [
        caja("libro_izq", lomo + Vector((-0.12, 0.04, 0)), (0.25, 0.04, 0.3), m["libro"], (0, 0, 22)),
        caja("libro_der", lomo + Vector((0.12, 0.04, 0)), (0.25, 0.04, 0.3), m["libro"], (0, 0, -22)),
        caja("hojas_izq", lomo + Vector((-0.11, 0.07, 0)), (0.22, 0.025, 0.27), m["papel"], (0, 0, 22)),
        caja("hojas_der", lomo + Vector((0.11, 0.07, 0)), (0.22, 0.025, 0.27), m["papel"], (0, 0, -22)),
    ]
    for nombre, angulo in (("pagina_der", -15), ("pagina_medio", 90), ("pagina_izq", 15)):
        direccion = Vector((1, 0, 0))
        direccion.rotate(Euler((0, 0, radians(angulo))))
        objetos[nombre] = [caja(nombre, lomo + Vector((0, 0.09, 0)) + direccion * 0.11, (0.22, 0.012, 0.26), m["papel"], (0, 0, angulo))]
    huesos.update({nombre: "cuerpo" for nombre in ("libro", "pagina_der", "pagina_medio", "pagina_izq")})

    # Maceta en el piso frente al pie izquierdo, con una planta que crece.
    maceta = Vector((0.5, -0.62, 0))
    objetos["maceta"] = [
        cuenco("maceta", maceta + Vector((0, 0, 0.17)), (0.13, 0.13, 0.17), m["maceta"]),
        elipsoide("tierra", maceta + Vector((0, 0, 0.165)), (0.115, 0.115, 0.012), m["madera"]),
    ]
    objetos["brote"] = [
        barra("brote_tallo", maceta + Vector((0, 0, 0.16)), maceta + Vector((0, 0, 0.24)), 0.014, m["planta"]),
        orientado("brote_hoja", maceta + Vector((0.035, 0, 0.25)), (0.035, 0.02, 0.012), (0, -1, 0.3), m["planta"], 30),
    ]
    objetos["planta"] = [
        barra("planta_tallo", maceta + Vector((0, 0, 0.16)), maceta + Vector((0, 0, 0.38)), 0.016, m["planta"]),
        orientado("planta_hoja_1", maceta + Vector((0.06, 0, 0.3)), (0.06, 0.03, 0.014), (0, -1, 0.3), m["planta"], 25),
        orientado("planta_hoja_2", maceta + Vector((-0.06, 0, 0.35)), (0.06, 0.03, 0.014), (0, -1, 0.3), m["planta"], -25),
    ]
    objetos["flor"] = [
        barra("flor_tallo", maceta + Vector((0, 0, 0.16)), maceta + Vector((0, 0, 0.44)), 0.016, m["planta"]),
        orientado("flor_hoja_1", maceta + Vector((0.06, 0, 0.3)), (0.06, 0.03, 0.014), (0, -1, 0.3), m["planta"], 25),
        orientado("flor_hoja_2", maceta + Vector((-0.06, 0, 0.35)), (0.06, 0.03, 0.014), (0, -1, 0.3), m["planta"], -25),
        orientado("flor_petalos", maceta + Vector((0, -0.02, 0.48)), (0.07, 0.07, 0.025), (0, -1, 0.2), m["lapiz"]),
        orientado("flor_centro", maceta + Vector((0, -0.045, 0.48)), (0.028, 0.028, 0.012), (0, -1, 0.2), m["panza"]),
    ]

    # Regadera colgando de la mano izquierda, ya inclinada para que al subir un
    # poco el brazo el pico apunte hacia la maceta.
    asa = mano + palma * 0.06
    cuerpo_regadera = asa + Vector((0.02, -0.04, -0.12))
    pico = Vector((0, -0.7, -0.5)).normalized()
    objetos["regadera"] = [
        elipsoide("regadera", cuerpo_regadera, (0.1, 0.085, 0.09), m["regadera"]),
        barra("regadera_pico", cuerpo_regadera + pico * 0.04, cuerpo_regadera + pico * 0.24, 0.022, m["regadera"]),
        barra("regadera_asa", asa - Vector((0, 0, 0.02)), cuerpo_regadera + Vector((0, 0, 0.06)), 0.016, m["regadera"]),
    ]
    huesos["regadera"] = "antebrazo.L"
    # A 64 píxeles la maceta y la regadera se pierden: se agrandan desde su base.
    for nombre, base, factor in (("maceta", maceta, 1.4), ("brote", maceta, 1.4), ("planta", maceta, 1.4),
                                 ("flor", maceta, 1.4), ("regadera", asa, 1.3)):
        for pieza in objetos[nombre]:
            pieza.data.transform(Matrix.Translation(base) @ Matrix.Scale(factor, 4) @ Matrix.Translation(-base))
    # Gotas cayendo sobre la maceta, en dos tandas que se alternan.
    for tanda, desfase in (("gotas_a", 0.0), ("gotas_b", 0.05)):
        objetos[tanda] = [
            elipsoide(f"{tanda}_{i}", maceta + Vector((0.02 * (i - 1), -0.02, 0.32 + 0.1 * i + desfase)), (0.018, 0.018, 0.03), m["agua"])
            for i in range(3)
        ]
    return objetos, huesos


def construir_utiles_pintor(esqueleto, m, centro_lienzo) -> dict[str, list[bpy.types.Object]]:
    """Pincel y paleta, armados con Nailong ya en la pose de pintar.

    Así el pincel sale de la mano apuntando al lienzo y la paleta queda de cara
    al jugador justo en esa pose; luego se pegan a las manos y las siguen.
    """
    from poses import dibujar

    pose = dibujar(0.0, "feliz")
    for hueso in ("cuerpo", "brazo.L", "antebrazo.L", "brazo.R", "antebrazo.R"):
        esqueleto.pose.bones[hueso].rotation_euler = [radians(a) for a in pose.get(hueso, {}).get("rot", (0, 0, 0))]
    bpy.context.view_layer.update()
    mano = lambda lado: esqueleto.matrix_world @ esqueleto.pose.bones[f"antebrazo.{lado}"].tail

    # El pincel va de la mano hasta casi tocar el lienzo, con la punta mojada.
    inicio, objetivo = mano("L"), centro_lienzo + Vector((-0.1, 0.08, 0.06))
    direccion = (objetivo - inicio).normalized()
    largo = (objetivo - inicio).length - 0.03
    pincel = [
        barra("pincel_mango", inicio - direccion * 0.06, inicio + direccion * (largo - 0.05), 0.036, m["madera"]),
        elipsoide("pincel_punta", inicio + direccion * largo, (0.05, 0.05, 0.05), m["lapiz"]),
    ]
    # La paleta frente a la mano derecha, con tres colores mirando al jugador.
    cara = Vector((0.2, -1, 0.35)).normalized()
    centro = mano("R") + Vector((0.03, -0.07, 0.02))
    eje_x = cara.cross(Vector((0, 0, 1))).normalized()
    eje_y = cara.cross(eje_x)
    paleta = [orientado("paleta", centro, (0.15, 0.11, 0.022), cara, m["madera"])] + [
        orientado(f"paleta_color_{i}", centro + cara * 0.02 + eje_x * dx + eje_y * dy, (0.04, 0.04, 0.012), cara, m[color])
        for i, (dx, dy, color) in enumerate(((-0.07, 0.02, "lapiz"), (0.0, -0.05, "planta"), (0.07, 0.02, "regadera")))
    ]
    pegar(pincel, esqueleto, "antebrazo.L")
    pegar(paleta, esqueleto, "antebrazo.R")
    for hueso in esqueleto.pose.bones:
        hueso.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()
    return {"pincel": pincel, "paleta": paleta}


def construir_cubeta(esqueleto, m) -> list[bpy.types.Object]:
    """Cubeta de calabaza colgando de la mano izquierda en la pose de truco o trato.

    Se arma con Nailong en esa pose para que cuelgue derecha del asa, y luego
    se pega a la mano.
    """
    from poses import truco_o_trato

    pose = truco_o_trato(0.0, "feliz")
    for hueso in ("cuerpo", "brazo.L", "antebrazo.L"):
        esqueleto.pose.bones[hueso].rotation_euler = [radians(a) for a in pose.get(hueso, {}).get("rot", (0, 0, 0))]
    bpy.context.view_layer.update()
    mano = esqueleto.matrix_world @ esqueleto.pose.bones["antebrazo.L"].tail
    centro = mano + Vector((0.08, -0.08, -0.28))
    cubeta = cuenco("cubeta", centro + Vector((0, 0, 0.12)), (0.19, 0.19, 0.21), m["calabaza"])
    for v in cubeta.data.vertices:
        relativo = v.co - centro
        gajo = 1 - 0.1 * abs(sin(4 * np.arctan2(relativo.y, relativo.x))) ** 0.7
        v.co.x, v.co.y = centro.x + relativo.x * gajo, centro.y + relativo.y * gajo
    cubeta.data.update()
    frente = centro + Vector((0, -0.19, 0))
    piezas = [
        cubeta,
        *[cono(f"cubeta_ojo_{lado}", frente + Vector((0.07 * lado, 0, 0.01)), frente + Vector((0.07 * lado, 0, 0.09)), 0.05, 0.0, m["negro"], 0.3)
          for lado in (-1, 1)],
        orientado("cubeta_boca", frente + Vector((0, 0, -0.06)), (0.1, 0.03, 0.02), (0, -1, 0), m["negro"]),
        barra("cubeta_asa_1", centro + Vector((-0.16, 0, 0.12)), mano + Vector((0, 0, 0.02)), 0.018, m["negro"]),
        barra("cubeta_asa_2", centro + Vector((0.16, 0, 0.12)), mano + Vector((0, 0, 0.02)), 0.018, m["negro"]),
    ]
    pegar(piezas, esqueleto, "antebrazo.L")
    for hueso in esqueleto.pose.bones:
        hueso.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()
    return piezas


def construir() -> Modelo:
    """Arma la escena completa y devuelve el esqueleto con sus ranuras."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    materiales = crear_materiales()
    tronco = construir_tronco(materiales)
    cabeza = construir_cabeza(materiales)
    extremidades = construir_extremidades(materiales)
    marcas, extras = construir_cara(cabeza, materiales)
    crestas = construir_crestas(cabeza, materiales)
    gorra = construir_gorra(materiales)
    disfraces = construir_disfraces(materiales)
    objetos, huesos_objetos = construir_objetos(cabeza, materiales)

    esqueleto = crear_esqueleto()
    deformar(tronco, esqueleto)
    for hueso, piezas in extremidades.items():
        pegar(piezas, esqueleto, hueso)
    pegar([cabeza, *crestas], esqueleto, "cabeza")
    pegar(marcas, esqueleto, "cabeza")
    for piezas in extras.values():
        pegar(piezas, esqueleto, "cabeza")
    pegar(gorra, esqueleto, "cabeza")
    prendas = {"gorra": gorra}
    for nombre, grupos in disfraces.items():
        prendas[nombre] = []
        for hueso, piezas in grupos:
            pegar(piezas, esqueleto, hueso)
            prendas[nombre] += piezas
    for nombre, piezas in objetos.items():
        pegar(piezas, esqueleto, huesos_objetos.get(nombre, "raiz"))
    objetos.update(construir_utiles_pintor(esqueleto, materiales, CENTRO_LIENZO))
    objetos["cubeta"] = construir_cubeta(esqueleto, materiales)
    return Modelo(esqueleto, extras, prendas, objetos, crestas, [cabeza, *marcas])


def vestir(modelo: Modelo, extras: list[str], prendas: list[str], objetos: list[str] = ()):
    """Muestra solo los extras de la cara, las prendas y los objetos pedidos."""
    for nombre, piezas in modelo.extras.items():
        for pieza in piezas:
            pieza.hide_render = nombre not in extras
    for nombre, piezas in modelo.prendas.items():
        for pieza in piezas:
            pieza.hide_render = nombre not in prendas
    for nombre, piezas in modelo.objetos.items():
        for pieza in piezas:
            pieza.hide_render = nombre not in objetos
    for cresta in modelo.crestas:
        cresta.hide_render = bool(TAPAN_CRESTAS & set(prendas))
    if TAPAN_CABEZA & set(prendas):
        for pieza in [*modelo.cabeza, *(p for piezas in modelo.extras.values() for p in piezas)]:
            pieza.hide_render = True
    else:
        for pieza in modelo.cabeza:
            pieza.hide_render = False
