"""Colocación del sprite en una celda de tamaño fijo."""

from PIL import Image


def anclar_en_celda(sprite: Image.Image, lado_celda: int) -> Image.Image:
    """Centra el sprite horizontalmente y apoya sus pies en el borde inferior.

    Usar siempre el mismo ancla evita que Nailong "salte" al alternar frames.
    """
    ancho, alto = sprite.size
    if ancho > lado_celda or alto > lado_celda:
        raise ValueError(
            f"El sprite ({ancho}x{alto}) no cabe en una celda de {lado_celda}px"
        )
    celda = Image.new("RGBA", (lado_celda, lado_celda), (0, 0, 0, 0))
    celda.paste(sprite, ((lado_celda - ancho) // 2, lado_celda - alto))
    return celda
