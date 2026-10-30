"""Primitivas para dibujar objetos en pixel art directamente en código."""

from PIL import Image, ImageDraw

Color = tuple[int, int, int]

TINTE_CONTORNO = (110, 24, 30)
FUERZA_CONTORNO = 0.55
VECINOS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def hex_a_rgb(codigo: str) -> Color:
    """Convierte '#rrggbb' en una tupla RGB."""
    codigo = codigo.lstrip("#")
    return (int(codigo[0:2], 16), int(codigo[2:4], 16), int(codigo[4:6], 16))


class Lienzo:
    """Lienzo transparente con figuras rellenas de color plano."""

    def __init__(self, ancho: int, alto: int):
        self.imagen = Image.new("RGBA", (ancho, alto), (0, 0, 0, 0))
        self.dibujo = ImageDraw.Draw(self.imagen)

    def rect(self, x0: int, y0: int, x1: int, y1: int, color: str):
        """Rectángulo relleno con esquinas incluidas (x1 e y1 inclusivos)."""
        self.dibujo.rectangle((x0, y0, x1, y1), fill=hex_a_rgb(color))

    def redondo(self, x0: int, y0: int, x1: int, y1: int, radio: int, color: str):
        """Rectángulo con esquinas redondeadas."""
        self.dibujo.rounded_rectangle((x0, y0, x1, y1), radius=radio, fill=hex_a_rgb(color))

    def elipse(self, x0: int, y0: int, x1: int, y1: int, color: str):
        """Elipse rellena dentro de la caja indicada."""
        self.dibujo.ellipse((x0, y0, x1, y1), fill=hex_a_rgb(color))

    def poligono(self, puntos: list[tuple[int, int]], color: str):
        """Polígono relleno."""
        self.dibujo.polygon(puntos, fill=hex_a_rgb(color))

    def linea(self, puntos: list[tuple[int, int]], color: str, grosor: int = 1):
        """Línea o polilínea de grosor fijo."""
        self.dibujo.line(puntos, fill=hex_a_rgb(color), width=grosor)

    def punto(self, x: int, y: int, color: str):
        """Un solo píxel."""
        self.imagen.putpixel((x, y), (*hex_a_rgb(color), 255))

    def terminar(self) -> Image.Image:
        """Oscurece el borde exterior hacia un tono rojizo, como los muebles generados."""
        ancho, alto = self.imagen.size
        origen = self.imagen.load()
        resultado = self.imagen.copy()
        destino = resultado.load()
        for y in range(alto):
            for x in range(ancho):
                pixel = origen[x, y]
                if pixel[3] == 0:
                    continue
                borde = any(
                    not (0 <= x + dx < ancho and 0 <= y + dy < alto) or origen[x + dx, y + dy][3] == 0
                    for dx, dy in VECINOS
                )
                if borde:
                    destino[x, y] = (
                        *(int(canal * FUERZA_CONTORNO + tinte * (1 - FUERZA_CONTORNO) * 0.6)
                          for canal, tinte in zip(pixel[:3], TINTE_CONTORNO)),
                        255,
                    )
        return resultado
