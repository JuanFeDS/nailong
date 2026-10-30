export const SKY = '#101a2c'
const FAR_HILLS = '#172840'
const NEAR_HILLS = '#1b3a2a'
const GROUND = '#16301f'
const GROUND_EDGE = '#24492f'
const GRASS = '#2f6040'
const MOON = '#f4ecc0'
const MOON_SHADE = '#d8cc98'
const STAR = '#fff8d0'

const STARS = [[28, 60], [70, 116], [120, 50], [168, 94], [212, 44], [248, 130], [330, 160], [40, 200], [300, 240], [96, 270], [200, 180], [150, 140], [20, 130], [340, 100]]

const hills = (context: CanvasRenderingContext2D, width: number, base: number, height: number, bumps: number, phase: number, color: string) => {
  context.fillStyle = color
  for (let x = 0; x < width; x += 4) {
    const top = base - height * (0.5 + 0.5 * Math.sin((x / width) * Math.PI * bumps + phase))
    context.fillRect(x, Math.round(top / 4) * 4, 4, base - top + 400)
  }
}

export function drawNight(context: CanvasRenderingContext2D, width: number, height: number, groundTop: number, time: number) {
  context.fillStyle = SKY
  context.fillRect(0, 0, width, height)

  STARS.forEach(([x, y], index) => {
    const twinkle = Math.floor(time * 2 + index * 0.7) % 5 === 0
    context.fillStyle = STAR
    context.fillRect(x, y, twinkle ? 2 : 3, twinkle ? 2 : 3)
    if (index % 4 === 0 && !twinkle) {
      context.fillRect(x - 3, y + 1, 2, 1)
      context.fillRect(x + 4, y + 1, 2, 1)
    }
  })

  context.fillStyle = MOON
  context.beginPath()
  context.arc(296, 84, 24, 0, Math.PI * 2)
  context.fill()
  context.fillStyle = MOON_SHADE
  context.beginPath()
  context.arc(288, 76, 5, 0, Math.PI * 2)
  context.arc(305, 92, 7, 0, Math.PI * 2)
  context.arc(300, 72, 3, 0, Math.PI * 2)
  context.fill()

  hills(context, width, groundTop - 6, 54, 3, 0.6, FAR_HILLS)
  hills(context, width, groundTop + 2, 26, 5, 2.1, NEAR_HILLS)

  context.fillStyle = GROUND
  context.fillRect(0, groundTop, width, height - groundTop)
  context.fillStyle = GROUND_EDGE
  context.fillRect(0, groundTop, width, 4)
  context.fillStyle = GRASS
  for (let x = 6; x < width; x += 22) {
    const tall = (x * 7) % 3
    context.fillRect(x, groundTop - 4 - tall * 2, 2, 4 + tall * 2)
    context.fillRect(x + 4, groundTop - 2 - tall, 2, 2 + tall)
  }
}
