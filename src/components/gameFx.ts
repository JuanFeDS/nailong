const POPUP_SECONDS = 0.7
const GRAVITY = 520

interface Popup {
  x: number
  y: number
  text: string
  color: string
  born: number
}

interface Particle {
  x: number
  y: number
  vx: number
  vy: number
  size: number
  color: string
  born: number
  life: number
}

export interface Fx {
  popups: Popup[]
  particles: Particle[]
  shakeUntil: number
  shakePower: number
}

export const createFx = (): Fx => ({ popups: [], particles: [], shakeUntil: 0, shakePower: 0 })

export const GOOD = '#ffd84d'
export const BAD = '#ff5a4a'

export function popup(fx: Fx, x: number, y: number, text: string, time: number, color = GOOD) {
  fx.popups.push({ x, y, text, color, born: time })
}

export function burst(fx: Fx, x: number, y: number, colors: string[], time: number, count = 10) {
  for (let index = 0; index < count; index += 1) {
    const angle = (index / count) * Math.PI * 2 + Math.random() * 0.6
    const speed = 90 + Math.random() * 140
    fx.particles.push({
      x,
      y,
      vx: Math.cos(angle) * speed,
      vy: Math.sin(angle) * speed - 80,
      size: 3 + Math.floor(Math.random() * 3) * 2,
      color: colors[index % colors.length],
      born: time,
      life: 0.45 + Math.random() * 0.3,
    })
  }
}

export function shake(fx: Fx, time: number, power = 6, seconds = 0.25) {
  fx.shakeUntil = time + seconds
  fx.shakePower = power
}

export function stepFx(fx: Fx, step: number, time: number) {
  fx.popups = fx.popups.filter((item) => time - item.born < POPUP_SECONDS)
  fx.particles = fx.particles.filter((particle) => {
    particle.vy += GRAVITY * step
    particle.x += particle.vx * step
    particle.y += particle.vy * step
    return time - particle.born < particle.life
  })
}

export function shakeOffset(fx: Fx, time: number): [number, number] {
  if (time >= fx.shakeUntil) return [0, 0]
  const power = fx.shakePower * ((fx.shakeUntil - time) / 0.25)
  return [Math.round((Math.random() * 2 - 1) * power), Math.round((Math.random() * 2 - 1) * power)]
}

export function drawFx(context: CanvasRenderingContext2D, fx: Fx, time: number) {
  for (const particle of fx.particles) {
    context.globalAlpha = Math.max(0, 1 - (time - particle.born) / particle.life)
    context.fillStyle = particle.color
    context.fillRect(Math.round(particle.x), Math.round(particle.y), particle.size, particle.size)
  }
  context.font = '28px "Pixelify Sans", monospace'
  context.textAlign = 'center'
  context.textBaseline = 'middle'
  context.lineWidth = 5
  context.strokeStyle = '#120c0a'
  for (const item of fx.popups) {
    const age = time - item.born
    const rise = Math.min(1, age / 0.12)
    context.globalAlpha = Math.max(0, 1 - age / POPUP_SECONDS)
    context.save()
    context.translate(item.x, item.y - age * 40)
    context.scale(0.6 + rise * 0.4, 0.6 + rise * 0.4)
    context.strokeText(item.text, 0, 0)
    context.fillStyle = item.color
    context.fillText(item.text, 0, 0)
    context.restore()
  }
  context.globalAlpha = 1
}

export const vibrate = (pattern: number | number[]) => navigator.vibrate?.(pattern)

export const comboMultiplier = (combo: number) => Math.min(3, 1 + Math.floor(combo / 5))
