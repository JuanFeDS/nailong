"""Reducción a resolución nativa de pixel art y cuantización de paleta."""

from PIL import Image


def recortar_contenido(imagen: Image.Image) -> Image.Image:
    """Recorta la imagen a la caja que contiene los píxeles no transparentes."""
    caja = imagen.getchannel("A").getbbox()
    return imagen.crop(caja) if caja else imagen


def reducir(imagen: Image.Image, alto_objetivo: int) -> Image.Image:
    """Reduce la imagen al alto indicado muestreando por vecino más cercano.

    El vecino más cercano evita mezclar colores, que es lo que difumina
    los bordes cuando una IA exporta pixel art a alta resolución.
    """
    ancho, alto = imagen.size
    ancho_objetivo = max(1, round(ancho * alto_objetivo / alto))
    return imagen.resize((ancho_objetivo, alto_objetivo), Image.NEAREST)


def cuantizar(imagen: Image.Image, cantidad_colores: int) -> Image.Image:
    """Limita la paleta a un número fijo de colores y binariza el alfa."""
    alfa = imagen.getchannel("A").point(lambda valor: 255 if valor >= 128 else 0)
    reducida = (
        imagen.convert("RGB")
        .quantize(colors=cantidad_colores, method=Image.FASTOCTREE, dither=Image.NONE)
        .convert("RGBA")
    )
    reducida.putalpha(alfa)
    return reducida
