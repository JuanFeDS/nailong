import type { GameSpec } from './MinigameCanvas'

const WIDTH = 360
const HEIGHT = 480
const GROUND_TOP = 372
const SCALE = 2
const FADE_IN = 0.15
const FADE_OUT = 0.25
const POP_SECONDS = 0.25
const TAP_MARGIN = 8
const BAT_CHANCE = 0.14
const BAT_PENALTY = 2
const SPAWN_TRIES = 8
const MIN_GAP = 76

const GHOST = 'rooms/halloween/ghost.png'
const BAT = 'rooms/halloween/bat.png'
const DECOR = ['rooms/halloween/gravestone_a.png', 'rooms/halloween/gravestone_b.png', 'rooms/halloween/pumpkin.png', 'rooms/halloween/skull.png']

const STARS = [[28, 40], [70, 96], [120, 30], [168, 74], [212, 24], [248, 110], [330, 140], [40, 180], [300, 220], [96, 250], [200, 160]]

interface Target {
  kind: 'ghost' | 'bat'
  x: number
  y: number
  born: number
  life: number
  hitAt: number | null
}

interface Popup {
  x: number
  y: number
  text: string
  born: number
}

interface State {
  targets: Target[]
  popups: Popup[]
  score: number
  nextSpawn: number
}

const sizeOf = (image: HTMLImageElement) => ({ width: image.naturalWidth * SCALE, height: image.naturalHeight * SCALE })
const ready = (image: HTMLImageElement) => image.complete && image.naturalWidth > 0

export const ghostHunt: GameSpec<State> = {
  width: WIDTH,
  height: HEIGHT,
  seconds: 30,
  assets: [GHOST, BAT, ...DECOR],
  create: () => ({ targets: [], popups: [], score: 0, nextSpawn: 0.4 }),
  score: (state) => state.score,

  update(state, _step, pointer, time) {
    state.targets = state.targets.filter((target) => (target.hitAt ?? target.born + target.life) + (target.hitAt === null ? FADE_OUT : POP_SECONDS) > time)
    state.popups = state.popups.filter((popup) => time - popup.born < 0.7)

    if (time >= state.nextSpawn) {
      const life = Math.max(0.9, 1.9 - time * 0.03)
      state.nextSpawn = time + Math.max(0.45, 1.1 - time * 0.02)
      for (let attempt = 0; attempt < SPAWN_TRIES; attempt += 1) {
        const x = 56 + Math.random() * (WIDTH - 112)
        const y = 110 + Math.random() * (GROUND_TOP - 170)
        const crowded = state.targets.some((target) => target.hitAt === null && Math.hypot(target.x - x, target.y - y) < MIN_GAP)
        if (crowded) continue
        state.targets.push({ kind: Math.random() < BAT_CHANCE ? 'bat' : 'ghost', x, y, born: time, life, hitAt: null })
        break
      }
    }

    for (const tap of pointer.taps) {
      const target = [...state.targets].reverse().find((candidate) => {
        if (candidate.hitAt !== null || time > candidate.born + candidate.life) return false
        const halfWidth = candidate.kind === 'ghost' ? 44 : 56
        const halfHeight = candidate.kind === 'ghost' ? 40 : 24
        return Math.abs(tap.x - candidate.x) <= halfWidth + TAP_MARGIN && Math.abs(tap.y - candidate.y) <= halfHeight + TAP_MARGIN
      })
      if (!target) continue
      target.hitAt = time
      if (target.kind === 'ghost') {
        state.score += 1
        state.popups.push({ x: target.x, y: target.y - 36, text: '+1', born: time })
      } else {
        const lost = Math.min(BAT_PENALTY, state.score)
        state.score -= lost
        state.popups.push({ x: target.x, y: target.y - 24, text: `-${BAT_PENALTY}`, born: time })
      }
    }
  },

  draw(context, state, images, time) {
    context.fillStyle = '#15112c'
    context.fillRect(0, 0, WIDTH, HEIGHT)
    context.fillStyle = '#fff8d0'
    for (const [x, y] of STARS) context.fillRect(x, y, 3, 3)
    context.fillStyle = '#f4ecc0'
    context.beginPath()
    context.arc(300, 64, 22, 0, Math.PI * 2)
    context.fill()
    context.fillStyle = '#d8cc98'
    context.beginPath()
    context.arc(292, 58, 5, 0, Math.PI * 2)
    context.arc(308, 72, 6, 0, Math.PI * 2)
    context.fill()
    context.fillStyle = '#16301f'
    context.fillRect(0, GROUND_TOP, WIDTH, HEIGHT - GROUND_TOP)

    const decorBase = HEIGHT - 28
    const placements: [string, number][] = [[DECOR[0], 56], [DECOR[2], 150], [DECOR[1], 246], [DECOR[3], 318]]
    for (const [path, x] of placements) {
      const image = images[path]
      if (!ready(image)) continue
      const { width, height } = sizeOf(image)
      context.drawImage(image, x - width / 2, decorBase - height, width, height)
    }

    for (const target of state.targets) {
      const image = images[target.kind === 'ghost' ? GHOST : BAT]
      if (!ready(image)) continue
      const { width, height } = sizeOf(image)
      let alpha = Math.min(1, (time - target.born) / FADE_IN)
      let scale = 1
      if (target.hitAt !== null) {
        const pop = Math.min(1, (time - target.hitAt) / POP_SECONDS)
        alpha = 1 - pop
        scale = 1 + pop * 0.6
      } else {
        alpha = Math.min(alpha, Math.max(0, (target.born + target.life + FADE_OUT - time) / FADE_OUT))
      }
      const bob = target.hitAt === null ? Math.sin(time * 5 + target.x) * 3 : 0
      context.save()
      context.globalAlpha = Math.max(0, alpha)
      if (target.kind === 'bat') {
        context.fillStyle = '#4a3a78'
        context.beginPath()
        context.arc(target.x, target.y + bob, 40 * scale, 0, Math.PI * 2)
        context.fill()
      }
      context.drawImage(image, target.x - (width * scale) / 2, target.y + bob - (height * scale) / 2, width * scale, height * scale)
      context.restore()
    }

    context.font = '28px monospace'
    context.textAlign = 'center'
    context.textBaseline = 'middle'
    for (const popup of state.popups) {
      const age = time - popup.born
      context.globalAlpha = Math.max(0, 1 - age / 0.7)
      context.fillStyle = popup.text.startsWith('-') ? '#ff6b5a' : '#ffd84d'
      context.fillText(popup.text, popup.x, popup.y - age * 40)
    }
    context.globalAlpha = 1
  },
}
