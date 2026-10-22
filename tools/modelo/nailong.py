"""Construye el modelo 3D de Nailong en Blender: piezas, esqueleto y ranuras.

Cada pieza es una malla rígida pegada a un hueso, como en la animación por
recortes, pero en 3D: así se puede ver desde cualquier ángulo. Las prendas y
las caras de cada estado de ánimo son piezas más, pegadas a la ranura que les
corresponde y que se muestran u ocultan según la combinación pedida.

Medidas en unidades de Blender: Z hacia arriba, Nailong mira hacia -Y y los
pies tocan Z = 0. La altura total ronda las 2,05 unidades.
"""

from dataclasses import dataclass, field
from math import radians

import bpy
from mathutils import Matrix, Vector


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
    "pupila",
    "iris",
    "brillo",
    "boca",
    "ceja",
    "mejilla",
    "lagrima",
    "gorra",
    "visera",
]

HUESOS = {
    # nombre: (cabeza, cola, padre)
    "raiz": ((0, 0, 0), (0, 0, 0.3), None),
    "cuerpo": ((0, 0, 0.5), (0, 0, 1.1), "raiz"),
    "cabeza": ((0, 0, 1.1), (0, 0, 1.9), "cuerpo"),
    "brazo.R": ((-0.38, -0.04, 1.0), (-0.49, -0.15, 0.66), "cuerpo"),
    "brazo.L": ((0.38, -0.04, 1.0), (0.49, -0.15, 0.66), "cuerpo"),
    "pierna.R": ((-0.2, 0, 0.42), (-0.2, 0, 0.08), "raiz"),
    "pierna.L": ((0.2, 0, 0.42), (0.2, 0, 0.08), "raiz"),
    "cola": ((0, 0.3, 0.45), (0, 0.75, 0.2), "cuerpo"),
}


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


def elipsoide(nombre, centro, radios, material, rotacion=(0, 0, 0), segmentos=32):
    """Crea un elipsoide suave con las transformaciones ya aplicadas."""
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segmentos, ring_count=segmentos // 2)
    objeto = bpy.context.object
    objeto.name = nombre
    objeto.scale = radios
    objeto.rotation_euler = [radians(angulo) for angulo in rotacion]
    objeto.location = centro
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.shade_smooth()
    objeto.data.materials.append(material)
    return objeto


def cono(nombre, base, punta, radio, material):
    """Crea un cono que va de la base a la punta, para púas y garras."""
    direccion = Vector(punta) - Vector(base)
    bpy.ops.mesh.primitive_cone_add(vertices=12, radius1=radio, depth=direccion.length)
    objeto = bpy.context.object
    objeto.name = nombre
    objeto.rotation_euler = direccion.to_track_quat("Z", "Y").to_euler()
    objeto.location = Vector(base) + direccion / 2
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    objeto.data.materials.append(material)
    return objeto


def trazo(nombre, puntos, grosor, material):
    """Crea un trazo curvo con volumen, para bocas y cejas."""
    curva = bpy.data.curves.new(nombre, "CURVE")
    curva.dimensions = "3D"
    curva.bevel_depth = grosor
    curva.bevel_resolution = 2
    linea = curva.splines.new("POLY")
    linea.points.add(len(puntos) - 1)
    for punto, coordenada in zip(linea.points, puntos):
        punto.co = (*coordenada, 1)
    curva.materials.append(material)
    objeto = bpy.data.objects.new(nombre, curva)
    bpy.context.collection.objects.link(objeto)
    return objeto


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


def pegar(objetos, esqueleto, hueso):
    """Pega las piezas a un hueso sin moverlas de donde fueron modeladas."""
    bpy.context.view_layer.update()
    matriz_hueso = esqueleto.matrix_world @ esqueleto.pose.bones[hueso].matrix
    matriz_cola = matriz_hueso @ Matrix.Translation((0, esqueleto.data.bones[hueso].length, 0))
    for objeto in objetos:
        objeto.parent = esqueleto
        objeto.parent_type = "BONE"
        objeto.parent_bone = hueso
        objeto.matrix_parent_inverse = matriz_cola.inverted()


def construir_cuerpo(m):
    torso = elipsoide("torso", (0, 0.02, 0.7), (0.47, 0.39, 0.5), m["piel"])
    panza = elipsoide("panza", (0, -0.22, 0.68), (0.32, 0.2, 0.38), m["panza"])
    return [torso, panza]


def construir_cabeza(m):
    craneo = elipsoide("craneo", (0, 0, 1.56), (0.52, 0.47, 0.47), m["piel"])
    hocico = elipsoide("hocico", (0, -0.24, 1.44), (0.34, 0.26, 0.24), m["piel"])
    return [craneo, hocico]


def construir_ojos(m, nombre, alto, inclinacion):
    """Crea los dos ojos con pupila, iris y brillo; el alto cambia con el ánimo."""
    piezas = []
    for lado in (-1, 1):
        x = 0.21 * lado
        rotacion = (0, -inclinacion * lado, 0)
        piezas += [
            elipsoide(f"{nombre}_pupila_{lado}", (x, -0.41, 1.6), (0.1, 0.06, alto), m["pupila"], rotacion),
            elipsoide(f"{nombre}_iris_{lado}", (x, -0.445, 1.585), (0.075, 0.04, alto * 0.7), m["iris"], rotacion),
            elipsoide(f"{nombre}_brillo_{lado}", (x + 0.03, -0.47, 1.635), (0.035, 0.02, 0.035), m["brillo"]),
        ]
    return piezas


def construir_caras(m) -> dict[str, list[bpy.types.Object]]:
    """Crea una cara por estado de ánimo; solo una se muestra a la vez."""
    feliz = construir_ojos(m, "feliz", 0.125, 0)
    feliz.append(trazo("feliz_boca", [(-0.14, -0.48, 1.45), (-0.06, -0.5, 1.39), (0.06, -0.5, 1.39), (0.14, -0.48, 1.45)], 0.02, m["boca"]))
    feliz += [elipsoide(f"feliz_mejilla_{lado}", (0.33 * lado, -0.36, 1.45), (0.07, 0.04, 0.04), m["mejilla"]) for lado in (-1, 1)]

    triste = construir_ojos(m, "triste", 0.09, 0)
    triste.append(trazo("triste_boca", [(-0.12, -0.48, 1.36), (-0.05, -0.5, 1.41), (0.05, -0.5, 1.41), (0.12, -0.48, 1.36)], 0.02, m["boca"]))
    triste += [trazo(f"triste_ceja_{lado}", [(0.1 * lado, -0.47, 1.75), (0.27 * lado, -0.42, 1.7)], 0.022, m["ceja"]) for lado in (-1, 1)]
    triste.append(elipsoide("triste_lagrima", (0.25, -0.43, 1.5), (0.035, 0.03, 0.05), m["lagrima"]))

    return {"feliz": feliz, "triste": triste}


def construir_brazo(m, lado):
    brazo = elipsoide(f"brazo_{lado}", (0.44 * lado, -0.08, 0.84), (0.11, 0.11, 0.21), m["piel"], (-15, 12 * lado, 0))
    palma = elipsoide(f"palma_{lado}", (0.49 * lado, -0.15, 0.66), (0.075, 0.07, 0.07), m["palma"])
    return [brazo, palma]


def construir_pierna(m, lado):
    x = 0.2 * lado
    muslo = elipsoide(f"pierna_{lado}", (x, 0, 0.24), (0.19, 0.19, 0.22), m["piel"])
    pie = elipsoide(f"pie_{lado}", (x, -0.06, 0.07), (0.17, 0.24, 0.08), m["piel"])
    garras = [
        cono(f"garra_{lado}_{dedo}", (x + 0.08 * dedo, -0.26, 0.05), (x + 0.09 * dedo, -0.34, 0.03), 0.035, m["garra"])
        for dedo in (-1, 0, 1)
    ]
    return [muslo, pie, *garras]


def construir_cola(m):
    cola = elipsoide("cola", (0, 0.45, 0.36), (0.12, 0.28, 0.12), m["piel"], (35, 0, 0))
    puas = [
        cono(f"pua_{indice}", (0, 0.36 + 0.13 * indice, 0.5 - 0.1 * indice), (0, 0.42 + 0.13 * indice, 0.62 - 0.1 * indice), 0.05, m["piel"])
        for indice in range(3)
    ]
    return [cola, *puas]


def construir_gorra(m):
    copa = elipsoide("gorra_copa", (0, 0.05, 1.7), (0.5, 0.48, 0.32), m["gorra"], (-22, 0, 0))
    visera = elipsoide("gorra_visera", (0, -0.43, 1.8), (0.32, 0.22, 0.035), m["visera"], (-10, 0, 0))
    return [copa, visera]


def construir() -> Modelo:
    """Arma la escena completa y devuelve el esqueleto con sus ranuras."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    materiales = crear_materiales()
    esqueleto = crear_esqueleto()
    modelo = Modelo(esqueleto)

    pegar(construir_cuerpo(materiales), esqueleto, "cuerpo")
    pegar(construir_cabeza(materiales), esqueleto, "cabeza")
    for lado, sufijo in ((-1, "R"), (1, "L")):
        pegar(construir_brazo(materiales, lado), esqueleto, f"brazo.{sufijo}")
        pegar(construir_pierna(materiales, lado), esqueleto, f"pierna.{sufijo}")
    pegar(construir_cola(materiales), esqueleto, "cola")

    modelo.caras = construir_caras(materiales)
    for piezas in modelo.caras.values():
        pegar(piezas, esqueleto, "cabeza")

    modelo.prendas = {"gorra": construir_gorra(materiales)}
    pegar(modelo.prendas["gorra"], esqueleto, "cabeza")
    return modelo


def vestir(modelo: Modelo, cara: str, prendas: list[str]):
    """Muestra solo la cara y las prendas pedidas."""
    for nombre, piezas in modelo.caras.items():
        for pieza in piezas:
            pieza.hide_render = nombre != cara
    for nombre, piezas in modelo.prendas.items():
        for pieza in piezas:
            pieza.hide_render = nombre not in prendas
