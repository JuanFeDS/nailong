"""Prototipo de la sala modelada en 3D y renderizada como pixel art.

Usa la misma cámara de Nailong (ortográfica, 35° sobre el suelo) y una paleta por
material, para que el personaje y los muebles compartan perspectiva. Las
unidades de la escena son píxeles del juego (la sala mide 640x360).

Uso:
    .venv/Scripts/python.exe tools/modelo/sala.py -o public/rooms/prototipo_sala3d.png
    .venv/Scripts/python.exe tools/modelo/sala.py -o public/rooms/fondo_sala3d.png --piezas public/rooms/objects3d

Con --piezas, el fondo sale sin muebles y cada mueble se guarda como sprite aparte,
recortado para que su borde inferior central caiga en la posición que usa el juego.
"""

import argparse
import random
import sys
import tempfile
from math import cos, pi, radians, sin
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))

from paleta import RAMPAS as RAMPAS_PERSONAJE  # noqa: E402
from paleta import a_rgb  # noqa: E402

# Se renderiza a la resolución del juego: un píxel del render es un píxel en pantalla.
ANCHO, ALTO = 640, 360
SUBMUESTREO = 4
ELEVACION = 35
ANCHO_JUEGO, ALTO_JUEGO = 640, 360
ALTO_PARED_JUEGO = 148
DISTANCIA_CAMARA = 2000
# La luz entra por la ventana: llega desde arriba, a la izquierda y desde el frente.
DIRECCION_LUZ = (-0.5, -0.45, 0.74)
INTENSIDAD_SOMBRA = 0.55

SEN, COS = sin(radians(ELEVACION)), cos(radians(ELEVACION))
ALTO_PARED = ALTO_PARED_JUEGO / COS
PROFUNDIDAD_PISO = (ALTO_JUEGO - ALTO_PARED_JUEGO) / SEN
OBJETIVO_Y = -(ALTO_JUEGO / 2 - ALTO_PARED_JUEGO) / SEN
ANCHO_SALA = ANCHO_JUEGO + 60
ALTO_BOISERIE = 60

# Rampas de 6 colores: contorno y cinco tonos de sombra a luz. Los de los muebles
# se tomaron de los sprites 2D de la sala para que conserven su calidez.
RAMPAS = {
    **RAMPAS_PERSONAJE,
    "pared": ["#2e2440", "#51527e", "#565984", "#5e6190", "#666a9a", "#7074a6"],
    "pared2": ["#2e2440", "#56588a", "#5e6194", "#666a9c", "#6e72a6", "#787cb0"],
    "boiserie": ["#3a1a0e", "#5a2c18", "#6a3522", "#7d402b", "#8a4932", "#9b5235"],
    "moldura": ["#4a2a1e", "#a15334", "#c06e45", "#d98a58", "#e8a670", "#f4c28e"],
    "zocalo": ["#2e1c2c", "#4a2c3e", "#594b69", "#614766", "#706085", "#7c6c90"],
    "suelo1": ["#3e2018", "#7d402b", "#8a4932", "#9b5235", "#ad5e3b", "#c06e45"],
    "suelo2": ["#3e2018", "#85442d", "#944c32", "#a15334", "#b3633c", "#c47a4e"],
    "suelo3": ["#3e2018", "#763c27", "#85442d", "#9b5644", "#a65a39", "#b8693f"],
    "suelo_base": ["#2a140e", "#3e2018", "#532b23", "#5a2e24", "#6a3522", "#763c27"],
    "clavo": ["#2a140e", "#3e2018", "#532b23", "#532b23", "#5a2e24", "#5a2e24"],
    "alfombra": ["#1a4a50", "#2b7c82", "#3d969b", "#44999b", "#4ca1a1", "#57a39d"],
    "salvia": ["#2e5a50", "#66a99c", "#87b79c", "#94bc9d", "#a7c59d", "#b2cba2"],
    "crema": ["#8a6440", "#d8b07a", "#f0c88a", "#fdd49c", "#fde2b8", "#fff0d8"],
    "coral": ["#6a0e26", "#a91439", "#d32b44", "#f14b4c", "#fa6454", "#fd8a72"],
    "sillon": ["#6a2410", "#b95812", "#d66b13", "#f39918", "#fcb925", "#fdd36a"],
    "cojin": ["#1d2840", "#1d5864", "#256a73", "#2e8286", "#419d9a", "#5ab3a5"],
    "puf": ["#1d2840", "#1d5864", "#256a73", "#2e8286", "#419d9a", "#7cc8b8"],
    "madera": ["#3a1404", "#672609", "#9f4f15", "#c96317", "#e7831c", "#f2a24a"],
    "maceta": ["#5c2a1a", "#a8401e", "#de6331", "#eb7635", "#f4945a", "#f8b07a"],
    "planta": ["#1e3a1c", "#285a2f", "#4f6932", "#669332", "#84ac35", "#a7c535"],
    "cortina": ["#4a0a20", "#a91439", "#c92542", "#e43a47", "#f4544d", "#fa7a6a"],
    "cielo": ["#2b6fb5", "#41a6f6", "#73c8f7", "#a6e0fa", "#c8ecfc", "#e4f6ff"],
    "colina": ["#1e3a1c", "#285a2f", "#4f6932", "#669332", "#84ac35", "#a7c535"],
    "pantalla": ["#7a5320", "#dda458", "#fdd16b", "#fad987", "#fde39a", "#fef4d0"],
    "nube": ["#94b0c2", "#d8dde6", "#eef2f7", "#ffffff", "#ffffff", "#ffffff"],
    "montana": ["#3b4a7a", "#566a9a", "#7088b4", "#8aa2c8", "#a6bcdc", "#c0d0e8"],
    "puerta_verde": ["#14301a", "#285a2f", "#3d7a3a", "#4f8f44", "#66a64e", "#80bc60"],
    "comida": ["#3a1a0e", "#5c2a1a", "#7a3a20", "#9a4e2a", "#b86638", "#d08048"],
    "metal": ["#16161e", "#30303e", "#4c4c5e", "#6c6c82", "#9090a8", "#b4b4c8"],
    "dorado": ["#5c3a0a", "#a0700f", "#d8a528", "#f2cf5a", "#fbe7a0", "#fff4cc"],
    "libro_rojo": ["#3d0a10", "#7a1420", "#b8202c", "#d8343a", "#e85048", "#f07868"],
    "libro_azul": ["#0e1c40", "#1d3a6a", "#21436f", "#316b95", "#4a8ab4", "#72aacc"],
    "libro_verde": ["#0f3a22", "#1d6a3a", "#2f9a50", "#52c26c", "#8be0a0", "#b4f0c4"],
    "libro_crema": ["#8a6440", "#d8b07a", "#f0c88a", "#fdd49c", "#fde2b8", "#fff0d8"],
    "calabaza_h": ["#5c1f08", "#b8400c", "#e8600f", "#f58a2a", "#f9a84a", "#fcc878"],
    "brasa": ["#8a3a0a", "#d86a10", "#f89a1c", "#ffc040", "#ffe070", "#fff2b0"],
    "luz_morada": ["#3b1f5c", "#6a3aa8", "#9a5ae0", "#b88cf8", "#d8b8ff", "#f0e0ff"],
    "piedra": ["#22222c", "#3c3c4a", "#5a5a6c", "#7c7c90", "#9a9ab0", "#b8b8cc"],
    "piedra_oscura": ["#14141c", "#22222c", "#32323e", "#44445a", "#585872", "#6c6c88"],
    "tela_arana": ["#8c88a0", "#bcb8d0", "#dcd8ec", "#eeeaf8", "#ffffff", "#ffffff"],
    "negro_h": ["#050508", "#0b0b12", "#14141c", "#1c1c28", "#26263a", "#30304a"],
    "murcielago_h": ["#0b0b12", "#1a1a24", "#2b2b38", "#3c3c4c", "#4c4c60", "#5c5c78"],
    "brebaje": ["#1a5a20", "#38b43c", "#6adc4a", "#a0f060", "#d0ff90", "#f0ffc0"],
    "fantasma_h": ["#7d879c", "#c9d0de", "#e9edf4", "#ffffff", "#ffffff", "#ffffff"],
    "corteza": ["#1a100c", "#2e1e16", "#44301f", "#5a4028", "#70523a", "#86684a"],
    "hueso": ["#6a5a40", "#b8a47a", "#dcc8a0", "#efe0bc", "#f8eed0", "#fff8e0"],
}

# Diez tonos por material. Cada mueble los reparte según su propia luz, como haría quien
# lo pinta a mano: siempre tiene su lado en sombra, su cara media y su brillo. El fondo,
# en cambio, queda casi todo en el tono medio y solo cambia con sombras y luces fuertes.
TONOS = 10
CORTES_MUEBLE = list(np.linspace(0.06, 0.96, TONOS - 1))
# Proporciones de la luz mediana del fondo que separan sus tonos.
CORTES_FONDO = [0.55, 0.64, 0.73, 0.82, 0.93, 1.08, 1.2, 1.34, 1.5]
BRILLO_BORDE = 2
# Materiales de tela y de madera: llevan una textura sutil para que no parezcan de plástico.
TELAS = {"sillon", "puf", "cojin", "coral", "crema", "cortina", "alfombra", "salvia"}
MADERAS = {"madera", "boiserie"}
# Luz cálida de hogar: las sombras se tiñen de vino y las luces de miel.
SOMBRA_CALIDA = (74, 30, 26)
LUZ_CALIDA = (255, 214, 150)
MEZCLA_CALIDA = 0.12
SOMBRA_SUELO = (52, 22, 14)

CAPA_FONDO, CAPA_DETALLE, CAPA_MUEBLE, CAPA_PEQUENO = 0, 1, 2, 3


class Pieza:
    def __init__(self, identificador, rampa, capa, grupo, emisivo, en_suelo, objeto):
        self.identificador = identificador
        self.objeto = objeto
        self.rampa = rampa
        self.capa = capa
        self.grupo = grupo
        self.emisivo = emisivo
        self.en_suelo = en_suelo


PIEZAS: list[Pieza] = []
OBJETOS_BLENDER: list = []
# Mueble al que pertenecen las piezas que se van creando: entre piezas del mismo
# mueble la línea es un tono oscuro, no el contorno negro de la silueta.
OBJETO_ACTUAL = [""]


def a_lineal(valor: float) -> float:
    return valor / 12.92 if valor <= 0.04045 else ((valor + 0.055) / 1.055) ** 2.4


def registrar(objeto, rampa, capa, grupo="", emisivo=False, en_suelo=False, bisel=0.0, suave=False, inflar=False, organico=0.0):
    """Fija la escala, redondea los bordes y le da a la pieza un color que la identifica."""
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    if bisel:
        modificador = objeto.modifiers.new("bisel", "BEVEL")
        modificador.width = bisel
        modificador.segments = 3
        modificador.limit_method = "ANGLE"
    if inflar:
        # Subdividir la caja ya biselada la vuelve mullida, como los cojines dibujados a mano.
        subdivision = objeto.modifiers.new("inflar", "SUBSURF")
        subdivision.levels = subdivision.render_levels = 2
    if organico:
        # Un poco de ruido en la superficie: nada hecho a mano es perfecto.
        textura = bpy.data.textures.new(f"ruido{len(PIEZAS)}", type="CLOUDS")
        textura.noise_scale = 9
        deformacion = objeto.modifiers.new("organico", "DISPLACE")
        deformacion.texture = textura
        deformacion.strength = organico
        deformacion.mid_level = 0.5
    if suave or bisel or inflar or organico:
        bpy.ops.object.shade_smooth()
    identificador = len(PIEZAS) + 1
    objeto.color = (a_lineal((identificador % 256) / 255), a_lineal((identificador // 256) / 255), 0, 1)
    PIEZAS.append(Pieza(identificador, rampa, capa, grupo, emisivo, en_suelo, OBJETO_ACTUAL[0]))
    OBJETOS_BLENDER.append(objeto)
    return objeto


def caja(centro, medidas, rampa, capa=CAPA_MUEBLE, giro=(0, 0, 0), **opciones):
    bpy.ops.mesh.primitive_cube_add(size=1, location=centro)
    bpy.context.object.scale = medidas
    bpy.context.object.rotation_euler = [radians(angulo) for angulo in giro]
    return registrar(bpy.context.object, rampa, capa, **opciones)


def cilindro(centro, radio, alto, rampa, capa=CAPA_MUEBLE, giro=(0, 0, 0), suave=True, **opciones):
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=radio, depth=alto, location=centro)
    bpy.context.object.rotation_euler = [radians(angulo) for angulo in giro]
    return registrar(bpy.context.object, rampa, capa, suave=suave, **opciones)


def cilindro_de_corte(centro, radio, grosor):
    """Cilindro invisible con el eje hacia la cámara, para recortar arcos."""
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=radio, depth=grosor, location=centro)
    cilindro_objeto = bpy.context.object
    cilindro_objeto.rotation_euler = (radians(90), 0, 0)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    cilindro_objeto.hide_render = True
    return cilindro_objeto


def tabla_en_arco(x, ancho, alto_recto, arco, y, grosor, corte, rampa, capa, **opciones):
    """Tabla vertical cuyo extremo superior sigue el arco de la puerta, en una sola pieza."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, alto_recto / 2))
    abajo = bpy.context.object
    abajo.scale = (ancho, grosor, alto_recto)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, alto_recto + arco / 2))
    arriba = bpy.context.object
    arriba.scale = (ancho, grosor, arco)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    modificador = arriba.modifiers.new("arco", "BOOLEAN")
    modificador.operation = "INTERSECT"
    modificador.object = corte
    modificador.solver = "EXACT"
    bpy.context.view_layer.objects.active = arriba
    bpy.ops.object.modifier_apply(modifier="arco")
    bpy.ops.object.select_all(action="DESELECT")
    abajo.select_set(True)
    arriba.select_set(True)
    bpy.context.view_layer.objects.active = abajo
    bpy.ops.object.join()
    return registrar(abajo, rampa, capa, **opciones)

def cono(centro, radio_abajo, radio_arriba, alto, rampa, capa=CAPA_MUEBLE, **opciones):
    bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=radio_abajo, radius2=radio_arriba, depth=alto, location=centro)
    return registrar(bpy.context.object, rampa, capa, suave=True, **opciones)


def esfera(centro, radios, rampa, capa=CAPA_PEQUENO, giro=(0, 0, 0), **opciones):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=1, location=centro)
    objeto = bpy.context.object
    objeto.scale = radios
    objeto.rotation_euler = [radians(angulo) for angulo in giro]
    return registrar(objeto, rampa, capa, suave=True, **opciones)


def piso_y(y_pantalla: float) -> float:
    """Profundidad en el piso de un punto que en la pantalla del juego está a y_pantalla."""
    return OBJETIVO_Y + (ALTO_JUEGO / 2 - y_pantalla) / SEN


def pared_z(y_pantalla: float) -> float:
    """Altura en la pared de un punto que en la pantalla del juego está a y_pantalla."""
    return (ALTO_PARED_JUEGO - y_pantalla) / COS


def construir_pared():
    caja((0, 3, ALTO_PARED / 2), (ANCHO_SALA, 6, ALTO_PARED), "pared", CAPA_FONDO, grupo="fondo")
    x = -ANCHO_SALA / 2
    while x < ANCHO_SALA / 2:
        alto_raya = ALTO_PARED - ALTO_BOISERIE
        caja((x + 4, -0.3, ALTO_BOISERIE + alto_raya / 2), (8, 0.6, alto_raya), "pared2", CAPA_FONDO, grupo="fondo")
        x += 28
    caja((0, -1.5, ALTO_BOISERIE / 2), (ANCHO_SALA, 3, ALTO_BOISERIE), "boiserie", CAPA_DETALLE)
    x = -ANCHO_SALA / 2 + 10
    while x < ANCHO_SALA / 2:
        caja((x + 34, -3.6, 32), (62, 2, 36), "boiserie", CAPA_MUEBLE)
        x += 78
    caja((0, -4, ALTO_BOISERIE + 2), (ANCHO_SALA, 6, 5), "moldura", CAPA_MUEBLE)
    caja((0, -5, 5), (ANCHO_SALA, 6, 10), "zocalo", CAPA_MUEBLE)


def construir_piso(azar: random.Random):
    caja((0, -PROFUNDIDAD_PISO / 2, -2), (ANCHO_SALA, PROFUNDIDAD_PISO + 20, 4), "suelo_base", CAPA_FONDO, grupo="fondo", en_suelo=True)
    ancho_tablon = 26
    filas = int(PROFUNDIDAD_PISO // ancho_tablon) + 1
    for fila in range(filas):
        y = -ancho_tablon / 2 - fila * ancho_tablon - 8
        x = -ANCHO_SALA / 2 - azar.uniform(0, 120)
        while x < ANCHO_SALA / 2:
            largo = azar.choice((150, 190, 230, 270))
            caja((x + largo / 2, y, 0.75), (largo - 1.5, ancho_tablon - 1.5, 1.5), azar.choice(("suelo1", "suelo2", "suelo3")), CAPA_FONDO, grupo="tablon", en_suelo=True)
            for desvio in (-7, 7):
                caja((x + largo - 6, y + desvio, 1.6), (2.2, 2.2, 0.6), "clavo", CAPA_DETALLE, en_suelo=True)
            x += largo


def montana(centro, radio, alto, rampa, capa):
    """Cono aplastado contra la pared, para dibujar montañas en ventanas y cuadros."""
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=radio, radius2=0, depth=alto, location=centro)
    objeto = bpy.context.object
    objeto.rotation_euler = (0, 0, radians(45))
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    objeto.scale = (1, 0.04, 1)
    return registrar(objeto, rampa, capa)


def construir_ventana():
    OBJETO_ACTUAL[0] = "ventana"
    centro_x, centro_z = -230, (pared_z(22) + pared_z(116)) / 2
    caja((centro_x, -3, centro_z), (122, 6, 100), "boiserie", CAPA_DETALLE)
    caja((centro_x, -6.5, centro_z + 6), (104, 1, 70), "cielo", CAPA_DETALLE + 1)
    for desvio_x, desvio_z, radio in ((-34, 22, 9), (-24, 25, 11), (-14, 22, 8), (26, 30, 8), (35, 32, 10)):
        esfera((centro_x + desvio_x, -7, centro_z + desvio_z), (radio, 0.3, radio * 0.6), "nube", CAPA_DETALLE + 2)
    montana((centro_x - 18, -6.9, centro_z - 12), 34, 40, "montana", CAPA_DETALLE + 2)
    montana((centro_x + 22, -6.9, centro_z - 16), 30, 32, "montana", CAPA_DETALLE + 2)
    caja((centro_x, -7.3, centro_z - 32), (104, 1, 16), "colina", CAPA_DETALLE + 3)
    esfera((centro_x + 28, -7.6, centro_z - 22), (12, 0.4, 9), "colina", CAPA_DETALLE + 3)
    esfera((centro_x - 24, -7.6, centro_z - 26), (16, 0.4, 8), "colina", CAPA_DETALLE + 3)
    caja((centro_x, -8.5, centro_z), (6, 2, 82), "boiserie", CAPA_MUEBLE)
    caja((centro_x, -8.5, centro_z), (104, 2, 5), "boiserie", CAPA_MUEBLE)
    caja((centro_x, -9, centro_z - 52), (134, 16, 6), "moldura", CAPA_MUEBLE)
    cilindro((centro_x, -12, centro_z + 62), 2.4, 164, "dorado", CAPA_MUEBLE, giro=(0, 90, 0))
    for lado in (-1, 1):
        for pliegue in range(2):
            x = centro_x + lado * (62 + pliegue * 7)
            cilindro((x, -13 - pliegue, centro_z + 4), 4.6, 118, "cortina", CAPA_MUEBLE)
        esfera((centro_x + lado * 66, -17, centro_z - 8), (10, 6, 4), "dorado", CAPA_PEQUENO)


def construir_cuadro_y_reloj():
    OBJETO_ACTUAL[0] = "cuadro"
    x, z = 310 - 320, (pared_z(84) + pared_z(36)) / 2
    caja((x, -2, z), (58, 4, 58), "boiserie", CAPA_DETALLE)
    caja((x, -4.4, z), (46, 1, 46), "cielo", CAPA_DETALLE + 1)
    montana((x - 6, -4.8, z - 4), 22, 26, "montana", CAPA_DETALLE + 2)
    montana((x + 10, -4.8, z - 8), 18, 20, "montana", CAPA_DETALLE + 2)
    caja((x, -5.2, z - 18), (46, 0.6, 10), "colina", CAPA_DETALLE + 3)
    OBJETO_ACTUAL[0] = "reloj"
    x, z = 180 - 320, pared_z(70)
    cilindro((x, -2, z), 16, 4, "madera", CAPA_DETALLE, giro=(90, 0, 0))
    cilindro((x, -4.3, z), 12.5, 1, "crema", CAPA_DETALLE + 1, giro=(90, 0, 0))
    caja((x, -5.2, z + 4), (1.8, 0.6, 9), "metal", CAPA_MUEBLE)
    caja((x + 3.5, -5.2, z), (8, 0.6, 1.8), "metal", CAPA_MUEBLE)


def construir_puertas():
    OBJETO_ACTUAL[0] = "puerta_trasera"
    x = 232 - 320
    for lado in (-1, 1):
        caja((x + lado * 41, -5, 76), (10, 10, 152), "puerta_verde", CAPA_DETALLE)
    caja((x, -5, 147), (92, 10, 10), "puerta_verde", CAPA_DETALLE)
    caja((x, -6, 71), (72, 4, 142), "madera", CAPA_MUEBLE)
    caja((x, -8.5, 112), (34, 1, 30), "cielo", CAPA_MUEBLE + 1)
    caja((x, -10, 112), (4, 2, 30), "madera", CAPA_MUEBLE + 2)
    caja((x, -10, 112), (34, 2, 4), "madera", CAPA_MUEBLE + 2)
    for altura in (24, 54):
        caja((x, -10, altura), (56, 4, 22), "madera", CAPA_MUEBLE + 1)
    esfera((x + 27, -12, 70), (3.5, 3, 3.5), "dorado")

    OBJETO_ACTUAL[0] = "puerta"
    x = 582 - 320
    caja((x, -3, 64), (94, 6, 128), "boiserie", CAPA_DETALLE)
    cilindro((x, -3, 128), 47, 6, "boiserie", CAPA_DETALLE, giro=(90, 0, 0), suave=False)
    corte = cilindro_de_corte((x, -7.5, 124), 40, 12)
    for indice in range(4):
        tabla_en_arco(x - 30 + indice * 20, 20, 124, 42, -7.5, 3, corte, "madera", CAPA_MUEBLE, grupo="tabla")
    for altura in (34, 96):
        caja((x, -9.6, altura), (80, 1.2, 5), "metal", CAPA_MUEBLE + 1)
    esfera((x + 28, -11, 66), (4, 3.5, 4), "dorado")


def construir_repisa():
    OBJETO_ACTUAL[0] = "repisa"
    x, z = 385 - 320, pared_z(100)
    caja((x, -8, z), (80, 16, 4), "madera")
    for lado in (-30, 30):
        caja((x + lado, -3, z - 6), (4, 6, 10), "madera")
    cono((x - 22, -8, z + 8), 5, 7, 12, "maceta", CAPA_PEQUENO)
    for giro in range(5):
        angulo = giro * 2 * pi / 5
        esfera((x - 22 + cos(angulo) * 4, -8 + sin(angulo) * 2, z + 20), (3.5, 2.5, 7), "planta", giro=(cos(angulo) * 25, sin(angulo) * 25, 0))
    caja((x + 4, -6, z + 10), (14, 2, 16), "dorado", CAPA_PEQUENO)
    caja((x + 4, -7.2, z + 10), (10, 0.6, 12), "colina", CAPA_PEQUENO + 1)
    cilindro((x + 26, -8, z + 9), 3, 14, "crema", CAPA_PEQUENO)
    esfera((x + 26, -8, z + 19), (1.6, 1.6, 2.6), "pantalla", CAPA_PEQUENO + 1, emisivo=True)


def construir_alfombra():
    OBJETO_ACTUAL[0] = "alfombra"
    centro = (360 - 320, piso_y(259))
    for radio, rampa, alto in ((72, "coral", 0.8), (67, "crema", 1.2), (60, "alfombra", 1.6), (40, "crema", 2.0), (36, "alfombra", 2.4), (14, "coral", 2.8)):
        cilindro((*centro, alto / 2 + 0.2), radio, alto, rampa, CAPA_DETALLE if rampa == "coral" and radio == 72 else CAPA_DETALLE + 1, en_suelo=True)
    for indice in range(12):
        angulo = indice * 2 * pi / 12
        caja((centro[0] + cos(angulo) * 50, centro[1] + sin(angulo) * 50, 2.3), (8, 8, 0.6), "salvia", CAPA_DETALLE + 2, giro=(0, 0, 45), en_suelo=True)
    for indice in range(26):
        angulo = pi + indice * pi / 25
        caja((centro[0] + cos(angulo) * 76, centro[1] + sin(angulo) * 76, 0.4), (2, 6, 0.6), "crema", CAPA_DETALLE + 2, giro=(0, 0, angulo * 180 / pi - 90), en_suelo=True)


def construir_cama():
    """Cama de madera a lo largo, con la cabecera a la izquierda para que Nailong duerma estirado."""
    OBJETO_ACTUAL[0] = "cama"
    frente = piso_y(236)
    x, y = 100 - 320, frente + 44
    largo, fondo = 164, 84
    for lado_x in (-1, 1):
        for lado_y in (-1, 1):
            cono((x + lado_x * (largo / 2 - 8), y + lado_y * (fondo / 2 - 7), 3), 3, 3.5, 6, "madera", CAPA_PEQUENO)
    caja((x, y, 12), (largo - 6, fondo, 12), "madera", bisel=3)
    # Cabecera alta y piecera baja, con el canto de arriba redondeado.
    for lado, alto in ((-1, 58), (1, 30)):
        borde = x + lado * (largo / 2 - 3)
        caja((borde, y, alto / 2 + 4), (10, fondo, alto), "madera", bisel=3)
        esfera((borde, y, alto + 4), (5.5, fondo / 2, 9), "madera", CAPA_MUEBLE)
        for lado_y in (-1, 1):
            cilindro((borde, y + lado_y * fondo / 2, alto / 2 + 4), 5, alto + 4, "madera", CAPA_MUEBLE, bisel=1.5)
            esfera((borde, y + lado_y * fondo / 2, alto + 9), (6, 6, 5.5), "madera", CAPA_PEQUENO)
    caja((x, y, 23), (largo - 14, fondo - 6, 12), "crema", bisel=5, inflar=True, organico=0.8)
    caja((x - 50, y + 4, 32), (26, 58, 9), "nube", CAPA_MUEBLE, bisel=4, inflar=True, organico=0.8)
    # Edredón tendido sobre la mitad de los pies, con el doblez de la sábana.
    caja((x + 16, y - 1, 30.5), (100, fondo - 2, 4), "coral", bisel=2, inflar=True, organico=1.2)
    caja((x - 30, y - 1, 31), (10, fondo - 1, 4.5), "nube", CAPA_PEQUENO, bisel=2, inflar=True)


def construir_puf():
    OBJETO_ACTUAL[0] = "puf"
    frente = piso_y(270)
    centro = (470 - 320, frente + 30)
    azar = random.Random(5)
    cilindro((*centro, 9), 27, 16, "puf", CAPA_MUEBLE, bisel=7, inflar=True, organico=1.2)
    gajos = 7
    for indice in range(gajos):
        angulo = indice * 2 * pi / gajos + azar.uniform(-0.08, 0.08)
        esfera(
            (centro[0] + cos(angulo) * 9, centro[1] + sin(angulo) * 8, 15 + azar.uniform(-1, 1)),
            (19 * azar.uniform(0.92, 1.08), 13, 12 * azar.uniform(0.9, 1.1)),
            "puf",
            CAPA_MUEBLE,
            giro=(azar.uniform(-5, 5), azar.uniform(-5, 5), angulo * 180 / pi),
            organico=1.2,
        )
    esfera((*centro, 25), (3.4, 3.4, 2.4), "cojin", CAPA_PEQUENO)


def construir_sillon():
    OBJETO_ACTUAL[0] = "sillon"
    frente = piso_y(305)
    x = 585 - 320
    for lado_x in (-36, 36):
        for lado_y in (8, 54):
            cono((x + lado_x, frente + lado_y, 4), 2.5, 4, 8, "madera", CAPA_PEQUENO)
    caja((x, frente + 31, 20), (92, 62, 26), "sillon", bisel=11, inflar=True, organico=1.5)
    esfera((x, frente + 58, 70), (46, 14, 38), "sillon", CAPA_MUEBLE, giro=(0, 3, 0), organico=2.2)
    caja((x, frente + 28, 40), (62, 52, 20), "sillon", bisel=9, inflar=True, organico=1.6)
    for lado in (-1, 1):
        esfera((x + lado * 38, frente + 33, 44 + lado), (14, 33, 27), "sillon", CAPA_MUEBLE, giro=(0, 0, lado * 4), organico=1.8)
    esfera((x - 12, frente + 46, 64), (17, 10, 16), "cojin", CAPA_PEQUENO, giro=(8, 0, 14), organico=1.4)


def construir_mesita():
    OBJETO_ACTUAL[0] = "mesita"
    frente = piso_y(190)
    centro = (330 - 320, frente + 18)
    cilindro((*centro, 2), 13, 4, "madera")
    cilindro((*centro, 20), 3, 34, "madera")
    cilindro((*centro, 38), 20, 6, "madera", bisel=2.5, inflar=True)
    cilindro((*centro, 46), 7, 12, "crema", CAPA_PEQUENO, bisel=2)
    cono((*centro, 62), 15, 9, 18, "pantalla", CAPA_PEQUENO, emisivo=True)


def construir_juguetero():
    """Baúl de juguetes en tres cuartos, abierto y lleno, como el dibujado a mano."""
    OBJETO_ACTUAL[0] = "juguetero"
    frente = piso_y(336)
    centro_x, centro_y = 200 - 320, frente + 26
    giro = 18
    coseno, seno = cos(radians(giro)), sin(radians(giro))

    def lugar(dx, dy, z):
        return (centro_x + dx * coseno - dy * seno, centro_y + dx * seno + dy * coseno, z)

    ancho, fondo, alto, grosor = 66, 44, 34, 4
    for indice, altura in enumerate((alto / 6, alto / 2, alto * 5 / 6)):
        caja(lugar(0, -fondo / 2 + grosor / 2, altura), (ancho, grosor, alto / 3), "madera", grupo="tabla", giro=(0, 0, giro))
    caja(lugar(0, fondo / 2 - grosor / 2, alto / 2), (ancho, grosor, alto), "madera", giro=(0, 0, giro))
    for lado in (-1, 1):
        caja(lugar(lado * (ancho / 2 - grosor / 2), 0, alto / 2), (grosor, fondo, alto), "madera", giro=(0, 0, giro))
        caja(lugar(lado * (ancho / 2 + 0.6), 0, alto * 0.62), (0.8, 14, 4), "boiserie", CAPA_PEQUENO, giro=(0, 0, giro))
        caja(lugar(lado * (ancho / 2 - 1), -fondo / 2 - 0.4, alto / 2), (5, 1, alto + 0.5), "dorado", CAPA_PEQUENO, giro=(0, 0, giro))
    caja(lugar(0, 0, 3), (ancho - grosor * 2, fondo - grosor * 2, 6), "madera", giro=(0, 0, giro))

    apertura = -108
    centro_tapa = (0, -fondo / 2, 2)
    tapa_y = centro_tapa[1] * cos(radians(apertura)) - centro_tapa[2] * sin(radians(apertura))
    tapa_z = centro_tapa[1] * sin(radians(apertura)) + centro_tapa[2] * cos(radians(apertura))
    caja(lugar(0, fondo / 2 + tapa_y, alto + tapa_z), (ancho + 2, fondo, 4), "madera", grupo="tabla", giro=(apertura, 0, giro), bisel=1.5)

    juguetes = (
        (-18, -4, 34, "coral", (10, 10, 10)),
        (14, -8, 32, "cojin", (8, 8, 8)),
        (24, 6, 33, "libro_verde", (7, 7, 7)),
        (-4, 8, 36, "libro_azul", (8, 8, 8)),
        (4, -12, 33, "dorado", (6, 6, 6)),
    )
    for dx, dy, z, rampa, radios in juguetes:
        esfera(lugar(dx, dy, z), radios, rampa, CAPA_PEQUENO)
    caja(lugar(-24, 8, 36), (9, 9, 9), "libro_rojo", CAPA_PEQUENO, giro=(12, 18, giro + 20), bisel=1)
    osito = (6, 4)
    esfera(lugar(*osito, 40), (9, 8, 9), "madera", CAPA_PEQUENO)
    esfera(lugar(*osito, 52), (8.5, 7.5, 7.5), "madera", CAPA_PEQUENO)
    for lado in (-1, 1):
        esfera(lugar(osito[0] + lado * 6.5, osito[1], 59), (3.2, 2.6, 3.2), "madera", CAPA_PEQUENO)
    esfera(lugar(osito[0], osito[1] - 6.5, 50), (3.4, 1.8, 2.4), "crema", CAPA_PEQUENO)


def construir_plato_y_pelota():
    # Nailong come en su mesita, con plato, vaso y cubiertos, como uno más de la casa.
    OBJETO_ACTUAL[0] = "plato"
    frente = piso_y(330)
    centro = (500 - 320, frente + 28)
    for lado_x in (-22, 22):
        for lado_y in (-15, 15):
            cilindro((centro[0] + lado_x, centro[1] + lado_y, 16), 2.8, 32, "madera")
    caja((*centro, 28), (52, 36, 6), "madera", bisel=2)
    cilindro((*centro, 35), 30, 4, "madera", bisel=2)
    caja((centro[0] - 3, centro[1] - 1, 37.4), (30, 20, 0.8), "coral", CAPA_PEQUENO)
    cilindro((centro[0] - 3, centro[1] - 1, 38.6), 10.5, 1.6, "crema", CAPA_PEQUENO, bisel=0.7)
    cilindro((centro[0] - 3, centro[1] - 1, 39.6), 7.5, 1.2, "comida", CAPA_PEQUENO + 1, bisel=0.5)
    for desvio_x, desvio_y in ((-6, 1), (-1, -3), (0, 3)):
        esfera((centro[0] + desvio_x, centro[1] + desvio_y, 41), (2.8, 2.8, 2.2), "coral", CAPA_PEQUENO + 2)
    esfera((centro[0] - 3, centro[1] + 2, 42), (3.2, 2.8, 2), "planta", CAPA_PEQUENO + 2)
    caja((centro[0] - 18, centro[1] - 1, 37.8), (1.6, 14, 0.8), "metal", CAPA_PEQUENO + 1)
    caja((centro[0] + 12, centro[1] - 1, 37.8), (1.6, 14, 0.8), "metal", CAPA_PEQUENO + 1)
    cilindro((centro[0] + 18, centro[1] + 6, 42), 4, 10, "cielo", CAPA_PEQUENO, bisel=0.6)
    OBJETO_ACTUAL[0] = "pelota"
    frente = piso_y(344)
    centro = (300 - 320, frente + 11)
    esfera((*centro, 11), (11, 11, 11), "colina", CAPA_MUEBLE)
    bpy.ops.mesh.primitive_torus_add(major_radius=11.2, minor_radius=1.6, location=(*centro, 11))
    bpy.context.object.rotation_euler = (radians(70), 0, radians(30))
    registrar(bpy.context.object, "crema", CAPA_PEQUENO, suave=True)


def construir_estanteria(azar: random.Random):
    OBJETO_ACTUAL[0] = "estanteria"
    x = 480 - 320
    centro_y = -17.5
    caja((x, centro_y + 15, 44), (88, 3, 88), "madera")
    for lado in (-1, 1):
        caja((x + lado * 42, centro_y, 44), (6, 34, 88), "madera")
    caja((x, centro_y, 89), (94, 36, 4), "madera", bisel=2)
    colores = ("libro_rojo", "libro_azul", "libro_verde", "libro_crema")
    for indice, altura in enumerate((1.5, 30, 58)):
        caja((x, centro_y + 1, altura), (80, 31, 3), "madera")
        cursor = x - 37
        limite = x + 34
        while cursor < limite:
            if azar.random() < 0.18 and limite - cursor > 20:
                for capa_pila in range(azar.choice((2, 3))):
                    alto_pila = altura + 1.5 + capa_pila * 5 + 2.5
                    caja((cursor + 10, centro_y + 4, alto_pila), (19 - capa_pila * 2, 20, 4.6), azar.choice(colores), CAPA_PEQUENO)
                cursor += 22
                continue
            ancho_libro = azar.choice((5, 6, 7, 8))
            alto_libro = azar.choice((17, 20, 23, 25))
            inclinacion = azar.choice((0, 0, 0, 12)) if limite - cursor < 12 else 0
            caja((cursor + ancho_libro / 2, centro_y + 4, altura + 1.5 + alto_libro / 2), (ancho_libro - 0.8, 20, alto_libro), azar.choice(colores), CAPA_PEQUENO, giro=(0, inclinacion, 0))
            cursor += ancho_libro
    cono((x - 22, centro_y, 97), 6, 8, 12, "maceta", CAPA_PEQUENO)
    for giro in range(6):
        angulo = giro * 2 * pi / 6
        esfera((x - 22 + cos(angulo) * 5, centro_y + sin(angulo) * 3, 109), (4, 3, 9), "planta", giro=(cos(angulo) * 30, sin(angulo) * 30, 0))
    cilindro((x + 20, centro_y, 97), 6, 10, "crema", CAPA_PEQUENO)


def construir_planta():
    OBJETO_ACTUAL[0] = "planta"
    frente = piso_y(340)
    centro = (44 - 320, frente + 16)
    cono((*centro, 12), 12, 16, 24, "maceta", bisel=2)
    for giro in range(13):
        angulo = giro * 2 * pi / 13 + (giro % 2) * 0.3
        alto = 34 + (giro % 4) * 7
        esfera(
            (centro[0] + cos(angulo) * 11, centro[1] + sin(angulo) * 9, alto),
            (6, 3.5, 17),
            "planta" if giro % 3 else "colina",
            CAPA_MUEBLE,
            giro=(sin(angulo) * 42, -cos(angulo) * 42, 0),
        )


def linea(a, b, rampa, grosor=1.4, y=-6.5, capa=CAPA_PEQUENO):
    """Un trazo recto en el plano de la pared, de un punto (x, z) a otro."""
    (x1, z1), (x2, z2) = a, b
    largo = ((x2 - x1) ** 2 + (z2 - z1) ** 2) ** 0.5
    angulo = -np.degrees(np.arctan2(z2 - z1, x2 - x1))
    return caja(((x1 + x2) / 2, y, (z1 + z2) / 2), (largo, 1.2, grosor), rampa, capa, giro=(0, angulo, 0))


def construir_calabaza(nombre, radio, centro_x, base_y, caras=True):
    """Calabaza gorda de gajos, con ojos y boca tallados que brillan, vista de tres cuartos."""
    OBJETO_ACTUAL[0] = nombre
    centro = (centro_x - 320, piso_y(base_y) + radio)
    alto = radio * 0.82
    for desvio, factor in ((0, 1.0), (-0.5, 0.82), (0.5, 0.82), (-0.28, 0.9), (0.28, 0.9)):
        esfera((centro[0] + desvio * radio, centro[1] + (0.18 * radio if desvio else 0), alto), (radio * 0.62 * (1.08 if desvio == 0 else 1), radio * 0.82 * factor, alto * factor), "calabaza_h", CAPA_MUEBLE)
    cilindro((centro[0] + radio * 0.05, centro[1], alto * 2 - 1), radio * 0.12, radio * 0.34, "planta", CAPA_PEQUENO, giro=(0, 8, 0))
    if not caras:
        return
    def superficie_en(z):
        """Profundidad del frente de la calabaza a esa altura, para pegar la cara sobre la cáscara."""
        relativo = min(abs(z - alto) / alto, 0.95)
        return centro[1] - radio * 0.82 * (1 - relativo ** 2) ** 0.5 - 0.3

    for lado in (-1, 1):
        z_ojo = alto * 1.5
        caja((centro[0] + lado * radio * 0.36, superficie_en(z_ojo), z_ojo), (radio * 0.32, 1.4, radio * 0.28), "brasa", CAPA_PEQUENO, giro=(0, 0, 0), emisivo=True)
    for indice in range(5):
        z_boca = alto * (1.0 - (0.12 if indice % 2 else 0))
        caja((centro[0] + (indice - 2) * radio * 0.24, superficie_en(z_boca), z_boca), (radio * 0.2, 1.4, radio * 0.18), "brasa", CAPA_PEQUENO, emisivo=True)


def construir_lapida(nombre, centro_x, base_y, cruz=False):
    OBJETO_ACTUAL[0] = nombre
    centro = (centro_x - 320, piso_y(base_y) + 6)
    esfera((centro[0], centro[1] + 1, 1.5), (17, 11, 3), "colina", CAPA_MUEBLE)
    if cruz:
        caja((centro[0], centro[1], 24), (8, 5, 46), "piedra", CAPA_MUEBLE, bisel=0.8)
        caja((centro[0], centro[1], 33), (26, 5, 8), "piedra", CAPA_MUEBLE, bisel=0.8)
        return
    caja((centro[0], centro[1], 17), (22, 5.5, 34), "piedra", CAPA_MUEBLE, bisel=0.8)
    cilindro((centro[0], centro[1], 34), 11, 5.5, "piedra", CAPA_MUEBLE, giro=(90, 0, 0), suave=False)
    caja((centro[0], centro[1] - 2.9, 30), (3, 1, 14), "piedra_oscura", CAPA_PEQUENO)
    caja((centro[0], centro[1] - 2.9, 33), (11, 1, 3), "piedra_oscura", CAPA_PEQUENO)


def construir_murcielago():
    OBJETO_ACTUAL[0] = "bat"
    x, z, y = 0, 60, -6
    esfera((x, y, z), (3.4, 2.4, 5), "murcielago_h", CAPA_PEQUENO)
    esfera((x, y - 0.5, z + 6.5), (3.2, 2.4, 3), "murcielago_h", CAPA_PEQUENO)
    for lado in (-1, 1):
        cono((x + lado * 2.2, y, z + 10), 1.6, 0.1, 4, "murcielago_h", CAPA_PEQUENO)
        esfera((x + lado * 1.3, y - 2.4, z + 6.8), (0.7, 0.4, 0.7), "brasa", CAPA_PEQUENO + 1, emisivo=True)
        for desvio_x, desvio_z, radios in ((7, 3, (7, 0.8, 5)), (14, 0, (6.5, 0.8, 4)), (20, -3.5, (5.5, 0.8, 3.2))):
            esfera((x + lado * desvio_x, y + 0.5, z + desvio_z), radios, "murcielago_h", CAPA_PEQUENO, giro=(0, lado * -14, 0))


def construir_telarana():
    OBJETO_ACTUAL[0] = "web"
    x0, z0 = -316, ALTO_PARED - 1
    largo = 78
    angulos = [radians(grados) for grados in (4, 22, 40, 58, 76, 90)]
    radios = (20, 38, 58, 78)
    for angulo in angulos:
        linea((x0, z0), (x0 + largo * cos(angulo), z0 - largo * sin(angulo)), "tela_arana", 1.5)
    for radio in radios[:-1]:
        puntos = [(x0 + radio * cos(angulo), z0 - radio * sin(angulo) * (1 - 0.08 * radio / 58)) for angulo in angulos]
        for a, b in zip(puntos, puntos[1:]):
            linea(a, b, "tela_arana", 1.3)
    caja((x0 + 14, -6, z0 - 40), (1, 1, 1), "tela_arana", CAPA_PEQUENO)
    esfera((x0 + 52, -6.5, z0 - 56), (3, 2, 3), "murcielago_h", CAPA_PEQUENO)
    for patas in range(3):
        linea((x0 + 52, z0 - 56), (x0 + 52 + (patas - 1) * 7, z0 - 49), "murcielago_h", 0.8, -6.8)


def construir_luces():
    OBJETO_ACTUAL[0] = "lights"
    inicio, fin = 190 - 320, 560 - 320
    mitad, centro = (fin - inicio) / 2, (inicio + fin) / 2
    z_arriba, caida = pared_z(10), 20
    puntos = []
    for indice in range(13):
        x = inicio + (fin - inicio) * indice / 12
        puntos.append((x, z_arriba - caida * (1 - ((x - centro) / mitad) ** 2)))
    for a, b in zip(puntos, puntos[1:]):
        linea(a, b, "metal", 0.9, -6.5, CAPA_DETALLE)
    for indice, (x, z) in enumerate(puntos[1:-1]):
        esfera((x, -6.5, z - 4), (3.6, 3.6, 4.4), "brasa" if indice % 2 else "luz_morada", CAPA_PEQUENO, emisivo=True)


def construir_caldero(nombre, centro_x, base_y):
    OBJETO_ACTUAL[0] = nombre
    centro = (centro_x - 320, piso_y(base_y) + 17)
    for lado_x in (-1, 1):
        for lado_y in (-1, 1):
            cono((centro[0] + lado_x * 9, centro[1] + lado_y * 8, 3), 2.4, 1.6, 6, "metal", CAPA_MUEBLE)
    esfera((centro[0], centro[1], 14), (16, 15.5, 8.4), "metal", CAPA_MUEBLE)
    bpy.ops.mesh.primitive_torus_add(major_radius=14, minor_radius=2.4, location=(centro[0], centro[1], 22))
    registrar(bpy.context.object, "metal", CAPA_MUEBLE, suave=True)
    cilindro((centro[0], centro[1], 22.4), 13.2, 1.4, "brebaje", CAPA_PEQUENO, emisivo=True)
    for desvio_x, desvio_y, radio in ((-5, 2, 2.6), (4, -3, 2), (6, 4, 1.6), (-2, -5, 1.4)):
        esfera((centro[0] + desvio_x, centro[1] + desvio_y, 24.4), (radio, radio, radio * 0.8), "brebaje", CAPA_PEQUENO + 1, emisivo=True)
    caja((centro[0] + 14.5, centro[1] - 2, 15), (1.6, 5, 7), "dorado", CAPA_PEQUENO)


def construir_fantasma(nombre="ghost"):
    OBJETO_ACTUAL[0] = nombre
    cono((0, 0, 14), 13, 9.5, 24, "fantasma_h", CAPA_MUEBLE)
    esfera((0, 0, 29), (10.5, 9.5, 11), "fantasma_h", CAPA_MUEBLE)
    for indice in range(6):
        angulo = indice * pi / 3
        esfera((cos(angulo) * 11.2, sin(angulo) * 10.2, 3.5 + 1.8 * (indice % 2)), (3.8, 3.8, 3.2), "fantasma_h", CAPA_MUEBLE)
    for lado in (-1, 1):
        esfera((lado * 13, -1, 20), (3.2, 3.4, 6.5), "fantasma_h", CAPA_MUEBLE, giro=(0, lado * 28, 0))
        esfera((lado * 4.2, -9.6, 31), (1.9, 1.1, 3.4), "negro_h", CAPA_PEQUENO)
    esfera((0, -9.4, 24.5), (2.3, 1.1, 3.2), "negro_h", CAPA_PEQUENO)


def construir_arana_colgante():
    OBJETO_ACTUAL[0] = "spider"
    x, z, y = 0, 60, -6
    esfera((x, y, z), (5.5, 4, 5), "murcielago_h", CAPA_PEQUENO)
    esfera((x, y - 0.5, z + 7), (3.4, 3, 3.2), "murcielago_h", CAPA_PEQUENO)
    for lado in (-1, 1):
        esfera((x + lado * 1.5, y - 3, z + 7.6), (0.9, 0.5, 0.9), "brasa", CAPA_PEQUENO + 1, emisivo=True)
        for patas in range(4):
            altura = z + 3 - patas * 2.4
            codo = (x + lado * (9 + patas * 0.6), altura + 6)
            punta = (x + lado * (15 + patas * 1.2), altura - 5)
            linea((x + lado * 3, altura), codo, "murcielago_h", 1.2, y)
            linea(codo, punta, "murcielago_h", 1.2, y)


def construir_velas(nombre, centro_x, base_y):
    OBJETO_ACTUAL[0] = nombre
    centro = (centro_x - 320, piso_y(base_y) + 7)
    for desvio_x, desvio_y, alto in ((-9, 2, 13), (0, -3, 19), (10, 3, 10)):
        cilindro((centro[0] + desvio_x, centro[1] + desvio_y, alto / 2), 3.6, alto, "hueso", CAPA_MUEBLE)
        esfera((centro[0] + desvio_x + 1.8, centro[1] + desvio_y - 2.6, alto - 3), (1.1, 1.1, 2.4), "hueso", CAPA_PEQUENO)
        esfera((centro[0] + desvio_x, centro[1] + desvio_y, alto + 3), (1.7, 1.7, 3.4), "brasa", CAPA_PEQUENO, emisivo=True)
    cilindro((centro[0], centro[1], 0.8), 15, 1.6, "metal", CAPA_MUEBLE)


def construir_cuervo(nombre, centro_x, base_y, k=1.9):
    OBJETO_ACTUAL[0] = nombre
    centro = (centro_x - 320, piso_y(base_y) + 4 * k)
    esfera((centro[0], centro[1], 9 * k), (6.5 * k, 9 * k, 6.5 * k), "murcielago_h", CAPA_MUEBLE, giro=(25, 0, 0))
    esfera((centro[0], centro[1] - 7 * k, 17 * k), (4.2 * k, 4 * k, 4.2 * k), "murcielago_h", CAPA_MUEBLE)
    caja((centro[0], centro[1] - 11.5 * k, 16.5 * k), (2.2 * k, 5 * k, 1.8 * k), "dorado", CAPA_PEQUENO)
    esfera((centro[0] + 2.2 * k, centro[1] - 9.5 * k, 18.4 * k), (0.9 * k, 0.5 * k, 0.9 * k), "brasa", CAPA_PEQUENO + 1, emisivo=True)
    caja((centro[0], centro[1] + 9 * k, 7.5 * k), (4 * k, 8 * k, 1.6 * k), "murcielago_h", CAPA_MUEBLE, giro=(-20, 0, 0))
    for lado in (-1, 1):
        esfera((centro[0] + lado * 6.2 * k, centro[1] + 0.5 * k, 9.5 * k), (1.8 * k, 7 * k, 5.4 * k), "negro_h", CAPA_MUEBLE, giro=(20, 0, lado * 10))
        caja((centro[0] + lado * 2 * k, centro[1], 2.2 * k), (0.9 * k, 0.9 * k, 4.4 * k), "dorado", CAPA_PEQUENO)


def construir_calavera(nombre, centro_x, base_y, k=1.6):
    OBJETO_ACTUAL[0] = nombre
    centro = (centro_x - 320, piso_y(base_y) + 8 * k)
    for giro in (35, -35):
        cilindro((centro[0], centro[1] + 3 * k, 1.6 * k), 1.5 * k, 24 * k, "hueso", CAPA_MUEBLE, giro=(0, 90, giro))
    esfera((centro[0], centro[1] - k, 8.5 * k), (7.2 * k, 6.5 * k, 6.4 * k), "hueso", CAPA_MUEBLE)
    caja((centro[0], centro[1] - 3.5 * k, 3.6 * k), (5.2 * k, 4 * k, 3.2 * k), "hueso", CAPA_MUEBLE)
    for lado in (-1, 1):
        esfera((centro[0] + lado * 2.8 * k, centro[1] - 6.2 * k, 9.4 * k), (1.9 * k, 0.9 * k, 2.1 * k), "negro_h", CAPA_PEQUENO)
    esfera((centro[0], centro[1] - 6.6 * k, 6.6 * k), (0.8 * k, 0.6 * k, 1.2 * k), "negro_h", CAPA_PEQUENO)


def construir_arbol_seco(nombre, centro_x, base_y):
    OBJETO_ACTUAL[0] = nombre
    centro = (centro_x - 320, piso_y(base_y) + 8)
    cono((centro[0], centro[1], 38), 11, 5, 76, "corteza", CAPA_MUEBLE, organico=1.2)
    esfera((centro[0], centro[1], 2), (15, 12, 4), "corteza", CAPA_MUEBLE)
    ramas = (
        ((0, 55), (-24, 82), 4.2), ((-24, 82), (-40, 112), 2.8), ((-24, 82), (-14, 118), 2.4),
        ((0, 62), (26, 92), 4.0), ((26, 92), (46, 108), 2.6), ((26, 92), (30, 126), 2.4),
        ((0, 74), (4, 116), 3.0), ((-24, 82), (-52, 90), 2.0), ((26, 92), (52, 82), 2.0),
    )
    for (x1, z1), (x2, z2), grosor in ramas:
        linea((centro[0] + x1, z1), (centro[0] + x2, z2), "corteza", grosor, centro[1] - 2, CAPA_MUEBLE)


def construir_halloween():
    construir_luces()
    construir_telarana()
    construir_murcielago()
    construir_calabaza("pumpkin", 26, 420, 352)
    construir_calabaza("pumpkin_m", 20, 548, 346)
    construir_calabaza("pumpkin_s", 14, 575, 352, caras=False)
    construir_lapida("gravestone_a", 100, 352)
    construir_lapida("gravestone_b", 160, 352, cruz=True)
    construir_caldero("cauldron", 250, 330)
    construir_fantasma()
    construir_arana_colgante()
    construir_velas("candles", 455, 340)
    construir_cuervo("crow", 200, 96)
    construir_calavera("skull", 350, 330)
    construir_arbol_seco("deadtree", 320, 230)


def construir_sala(semilla: int = 7, halloween: bool = False):
    azar = random.Random(semilla)
    construir_pared()
    construir_piso(azar)
    construir_ventana()
    construir_cuadro_y_reloj()
    construir_puertas()
    construir_repisa()
    construir_alfombra()
    construir_cama()
    construir_puf()
    construir_sillon()
    construir_mesita()
    construir_juguetero()
    construir_plato_y_pelota()
    construir_estanteria(azar)
    construir_planta()
    if halloween:
        construir_halloween()


def preparar_camara():
    escena = bpy.context.scene
    escena.render.engine = "BLENDER_WORKBENCH"
    escena.render.resolution_x = ANCHO * SUBMUESTREO
    escena.render.resolution_y = ALTO * SUBMUESTREO
    escena.render.film_transparent = False
    escena.display.render_aa = "OFF"
    escena.view_settings.view_transform = "Standard"
    escena.display.shading.show_object_outline = False
    escena.display.shading.show_cavity = False
    escena.display.shading.show_specular_highlight = True
    escena.display.light_direction = Vector(DIRECCION_LUZ).normalized()
    escena.display.shading.shadow_intensity = INTENSIDAD_SOMBRA
    # Sin este margen las caras planas se sombrean a sí mismas y salen moteadas.
    escena.display.shadow_shift = 0.2

    datos = bpy.data.cameras.new("camara")
    datos.type = "ORTHO"
    datos.ortho_scale = ANCHO_JUEGO
    datos.clip_end = DISTANCIA_CAMARA * 3
    camara = bpy.data.objects.new("camara", datos)
    escena.collection.objects.link(camara)
    escena.camera = camara

    direccion = Vector((0, -COS, SEN))
    objetivo = Vector((0, OBJETIVO_Y, 0))
    camara.location = objetivo + direccion * DISTANCIA_CAMARA
    camara.rotation_euler = (-direccion).to_track_quat("-Z", "Y").to_euler()
    return camara


def renderizar(ruta: Path, luz: str, color: str, sombras: bool) -> np.ndarray:
    escena = bpy.context.scene
    escena.display.shading.light = luz
    escena.display.shading.color_type = color
    escena.display.shading.single_color = (1, 1, 1)
    escena.display.shading.show_shadows = sombras
    escena.render.filepath = str(ruta)
    bpy.ops.render.render(write_still=True)
    return np.asarray(Image.open(ruta).convert("RGB"), dtype=np.float32) / 255


def bloques(matriz: np.ndarray) -> np.ndarray:
    """Agrupa la imagen supermuestreada en bloques de SUBMUESTREO x SUBMUESTREO."""
    alto, ancho = matriz.shape[:2]
    return matriz.reshape(alto // SUBMUESTREO, SUBMUESTREO, ancho // SUBMUESTREO, SUBMUESTREO, *matriz.shape[2:])


def moda(identificadores: np.ndarray) -> np.ndarray:
    pixeles = bloques(identificadores).transpose(0, 2, 1, 3).reshape(ALTO, ANCHO, -1)
    mejor = np.zeros((ALTO, ANCHO), dtype=np.int32)
    cuenta_mejor = np.zeros((ALTO, ANCHO), dtype=np.int32)
    for valor in np.unique(pixeles):
        cuenta = (pixeles == valor).sum(axis=-1)
        mas = cuenta > cuenta_mejor
        mejor[mas] = valor
        cuenta_mejor[mas] = cuenta[mas]
    return mejor


def dentro_de(poligono: list[tuple[float, float]]) -> np.ndarray:
    """Máscara de los píxeles de la imagen final que caen dentro de un polígono convexo."""
    filas, columnas = np.mgrid[0:ALTO, 0:ANCHO]
    mascara = np.ones((ALTO, ANCHO), dtype=bool)
    for (x1, y1), (x2, y2) in zip(poligono, poligono[1:] + poligono[:1]):
        mascara &= (x2 - x1) * (filas - y1) - (y2 - y1) * (columnas - x1) >= 0
    return mascara


def dentro_de_elipse(centro: tuple[float, float], radios: tuple[float, float]) -> np.ndarray:
    filas, columnas = np.mgrid[0:ALTO, 0:ANCHO]
    return ((columnas - centro[0]) / radios[0]) ** 2 + ((filas - centro[1]) / radios[1]) ** 2 <= 1


def rampa_de(nombre: str) -> np.ndarray:
    """Interpola la rampa de seis colores a contorno más diez tonos."""
    colores = np.array([a_rgb(color) for color in RAMPAS[nombre]], dtype=float)
    posiciones = np.linspace(0, len(colores) - 1, TONOS + 1)
    indices = np.floor(posiciones).astype(int).clip(0, len(colores) - 2)
    mezcla = (posiciones - indices)[:, None]
    return np.rint(colores[indices] * (1 - mezcla) + colores[indices + 1] * mezcla).astype(np.uint8)


def vetas(identificadores: np.ndarray) -> np.ndarray:
    """Trazos cortos y sueltos que imitan la veta de la madera del piso."""
    filas, columnas = np.mgrid[0:ALTO, 0:ANCHO]
    semilla = (columnas // 6 * 73856093) ^ (filas * 19349663) ^ (identificadores * 83492791)
    return (semilla % 61) == 0


def pintar(identificadores: np.ndarray, luz: np.ndarray, luces: bool = True, lampara: bool = True) -> Image.Image:
    por_id = {pieza.identificador: pieza for pieza in PIEZAS}
    tonos = np.zeros(identificadores.shape, dtype=np.int64)
    en_suelo = np.zeros(identificadores.shape, dtype=bool)
    capas = np.zeros(identificadores.shape, dtype=np.int32)
    grupos = np.zeros(identificadores.shape, dtype=object)
    objetos = np.zeros(identificadores.shape, dtype=object)
    claves = np.zeros(identificadores.shape, dtype=object)
    for identificador, pieza in por_id.items():
        mascara = identificadores == identificador
        en_suelo[mascara] = pieza.en_suelo
        capas[mascara] = pieza.capa
        grupos[mascara] = pieza.grupo
        objetos[mascara] = pieza.objeto or f"pieza{identificador}"
        clave = pieza.objeto or (pieza.grupo if pieza.capa == CAPA_FONDO else f"pieza{identificador}")
        claves[mascara] = ("fondo:" if pieza.capa == CAPA_FONDO else "mueble:") + clave
    for clave in set(claves[identificadores > 0].ravel()):
        if not isinstance(clave, str):
            continue
        mascara = claves == clave
        umbrales = np.quantile(luz[mascara], CORTES_MUEBLE)
        # Un objeto casi plano (una puerta, la pared) no tiene volumen que repartir: repartirlo
        # igual llenaría su cara de ruido, así que se trata como fondo.
        if clave.startswith("fondo:") or umbrales[-1] - umbrales[0] < 0.12:
            umbrales = np.median(luz[mascara]) * np.array(CORTES_FONDO)
        tonos[mascara] = np.digitize(luz[mascara], umbrales)
    for identificador, pieza in por_id.items():
        if pieza.emisivo:
            mascara = identificadores == identificador
            tonos[mascara] = np.maximum(tonos[mascara], 3) + 3

    escala = ANCHO / ANCHO_JUEGO
    rayo_de_sol = dentro_de([(84 * escala, 192 * escala), (196 * escala, 192 * escala), (284 * escala, 300 * escala), (172 * escala, 300 * escala)]) & luces
    resplandor = dentro_de_elipse((330 * escala, 198 * escala), (48 * escala, 14 * escala)) & luces & lampara
    tonos[en_suelo & (rayo_de_sol | resplandor)] += 2
    tonos[(grupos == "tablon") & vetas(identificadores) & ~rayo_de_sol] -= 1
    filas, columnas = np.mgrid[0:ALTO, 0:ANCHO]
    distancia = np.hypot((columnas - ANCHO / 2) / (ANCHO / 2), (filas - ALTO / 2) / (ALTO / 2))
    tonos[(capas == CAPA_FONDO) & (distancia > 1.18)] -= 2

    vacio = identificadores == 0
    mueble = capas >= CAPA_MUEBLE
    objeto_arriba = np.roll(objetos, 1, axis=0)
    tonos[mueble & ~vacio & (objeto_arriba != objetos)] += BRILLO_BORDE

    silueta = np.zeros(identificadores.shape, dtype=bool)
    pliegue = np.zeros(identificadores.shape, dtype=bool)
    apoyo = np.zeros(identificadores.shape, dtype=bool)
    for desplazamiento in ((0, 1), (1, 0), (0, -1), (-1, 0)):
        vecino_id = np.roll(identificadores, desplazamiento, axis=(0, 1))
        vecino_capa = np.roll(capas, desplazamiento, axis=(0, 1))
        vecino_grupo = np.roll(grupos, desplazamiento, axis=(0, 1))
        vecino_objeto = np.roll(objetos, desplazamiento, axis=(0, 1))
        distinto = (vecino_id != identificadores) & ~vacio
        encima = (capas > vecino_capa) | ((capas == vecino_capa) & (identificadores > vecino_id))
        otro_objeto = vecino_objeto != objetos
        silueta |= distinto & encima & otro_objeto & (capas >= CAPA_DETALLE)
        tablas = np.isin(grupos, ("tablon", "tabla")) & (vecino_grupo == grupos) & (desplazamiento[0] + desplazamiento[1] > 0)
        pliegue |= distinto & ((encima & ~otro_objeto & (capas >= CAPA_DETALLE)) | tablas)
        if desplazamiento == (-1, 0):
            apoyo |= distinto & encima & otro_objeto & mueble

    rampas = np.zeros(identificadores.shape, dtype=object)
    for identificador, pieza in por_id.items():
        rampas[identificadores == identificador] = pieza.rampa
    semilla = (columnas * 73856093) ^ (filas * 19349663)
    tonos[np.isin(rampas, list(TELAS)) & ((semilla % 11) == 0)] -= 1
    veta_madera = ((columnas * 2654435761) ^ (filas // 6 * 40503)) % 31 == 0
    tonos[np.isin(rampas, list(MADERAS)) & veta_madera] -= 1

    tonos = np.clip(tonos, 0, TONOS - 1)
    oscurecido = tonos.copy()
    oscurecido[pliegue] -= 2
    oscurecido[silueta] = tonos[silueta] - 4
    oscurecido[apoyo] = -1
    oscurecido = np.clip(oscurecido, -1, TONOS - 1)

    salida = np.zeros((ALTO, ANCHO, 4), dtype=np.uint8)
    salida[..., 3] = np.where(vacio, 0, 255)
    for identificador, pieza in por_id.items():
        mascara = identificadores == identificador
        salida[mascara, :3] = rampa_de(pieza.rampa)[oscurecido[mascara] + 1]
    return calentar(Image.fromarray(salida))


def calentar(imagen: Image.Image) -> Image.Image:
    """Tiñe toda la escena con la misma luz cálida para que muebles y sala se sientan juntos."""
    datos = np.asarray(imagen).astype(float)
    luminosidad = (datos[..., :3] @ np.array([0.3, 0.59, 0.11])) / 255
    tinte = np.where(luminosidad[..., None] < 0.45, SOMBRA_CALIDA, LUZ_CALIDA)
    datos[..., :3] = datos[..., :3] * (1 - MEZCLA_CALIDA) + tinte * MEZCLA_CALIDA
    return Image.fromarray(np.clip(datos, 0, 255).astype(np.uint8))


# Mueble del modelo -> tipo de objeto del juego y su posición (x, base) en la sala.
MUEBLES = {
    "alfombra": ("rug", 360, 300),
    "reloj": ("clock", 180, 86),
    "repisa": ("wallshelf", 385, 100),
    "estanteria": ("bookshelf", 480, 168),
    "mesita": ("sidetable", 330, 190),
    "puf": ("pouf", 470, 270),
    "sillon": ("armchair", 585, 305),
    "juguetero": ("toybox", 200, 336),
    "cuadro": ("frame", 310, 84),
    "planta": ("plant", 44, 340),
    "cama": ("bed", 100, 236),
    "plato": ("bowl", 500, 330),
    "pelota": ("ball", 300, 344),
    "puerta": ("door", 582, 156),
    "puerta_trasera": ("backdoor", 232, 156),
}


# Adornos de Halloween: pieza -> (archivo, x del ancla, base). Los de pared no tienen base
# fija: el recorte termina donde termina el dibujo y el juego los coloca a mano.
HALLOWEEN = {
    "pumpkin": ("pumpkin", 420, 352),
    "pumpkin_m": ("pumpkin_m", 548, 346),
    "pumpkin_s": ("pumpkin_s", 575, 352),
    "gravestone_a": ("gravestone_a", 100, 352),
    "gravestone_b": ("gravestone_b", 160, 352),
    "bat": ("bat", 320, 0),
    "web": ("web", 43, 0),
    "lights": ("lights", 375, 0),
    "cauldron": ("cauldron", 250, 330),
    "ghost": ("ghost", 320, 0),
    "spider": ("spider", 320, 0),
    "candles": ("candles", 455, 340),
    "crow": ("crow", 200, 96),
    "skull": ("skull", 350, 330),
    "deadtree": ("deadtree", 320, 230),
}
HALLOWEEN_EN_PARED = {"bat", "web", "lights"}


def renderizar_imagen(carpeta: Path, luces: bool, lampara: bool = True) -> Image.Image:
    ids = renderizar(carpeta / "ids.png", "FLAT", "OBJECT", sombras=False)
    luz = renderizar(carpeta / "luz.png", "STUDIO", "SINGLE", sombras=True)[..., 0]
    canales = np.rint(ids * 255).astype(np.int32)
    identificadores = canales[..., 0] + canales[..., 1] * 256
    luz_media = bloques(luz).mean(axis=(1, 3))
    suavizada = sum(np.roll(luz_media, (fila, columna), axis=(0, 1)) for fila in (-1, 0, 1) for columna in (-1, 0, 1)) / 9
    return pintar(moda(identificadores), suavizada, luces, lampara)


def recortar_en_ancla(imagen: Image.Image, ancla_x: float, base: float) -> Image.Image:
    """Recorta el mueble con su borde inferior central en el punto (x, base) del juego."""
    datos = np.array(imagen)
    opaco = datos[..., 3] > 0
    vecinos = sum(np.roll(opaco, (fila, columna), axis=(0, 1)) for fila in (-1, 0, 1) for columna in (-1, 0, 1)) - opaco
    datos[opaco & (vecinos == 0)] = 0
    imagen = Image.fromarray(datos)
    izquierda, arriba, derecha, abajo = imagen.getchannel("A").getbbox()
    escala = ANCHO / ANCHO_JUEGO
    centro, suelo = ancla_x * escala, base * escala
    mitad = int(np.ceil(max(centro - izquierda, derecha - centro)))
    fondo = max(abajo, int(round(suelo)))
    return imagen.crop((int(round(centro)) - mitad, arriba, int(round(centro)) + mitad, fondo))


EN_PARED = {"clock", "frame", "wallshelf", "door", "backdoor"}
SIN_SOMBRA = {"rug"}


def agregar_sombra(sprite: Image.Image, tipo: str) -> Image.Image:
    """Sombra suave de contacto bajo el mueble (o detrás, si cuelga de la pared).

    Sin ella las piezas sueltas flotan sobre el piso; con ella se asientan en la sala.
    La sombra queda por encima del borde inferior para no mover el punto de apoyo.
    """
    if tipo in SIN_SOMBRA:
        return sprite
    alfa = np.asarray(sprite.getchannel("A")) > 0
    if tipo in EN_PARED:
        desvio = 3
        lienzo = Image.new("RGBA", (sprite.width + desvio * 2, sprite.height + desvio), (0, 0, 0, 0))
        sombra = np.zeros((lienzo.height, lienzo.width), dtype=bool)
        sombra[desvio * 2 : desvio * 2 + alfa.shape[0] - desvio, desvio * 2 :] = alfa[: alfa.shape[0] - desvio, :]
        capa = np.zeros((lienzo.height, lienzo.width, 4), dtype=np.uint8)
        capa[sombra] = (*SOMBRA_SUELO, 70)
        lienzo.alpha_composite(Image.fromarray(capa))
        lienzo.alpha_composite(sprite, (desvio, 0))
        return lienzo
    filas = np.nonzero(alfa.any(axis=1))[0]
    base = alfa[max(filas[-1] - 8, 0) : filas[-1] + 1].any(axis=0)
    columnas = np.nonzero(base)[0]
    ancho = (columnas[-1] - columnas[0] + 1) * 1.2
    alto = max(8, ancho * 0.3)
    margen = int(np.ceil(max(0, ancho / 2 + 4 - sprite.width / 2)))
    lienzo = Image.new("RGBA", (sprite.width + margen * 2, sprite.height), (0, 0, 0, 0))
    filas_l, columnas_l = np.mgrid[0 : lienzo.height, 0 : lienzo.width]
    centro_x = lienzo.width / 2 + ancho * 0.06
    centro_y = lienzo.height - alto / 2
    distancia = ((columnas_l - centro_x) / (ancho / 2)) ** 2 + ((filas_l - centro_y) / (alto / 2)) ** 2
    capa = np.zeros((lienzo.height, lienzo.width, 4), dtype=np.uint8)
    capa[distancia <= 1] = (*SOMBRA_SUELO, 60)
    capa[distancia <= 0.45] = (*SOMBRA_SUELO, 110)
    lienzo.alpha_composite(Image.fromarray(capa))
    lienzo.alpha_composite(sprite, (margen, 0))
    return lienzo


def exportar_piezas(carpeta_piezas: Path, ruta_fondo: Path, temporal: Path, carpeta_halloween: Path | None = None):
    escena = bpy.context.scene
    muebles = [objeto for objeto, pieza in zip(OBJETOS_BLENDER, PIEZAS) if pieza.objeto in MUEBLES or pieza.objeto in HALLOWEEN]
    for objeto in muebles:
        objeto.hide_render = True
    renderizar_imagen(temporal, luces=True, lampara=False).save(ruta_fondo)
    print(f"fondo -> {ruta_fondo}")

    escena.render.film_transparent = True
    for objeto in OBJETOS_BLENDER:
        objeto.hide_render = True
    carpeta_piezas.mkdir(parents=True, exist_ok=True)
    for nombre, (tipo, ancla_x, base) in MUEBLES.items():
        propios = [objeto for objeto, pieza in zip(OBJETOS_BLENDER, PIEZAS) if pieza.objeto == nombre]
        for objeto in propios:
            objeto.hide_render = False
        sprite = agregar_sombra(recortar_en_ancla(renderizar_imagen(temporal, luces=False), ancla_x, base), tipo)
        sprite.save(carpeta_piezas / f"{tipo}.png")
        print(f"{tipo}: {sprite.size}")
        for objeto in propios:
            objeto.hide_render = True
    if carpeta_halloween:
        exportar_halloween(carpeta_halloween, temporal)


def exportar_halloween(carpeta: Path, temporal: Path):
    carpeta.mkdir(parents=True, exist_ok=True)
    for nombre, (archivo, ancla_x, base) in HALLOWEEN.items():
        propios = [objeto for objeto, pieza in zip(OBJETOS_BLENDER, PIEZAS) if pieza.objeto == nombre]
        for objeto in propios:
            objeto.hide_render = False
        recorte = recortar_en_ancla(renderizar_imagen(temporal, luces=False), ancla_x, base)
        sprite = agregar_sombra(recorte, "clock" if nombre in HALLOWEEN_EN_PARED else "pumpkin")
        sprite.save(carpeta / f"{archivo}.png")
        print(f"halloween/{archivo}: {sprite.size}")
        for objeto in propios:
            objeto.hide_render = True


def main() -> None:
    analizador = argparse.ArgumentParser(description=__doc__)
    analizador.add_argument("-o", "--salida", type=Path, required=True)
    analizador.add_argument("--piezas", type=Path, help="Carpeta donde guardar cada mueble como sprite")
    analizador.add_argument("--halloween", type=Path, help="Carpeta donde guardar los adornos de Halloween (con --piezas)")
    argumentos = analizador.parse_args()

    bpy.ops.wm.read_factory_settings(use_empty=True)
    PIEZAS.clear()
    OBJETOS_BLENDER.clear()
    construir_sala(halloween=bool(argumentos.halloween))
    preparar_camara()
    argumentos.salida.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as temporal:
        if argumentos.piezas:
            exportar_piezas(argumentos.piezas, argumentos.salida, Path(temporal), argumentos.halloween)
        else:
            imagen = renderizar_imagen(Path(temporal), luces=True)
            imagen.save(argumentos.salida)
            print(f"{imagen.size} -> {argumentos.salida} ({len(PIEZAS)} piezas)")


if __name__ == "__main__":
    main()
