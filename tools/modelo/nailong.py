"""Construye el modelo 3D de Nailong en Blender: cuerpo, esqueleto y ranuras.

El cuerpo es una sola malla suave: se arma con volúmenes simples que se funden
entre sí como plastilina (metaballs), y el esqueleto la deforma. Los
ojos, las garras, las caras de cada estado de ánimo y las prendas son piezas
aparte pegadas a un hueso, que se muestran u ocultan según la combinación
pedida.

Medidas en unidades de Blender: Z hacia arriba, Nailong mira hacia -Y y los
pies tocan Z = 0. La altura total ronda las 2 unidades.
"""

from dataclasses import dataclass, field
from math import radians

import bpy
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
    "esclerotica",
    "iris",
    "pupila",
    "brillo",
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
    "cabeza": ((0, -0.12, 1.2), (0, -0.12, 2.0), "cuerpo"),
    "brazo.R": ((-0.48, -0.1, 1.0), (-0.66, -0.26, 0.76), "cuerpo"),
    "brazo.L": ((0.48, -0.1, 1.0), (0.66, -0.26, 0.76), "cuerpo"),
    "pierna.R": ((-0.24, 0, 0.36), (-0.24, -0.02, 0.04), "raiz"),
    "pierna.L": ((0.24, 0, 0.36), (0.24, -0.02, 0.04), "raiz"),
    "cola": ((0, 0.3, 0.38), (0, 0.78, 0.1), "cuerpo"),
}

# Volúmenes que forman el cuerpo antes de fundirlos: (centro, radios, rotación).
VOLUMENES = [
    # Cabeza en forma de frijol, más larga hacia adelante y ancha abajo.
    ((0, -0.14, 1.62), (0.5, 0.58, 0.42), (0, 0, 0)),
    ((0, -0.24, 1.42), (0.5, 0.46, 0.3), (0, 0, 0)),
    # Cuerpo en forma de pera.
    ((0, 0.03, 0.78), (0.5, 0.43, 0.5), (0, 0, 0)),
    ((0, 0.03, 0.5), (0.53, 0.46, 0.38), (0, 0, 0)),
    # Piernas cortas y pies.
    ((-0.24, 0, 0.2), (0.2, 0.21, 0.2), (0, 0, 0)),
    ((0.24, 0, 0.2), (0.2, 0.21, 0.2), (0, 0, 0)),
    ((-0.24, -0.08, 0.07), (0.18, 0.25, 0.08), (0, 0, 0)),
    ((0.24, -0.08, 0.07), (0.18, 0.25, 0.08), (0, 0, 0)),
    # Cola corta y gruesa.
    ((0, 0.34, 0.3), (0.22, 0.32, 0.18), (30, 0, 0)),
    ((0, 0.62, 0.14), (0.1, 0.18, 0.08), (30, 0, 0)),
]

# Brazos como cápsulas del hombro a la mano: (hombro, mano, radio).
BRAZOS = [((-0.48, -0.1, 1.0), (-0.66, -0.26, 0.76), 0.1), ((0.48, -0.1, 1.0), (0.66, -0.26, 0.76), 0.1)]

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


def capsula(inicio, fin, radio):
    """Volumen alargado que une dos puntos, en el formato de VOLUMENES."""
    inicio, fin = Vector(inicio), Vector(fin)
    direccion = fin - inicio
    return (inicio + fin) / 2, (radio, radio, direccion.length / 2 + radio * 0.6), direccion.to_track_quat("Z", "Y")


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


def fundir(volumenes, nombre: str) -> bpy.types.Object:
    """Funde los volúmenes (centro, radios, rotación) en una sola malla continua."""
    datos = bpy.data.metaballs.new(nombre)
    datos.resolution = datos.render_resolution = RESOLUCION
    for centro, radios, rotacion in volumenes:
        elemento = datos.elements.new()
        elemento.type = "ELLIPSOID"
        elemento.co = centro
        elemento.radius = max(radios) / ALCANCE_METABALL
        elemento.size_x, elemento.size_y, elemento.size_z = (radio / max(radios) for radio in radios)
        elemento.rotation = rotacion
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


def pintar_regiones(cuerpo, materiales):
    """Asigna la panza y las palmas a las caras de la malla según su posición."""
    for nombre in ("piel", "panza", "palma"):
        cuerpo.data.materials.append(materiales[nombre])
    manos = [Vector(mano) for _, mano, _ in BRAZOS]
    for cara in cuerpo.data.polygons:
        centro, normal = cara.center, cara.normal
        panza = (centro.x / 0.36) ** 2 + ((centro.z - 0.66) / 0.42) ** 2 < 1 and normal.y < -0.25
        palma = any((centro - mano).length < 0.1 and normal.y < 0.2 for mano in manos)
        cara.material_index = 2 if palma else 1 if panza else 0


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


def deformar(cuerpo, esqueleto):
    """Hace que el esqueleto deforme la malla, con pesos calculados solos."""
    bpy.ops.object.select_all(action="DESELECT")
    cuerpo.select_set(True)
    esqueleto.select_set(True)
    bpy.context.view_layer.objects.active = esqueleto
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")


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


def construir_cuerpo(materiales) -> bpy.types.Object:
    volumenes = [
        (centro, radios, Euler([radians(angulo) for angulo in rotacion]).to_quaternion())
        for centro, radios, rotacion in VOLUMENES
    ]
    volumenes += [capsula(*brazo) for brazo in BRAZOS]
    cuerpo = fundir(volumenes, "cuerpo")
    pintar_regiones(cuerpo, materiales)
    return cuerpo


def construir_garras(cuerpo, m):
    """Tres garras oscuras al frente de cada pie y en la punta de cada mano."""
    pies, manos = [], {-1: [], 1: []}
    for lado in (-1, 1):
        for dedo in (-1, 0, 1):
            punto, normal = superficie(cuerpo, (0.24 * lado + 0.09 * dedo, -2, 0.05), (0, 1, 0))
            pies.append(orientado(f"garra_pie_{lado}_{dedo}", punto, (0.035, 0.03, 0.04), normal, m["garra"]))
        hombro, mano, _ = BRAZOS[0 if lado < 0 else 1]
        direccion = (Vector(mano) - Vector(hombro)).normalized()
        for dedo in (-1, 0, 1):
            origen = Vector(mano) + direccion * 0.6 + Vector((0.05 * dedo * lado, -0.03, 0.05 * dedo))
            punto, normal = superficie(cuerpo, origen, -direccion)
            manos[lado].append(orientado(f"garra_mano_{lado}_{dedo}", punto, (0.025, 0.025, 0.035), normal, m["garra"]))
    return pies, manos


def construir_ojos(cuerpo, m, prefijo):
    """Ojos grandes: blanco, aro verde, pupila negra y un brillo."""
    piezas, posiciones = [], []
    for lado in (-1, 1):
        punto, normal = superficie(cuerpo, (0.23 * lado, -2, 1.6), (0, 1, 0))
        normal = (normal + Vector((0.12 * lado, 0, 0))).normalized()
        frente = lambda distancia: punto + normal * distancia  # noqa: E731
        piezas += [
            orientado(f"{prefijo}_esclerotica_{lado}", frente(-0.02), (0.13, 0.14, 0.05), normal, m["esclerotica"]),
            orientado(f"{prefijo}_iris_{lado}", frente(0.008), (0.1, 0.11, 0.025), normal, m["iris"]),
            orientado(f"{prefijo}_pupila_{lado}", frente(0.018), (0.075, 0.085, 0.02), normal, m["pupila"]),
            orientado(f"{prefijo}_brillo_{lado}", frente(0.03) + Vector((0.03, 0, 0.04)), (0.025, 0.025, 0.01), normal, m["brillo"]),
        ]
        posiciones.append((punto, normal))
    return piezas, posiciones


def construir_caras(cuerpo, m) -> dict[str, list[bpy.types.Object]]:
    """Crea una cara por estado de ánimo; solo una se muestra a la vez."""
    def boca(prefijo, curvatura):
        puntos = []
        for x in (-0.13, 0, 0.13):
            z = 1.42 + (curvatura if x == 0 else 0)
            punto, normal = superficie(cuerpo, (x, -2, z), (0, 1, 0))
            puntos.append(punto + normal * 0.01)
        return trazo(f"{prefijo}_boca", puntos, 0.018, m["boca"])

    feliz, _ = construir_ojos(cuerpo, m, "feliz")
    feliz.append(boca("feliz", -0.05))

    triste, ojos = construir_ojos(cuerpo, m, "triste")
    triste.append(boca("triste", 0.035))
    for lado, (punto, normal) in zip((-1, 1), ojos):
        parpado = orientado(
            f"triste_parpado_{lado}", punto + normal * 0.02 + Vector((0, 0, 0.1)), (0.15, 0.08, 0.07), normal, m["parpado"], -18 * lado
        )
        triste.append(parpado)
    punto, normal = ojos[1]
    triste.append(elipsoide("triste_lagrima", punto + normal * 0.05 + Vector((0.06, 0, -0.14)), (0.03, 0.025, 0.045), m["lagrima"]))
    return {"feliz": feliz, "triste": triste}


def construir_gorra(m):
    copa = elipsoide("gorra_copa", (0, -0.1, 1.82), (0.53, 0.62, 0.3), m["gorra"], (-12, 0, 0))
    visera = elipsoide("gorra_visera", (0, -0.7, 1.88), (0.34, 0.24, 0.035), m["visera"], (-8, 0, 0))
    return [copa, visera]


def construir() -> Modelo:
    """Arma la escena completa y devuelve el esqueleto con sus ranuras."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    materiales = crear_materiales()
    cuerpo = construir_cuerpo(materiales)
    pies, manos = construir_garras(cuerpo, materiales)
    caras = construir_caras(cuerpo, materiales)
    gorra = construir_gorra(materiales)

    esqueleto = crear_esqueleto()
    deformar(cuerpo, esqueleto)
    pegar(pies[:3], esqueleto, "pierna.R")
    pegar(pies[3:], esqueleto, "pierna.L")
    pegar(manos[-1], esqueleto, "brazo.R")
    pegar(manos[1], esqueleto, "brazo.L")
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
