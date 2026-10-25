"""Renderiza hojas de sprites en pixel art a partir del modelo 3D de Nailong.

Cada cuadro se renderiza tres veces a mayor resolución: una pasada dice qué
material ocupa cada píxel, otra cuánta luz recibe y otra a qué distancia de
la cámara está, para trazar contornos donde una parte tapa a otra. Luego se
reduce a la resolución final y se pinta con la paleta de los sprites hechos a mano, así
que el resultado usa exactamente los mismos colores que el resto del juego.

Uso:
    .venv/bin/python tools/modelo/render.py --animacion caminar --vista lado,frente \\
        --animo feliz,triste --prendas gorra -o public/sprites/modelo
"""

import argparse
import sys
import tempfile
from math import radians
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))

from nailong import MATERIALES, Modelo, color_identificador, construir, vestir  # noqa: E402
from paleta import DETALLES, OJO, RAMPAS, UMBRALES_LUZ, a_rgb  # noqa: E402
from poses import ANIMACIONES  # noqa: E402

LADO_CUADRO = 64
SUBMUESTREO = 4
ESCALA_ORTOGRAFICA = 2.2
CENTRO_CAMARA = 1.02
COBERTURA_DETALLE = 4
DISTANCIA_CAMARA = 10
# Diferencia de profundidad (en unidades) a partir de la cual una parte tapa a otra.
SALTO_PROFUNDIDAD = 0.12

VISTAS = {
    # nombre: dirección desde Nailong hacia la cámara
    "lado": (-1, -0.9, 0),
    "frente": (0, -1, 0),
    "espalda": (0, 1, 0),
}

# Giro extra de la cabeza en cada vista, en grados: de lado Nailong voltea la
# cara hacia el jugador y mira un poco hacia arriba, como en los sprites 2D.
GIRO_CABEZA = {"lado": (-8, -28, 0)}


def preparar_escena():
    escena = bpy.context.scene
    escena.render.engine = "BLENDER_WORKBENCH"
    escena.render.resolution_x = escena.render.resolution_y = LADO_CUADRO * SUBMUESTREO
    escena.render.film_transparent = True
    escena.display.render_aa = "OFF"
    escena.view_settings.view_transform = "Standard"
    escena.display.shading.single_color = (1, 1, 1)
    escena.cycles.samples = 1
    escena.cycles.filter_width = 0.01
    escena.cycles.use_denoising = False

    datos = bpy.data.cameras.new("camara")
    datos.type = "ORTHO"
    datos.ortho_scale = ESCALA_ORTOGRAFICA
    camara = bpy.data.objects.new("camara", datos)
    escena.collection.objects.link(camara)
    escena.camera = camara
    return camara, crear_material_profundidad()


def crear_material_profundidad() -> bpy.types.Material:
    """Material que emite la distancia a la cámara, mapeada entre 0 y 1."""
    material = bpy.data.materials.new("profundidad")
    material.use_nodes = True
    nodos, enlaces = material.node_tree.nodes, material.node_tree.links
    nodos.clear()
    camara = nodos.new("ShaderNodeCameraData")
    rango = nodos.new("ShaderNodeMapRange")
    rango.inputs["From Min"].default_value = DISTANCIA_CAMARA - ESCALA_ORTOGRAFICA
    rango.inputs["From Max"].default_value = DISTANCIA_CAMARA + ESCALA_ORTOGRAFICA
    emision = nodos.new("ShaderNodeEmission")
    salida = nodos.new("ShaderNodeOutputMaterial")
    enlaces.new(camara.outputs["View Z Depth"], rango.inputs["Value"])
    enlaces.new(rango.outputs["Result"], emision.inputs["Color"])
    enlaces.new(emision.outputs["Emission"], salida.inputs["Surface"])
    return material


def apuntar(camara, vista: str):
    direccion = Vector(VISTAS[vista])
    centro = Vector((0, 0, CENTRO_CAMARA))
    camara.location = centro + direccion * DISTANCIA_CAMARA
    camara.rotation_euler = (-direccion).to_track_quat("-Z", "Y").to_euler()


def posar(modelo: Modelo, pose: dict):
    for hueso in modelo.esqueleto.pose.bones:
        valores = pose.get(hueso.name, {})
        hueso.rotation_euler = [radians(angulo) for angulo in valores.get("rot", (0, 0, 0))]
        hueso.location = (0, valores.get("lift", 0), 0)
    bpy.context.view_layer.update()


def renderizar_pasada(ruta: Path, luz: str, color: str) -> np.ndarray:
    escena = bpy.context.scene
    escena.render.engine = "BLENDER_WORKBENCH"
    escena.display.shading.light = luz
    escena.display.shading.color_type = color
    escena.render.filepath = str(ruta)
    bpy.ops.render.render(write_still=True)
    return np.asarray(Image.open(ruta).convert("RGBA"), dtype=np.float32) / 255


def renderizar_profundidad(ruta: Path, material: bpy.types.Material) -> np.ndarray:
    """Devuelve la distancia a la cámara de cada píxel, en unidades de Blender."""
    escena = bpy.context.scene
    escena.render.engine = "CYCLES"
    capa = bpy.context.view_layer
    capa.material_override = material
    escena.render.filepath = str(ruta)
    bpy.ops.render.render(write_still=True)
    capa.material_override = None
    pasada = np.asarray(Image.open(ruta).convert("RGBA"), dtype=np.float32) / 255
    normalizada = np.vectorize(a_lineal)(pasada[..., 0])
    profundidad = DISTANCIA_CAMARA - ESCALA_ORTOGRAFICA + normalizada * 2 * ESCALA_ORTOGRAFICA
    return np.where(pasada[..., 3] > 0.5, profundidad, np.inf)


def a_srgb(lineal: float) -> float:
    return lineal * 12.92 if lineal <= 0.0031308 else 1.055 * lineal ** (1 / 2.4) - 0.055


def a_lineal(srgb: float) -> float:
    return srgb / 12.92 if srgb <= 0.04045 else ((srgb + 0.055) / 1.055) ** 2.4


def identificar(pasada: np.ndarray) -> np.ndarray:
    """Convierte la pasada de colores planos en el índice de material (0 = vacío)."""
    esperados = np.array([a_srgb(color_identificador(indice)[0]) for indice in range(len(MATERIALES))])
    cercano = np.abs(pasada[..., 0, None] - esperados).argmin(axis=-1) + 1
    return np.where(pasada[..., 3] > 0.5, cercano, 0)


def agrupar(pasada: np.ndarray) -> np.ndarray:
    """Agrupa los subpíxeles de cada píxel final en el último eje."""
    lado = LADO_CUADRO
    return pasada.reshape(lado, SUBMUESTREO, lado, SUBMUESTREO).transpose(0, 2, 1, 3).reshape(lado, lado, -1)


def reducir(indices: np.ndarray, luz: np.ndarray, profundidad: np.ndarray):
    """Reduce a la resolución final eligiendo un material por píxel, con su luz y profundidad medias."""
    bloques, luces, profundidades = agrupar(indices), agrupar(luz), agrupar(profundidad)
    conteos = np.stack([(bloques == indice).sum(-1) for indice in range(len(MATERIALES) + 1)], -1)

    elegido = conteos.argmax(-1)
    for nombre in reversed(DETALLES):
        indice = MATERIALES.index(nombre) + 1
        elegido = np.where(conteos[..., indice] >= COBERTURA_DETALLE, indice, elegido)

    mascara = bloques == elegido[..., None]
    cantidad = np.maximum(mascara.sum(-1), 1)
    luz_media = (luces * mascara).sum(-1) / cantidad
    profundidad_media = np.where(mascara, np.nan_to_num(profundidades, posinf=0), 0).sum(-1) / cantidad
    return elegido, luz_media, np.where(elegido > 0, profundidad_media, np.inf)


def contorno(profundidad: np.ndarray) -> np.ndarray:
    """Marca los píxeles junto al vacío o detrás de una parte que los tapa."""
    lleno = np.isfinite(profundidad)
    relleno = np.pad(profundidad, 1, constant_values=np.inf)
    alto, ancho = profundidad.shape
    borde = np.zeros_like(lleno)
    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        vecino = relleno[1 + dy : 1 + dy + alto, 1 + dx : 1 + dx + ancho]
        borde |= ~np.isfinite(vecino) | (vecino < profundidad - SALTO_PROFUNDIDAD)
    return lleno & borde


def pintar(elegido: np.ndarray, luz: np.ndarray, profundidad: np.ndarray) -> Image.Image:
    """Pinta cada píxel con el tono de su rampa y traza los contornos."""
    salida = np.zeros((*elegido.shape, 4), dtype=np.uint8)
    tono = np.where(contorno(profundidad), 0, 1 + np.searchsorted(UMBRALES_LUZ, luz))

    for indice, nombre in enumerate(MATERIALES, start=1):
        rampa = np.array([a_rgb(color) for color in RAMPAS[nombre]], dtype=np.uint8)
        mascara = elegido == indice
        salida[mascara, :3] = rampa[tono[mascara]]
        salida[mascara, 3] = 255
    for ojo in regiones(elegido == MATERIALES.index("ojo") + 1):
        dibujar_ojo(salida, ojo)
    return Image.fromarray(salida)


def regiones(mascara: np.ndarray) -> list[set[tuple[int, int]]]:
    """Separa la máscara en grupos de píxeles conectados (uno por ojo)."""
    pendientes = set(zip(*np.nonzero(mascara)))
    grupos = []
    while pendientes:
        frontera = [pendientes.pop()]
        grupo = set(frontera)
        while frontera:
            y, x = frontera.pop()
            for vecino in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                if vecino in pendientes:
                    pendientes.remove(vecino)
                    grupo.add(vecino)
                    frontera.append(vecino)
        grupos.append(grupo)
    return grupos


def dibujar_ojo(salida: np.ndarray, pixeles: set[tuple[int, int]]):
    """Pinta un ojo al estilo de los sprites hechos a mano, sea cual sea su tamaño."""
    filas = [y for y, _ in pixeles]
    columnas = [x for _, x in pixeles]
    arriba, abajo = min(filas), max(filas)
    izquierda, derecha = min(columnas), max(columnas)
    centro = (izquierda + derecha) / 2
    pupila = {int(np.floor(centro - 0.5)), int(np.floor(centro + 0.5))} if derecha - izquierda >= 3 else {round(centro)}
    columna_brillo = max(pupila) + 1
    alto = abajo - arriba + 1

    for y, x in pixeles:
        if y == arriba:
            color = OJO["borde"]
        elif y == abajo and alto >= 4:
            color = OJO["iris_oscuro"]
        elif x == columna_brillo and y in (arriba + 1, arriba + 2) and alto >= 4:
            color = OJO["brillo"]
        elif x in pupila and y <= abajo - 2:
            color = OJO["pupila"]
        elif y == abajo - 1 and alto >= 4:
            color = OJO["iris_claro"]
        elif x in (izquierda, derecha):
            color = OJO["iris_oscuro"]
        else:
            color = OJO["iris"]
        salida[y, x, :3] = a_rgb(color)


def renderizar_cuadro(carpeta: Path, material_profundidad) -> Image.Image:
    indices = identificar(renderizar_pasada(carpeta / "id.png", "FLAT", "MATERIAL"))
    luz = renderizar_pasada(carpeta / "luz.png", "STUDIO", "SINGLE")[..., 0]
    profundidad = renderizar_profundidad(carpeta / "profundidad.png", material_profundidad)
    return pintar(*reducir(indices, luz, profundidad))


def renderizar_hoja(modelo, camara, material_profundidad, animacion, vista, animo, prendas, cuadros, carpeta) -> Image.Image:
    vestir(modelo, animo, prendas)
    apuntar(camara, vista)
    hoja = Image.new("RGBA", (LADO_CUADRO * cuadros, LADO_CUADRO))
    for cuadro in range(cuadros):
        pose = ANIMACIONES[animacion](cuadro / cuadros, animo)
        if vista in GIRO_CABEZA:
            cabeza = pose.setdefault("cabeza", {})
            cabeza["rot"] = tuple(a + b for a, b in zip(cabeza.get("rot", (0, 0, 0)), GIRO_CABEZA[vista]))
        posar(modelo, pose)
        hoja.paste(renderizar_cuadro(carpeta, material_profundidad), (cuadro * LADO_CUADRO, 0))
    return hoja


def lista(texto: str) -> list[str]:
    return [valor for valor in texto.split(",") if valor]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--animacion", type=lista, default=["caminar"])
    parser.add_argument("--vista", type=lista, default=["lado"])
    parser.add_argument("--animo", type=lista, default=["feliz"])
    parser.add_argument("--prendas", type=lista, default=[])
    parser.add_argument("--cuadros", type=int, default=4)
    parser.add_argument("--blend", type=Path, help="guarda también el modelo como archivo .blend")
    parser.add_argument("-o", "--salida", type=Path, required=True)
    argumentos = parser.parse_args()

    modelo = construir()
    camara, material_profundidad = preparar_escena()
    argumentos.salida.mkdir(parents=True, exist_ok=True)
    if argumentos.blend:
        bpy.ops.wm.save_as_mainfile(filepath=str(argumentos.blend.resolve()))

    sufijo_prendas = "".join(f"_{prenda}" for prenda in argumentos.prendas)
    with tempfile.TemporaryDirectory() as temporal:
        for animacion in argumentos.animacion:
            for vista in argumentos.vista:
                for animo in argumentos.animo:
                    hoja = renderizar_hoja(
                        modelo, camara, material_profundidad, animacion, vista, animo, argumentos.prendas, argumentos.cuadros, Path(temporal)
                    )
                    ruta = argumentos.salida / f"{animacion}_{vista}_{animo}{sufijo_prendas}.png"
                    hoja.save(ruta)
                    print(ruta)


if __name__ == "__main__":
    main()
