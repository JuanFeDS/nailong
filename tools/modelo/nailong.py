"""Construye el modelo 3D de Nailong en Blender: cuerpo, esqueleto y ranuras.

El tronco (cabeza y cuerpo) es una sola superficie definida por sus siluetas:
el ancho visto de frente y cuánto sobresale hacia adelante y hacia atrás visto
de perfil, a cada altura. El esqueleto lo deforma. Brazos, piernas y cola son
volúmenes suaves que se funden como plastilina (metaballs). Los ojos, las garras, las caras de cada estado de ánimo y las prendas son piezas
aparte pegadas a un hueso, que se muestran u ocultan según la combinación
pedida.

Medidas en unidades de Blender: Z hacia arriba, Nailong mira hacia -Y y los
pies tocan Z = 0. La altura total ronda las 2 unidades.
"""

from dataclasses import dataclass, field
from math import cos, pi, radians, sin

import bpy
import numpy as np
from mathutils import Euler, Matrix, Vector


@dataclass
class Modelo:
    """Referencias al modelo construido que necesitan el render y las poses."""

    esqueleto: bpy.types.Object
    caras: dict[str, list[bpy.types.Object]] = field(default_factory=dict)
    prendas: dict[str, list[bpy.types.Object]] = field(default_factory=dict)


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
    "gorra",
    "visera",
]

HUESOS = {
    # nombre: (cabeza, cola, padre)
    "raiz": ((0, 0, 0), (0, 0, 0.3), None),
    "cuerpo": ((0, 0, 0.35), (0, 0, 1.15), "raiz"),
    "cabeza": ((0, -0.08, 1.13), (0, -0.08, 1.96), "cuerpo"),
    "brazo.R": ((-0.42, -0.06, 0.95), (-0.61, -0.28, 0.69), "cuerpo"),
    "brazo.L": ((0.42, -0.06, 0.95), (0.61, -0.28, 0.69), "cuerpo"),
    "pierna.R": ((-0.25, 0, 0.36), (-0.25, -0.02, 0.04), "raiz"),
    "pierna.L": ((0.25, 0, 0.36), (0.25, -0.02, 0.04), "raiz"),
    "cola": ((0, 0.3, 0.38), (0, 0.78, 0.1), "cuerpo"),
}

# Siluetas del tronco: (altura, medio ancho de frente, hacia adelante, hacia atrás).
# Por encima de la última fila la cabeza se cierra en una cúpula.
PERFIL = [
    (0.1, 0.34, 0.26, 0.26),
    (0.22, 0.45, 0.37, 0.35),
    (0.4, 0.49, 0.43, 0.38),
    (0.62, 0.47, 0.42, 0.36),
    (0.84, 0.42, 0.37, 0.32),
    (1.03, 0.41, 0.35, 0.3),
    # Cuello: el quiebre bajo la barbilla que separa la cabeza del cuerpo.
    (1.13, 0.43, 0.39, 0.31),
    (1.22, 0.47, 0.5, 0.34),
    (1.34, 0.56, 0.64, 0.43),
    (1.44, 0.57, 0.66, 0.46),
    (1.5, 0.565, 0.65, 0.47),
]
ALTO_CUPULA = 0.46
# Exponente de la sección: 2 es una elipse; más alto la hace más cuadrada.
REDONDEZ = 2.15
FILAS, COLUMNAS = 90, 64

# Extremidades como volúmenes que se funden: (centro, radios, rotación en grados).
BRAZO = [
    ((0.42, -0.06, 0.95), (0.13, 0.13, 0.14), (0, 0, 0)),
    ((0.51, -0.15, 0.83), (0.1, 0.1, 0.16), (-35, 30, 0)),
    ((0.59, -0.23, 0.72), (0.1, 0.095, 0.1), (0, 0, 0)),
]
MANO = Vector((0.61, -0.28, 0.69))
PIERNA = [
    ((0.25, -0.02, 0.2), (0.2, 0.22, 0.19), (0, 0, 0)),
    ((0.25, -0.08, 0.07), (0.19, 0.23, 0.075), (0, 0, 0)),
]
COLA = [
    ((0, 0.4, 0.24), (0.17, 0.3, 0.13), (18, 0, 0)),
    ((0, 0.66, 0.12), (0.08, 0.17, 0.065), (18, 0, 0)),
]

RESOLUCION = 0.02
# Radio de la superficie de un metaball respecto a su radio de influencia.
ALCANCE_METABALL = 0.575


def color_identificador(indice: int) -> tuple[float, float, float, float]:
    """Devuelve un color plano distinto para cada material, legible tras el render."""
    return ((indice + 1) * 12 / 255, 0.0, 0.0, 1.0)


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
    """Calcula ancho, frente y espalda en cada fila, cerrando la cabeza en cúpula."""
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
            # La cúpula usa un cuarto de elipse para cerrar la cabeza sin pico.
            angulo = (recorrido - alto_cuerpo) / ALTO_CUPULA * pi / 2
            z = tope + ALTO_CUPULA * sin(angulo)
            factor = cos(angulo)
            _, ancho, frente, atras = PERFIL[-1]
            ancho, frente, atras = ancho * factor, frente * factor, atras * factor
        resultado.append((z, ancho, frente, atras))
    return resultado


def superelipse(angulo: float) -> tuple[float, float]:
    coseno, seno = cos(angulo), sin(angulo)
    exponente = 2 / REDONDEZ
    return (
        (abs(coseno) ** exponente) * (1 if coseno >= 0 else -1),
        (abs(seno) ** exponente) * (1 if seno >= 0 else -1),
    )


def construir_tronco(materiales) -> bpy.types.Object:
    """Levanta la superficie del tronco fila por fila a partir de las siluetas."""
    vertices, caras = [], []
    filas = secciones()
    for z, ancho, frente, atras in filas:
        for columna in range(COLUMNAS):
            x, y = superelipse(columna / COLUMNAS * 2 * pi)
            vertices.append((x * ancho, y * (atras if y > 0 else frente), z))
    for fila in range(len(filas) - 1):
        for columna in range(COLUMNAS):
            siguiente = (columna + 1) % COLUMNAS
            a, b = fila * COLUMNAS + columna, fila * COLUMNAS + siguiente
            caras.append((a, b, b + COLUMNAS, a + COLUMNAS))
    vertices.append((0, 0, filas[0][0] - 0.02))
    fondo = len(vertices) - 1
    caras += [((columna + 1) % COLUMNAS, columna, fondo) for columna in range(COLUMNAS)]

    malla = bpy.data.meshes.new("tronco")
    malla.from_pydata(vertices, [], caras)
    malla.validate()
    tronco = bpy.data.objects.new("tronco", malla)
    bpy.context.collection.objects.link(tronco)
    for poligono in malla.polygons:
        poligono.use_smooth = True
    malla.update()

    for nombre in ("piel", "panza"):
        malla.materials.append(materiales[nombre])
    for cara in malla.polygons:
        centro, normal = cara.center, cara.normal
        panza = (centro.x / 0.31) ** 2 + ((centro.z - 0.6) / 0.4) ** 2 < 1 and normal.y < -0.3
        cara.material_index = 1 if panza else 0
    return tronco


def pintar_palma(brazo, materiales, mano):
    """Marca como palma rosada la punta de la mano que mira al frente."""
    for nombre in ("piel", "palma"):
        brazo.data.materials.append(materiales[nombre])
    for cara in brazo.data.polygons:
        frente = cara.normal.y < -0.2
        cara.material_index = 1 if frente and (cara.center - mano).length < 0.08 else 0


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
        mezcla = min(max((vertice.co.z - 1.05) / 0.17, 0), 1)
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
        mano = Vector((MANO.x * lado, MANO.y, MANO.z))
        brazo = fundir(BRAZO, f"brazo_{sufijo}", lado)
        pintar_palma(brazo, m, mano)
        garras_mano = []
        for dedo in (-1, 0, 1):
            origen = mano + Vector((0.06 * dedo, -0.5, 0.04 - 0.04 * abs(dedo)))
            punto, normal = superficie(brazo, origen, mano - origen + Vector((0, 0, -0.02)))
            garras_mano.append(orientado(f"garra_mano_{sufijo}_{dedo}", punto, (0.025, 0.025, 0.035), normal, m["garra"]))
        piezas[f"brazo.{sufijo}"] = [brazo, *garras_mano]

        pierna = fundir(PIERNA, f"pierna_{sufijo}", lado)
        pierna.data.materials.append(m["piel"])
        garras_pie = []
        for dedo in (-1, 0, 1):
            punto, normal = superficie(pierna, (0.25 * lado + 0.09 * dedo, -2, 0.05), (0, 1, 0))
            garras_pie.append(orientado(f"garra_pie_{sufijo}_{dedo}", punto, (0.035, 0.03, 0.04), normal, m["garra"]))
        piezas[f"pierna.{sufijo}"] = [pierna, *garras_pie]
    return piezas


def construir_ojos(cuerpo, m, prefijo):
    """Marca dónde va cada ojo; el render dibuja sus píxeles con una regla fija."""
    piezas, posiciones = [], []
    for lado in (-1, 1):
        punto, normal = superficie(cuerpo, (0.26 * lado, -2, 1.53), (0, 1, 0))
        piezas.append(orientado(f"{prefijo}_ojo_{lado}", punto, (0.11, 0.135, 0.03), normal, m["ojo"]))
        posiciones.append((punto, normal))
    return piezas, posiciones


def construir_caras(cuerpo, m) -> dict[str, list[bpy.types.Object]]:
    """Crea una cara por estado de ánimo; solo una se muestra a la vez."""
    def boca(prefijo, curvatura):
        puntos = []
        for x in (-0.11, 0, 0.11):
            z = 1.36 + (curvatura if x == 0 else 0)
            punto, normal = superficie(cuerpo, (x, -2, z), (0, 1, 0))
            puntos.append(punto + normal * 0.01)
        return trazo(f"{prefijo}_boca", puntos, 0.013, m["boca"])

    feliz, _ = construir_ojos(cuerpo, m, "feliz")
    feliz.append(boca("feliz", -0.04))

    triste, ojos = construir_ojos(cuerpo, m, "triste")
    triste.append(boca("triste", 0.03))
    for lado, (punto, normal) in zip((-1, 1), ojos):
        parpado = orientado(
            f"triste_parpado_{lado}", punto + normal * 0.02 + Vector((0, 0, 0.1)), (0.15, 0.08, 0.07), normal, m["parpado"], 18 * lado
        )
        triste.append(parpado)
    punto, normal = ojos[1]
    triste.append(elipsoide("triste_lagrima", punto + normal * 0.05 + Vector((0.06, 0, -0.14)), (0.03, 0.025, 0.045), m["lagrima"]))
    return {"feliz": feliz, "triste": triste}


def construir_gorra(m):
    copa = elipsoide("gorra_copa", (0, -0.08, 1.78), (0.6, 0.7, 0.3), m["gorra"], (-12, 0, 0))
    visera = elipsoide("gorra_visera", (0, -0.74, 1.82), (0.36, 0.25, 0.035), m["visera"], (-8, 0, 0))
    return [copa, visera]


def construir() -> Modelo:
    """Arma la escena completa y devuelve el esqueleto con sus ranuras."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    materiales = crear_materiales()
    tronco = construir_tronco(materiales)
    extremidades = construir_extremidades(materiales)
    caras = construir_caras(tronco, materiales)
    gorra = construir_gorra(materiales)

    esqueleto = crear_esqueleto()
    deformar(tronco, esqueleto)
    for hueso, piezas in extremidades.items():
        pegar(piezas, esqueleto, hueso)
    for piezas in caras.values():
        pegar(piezas, esqueleto, "cabeza")
    pegar(gorra, esqueleto, "cabeza")
    return Modelo(esqueleto, caras, {"gorra": gorra})


def vestir(modelo: Modelo, cara: str, prendas: list[str]):
    """Muestra solo la cara y las prendas pedidas."""
    for nombre, piezas in modelo.caras.items():
        for pieza in piezas:
            pieza.hide_render = nombre != cara
    for nombre, piezas in modelo.prendas.items():
        for pieza in piezas:
            pieza.hide_render = nombre not in prendas
