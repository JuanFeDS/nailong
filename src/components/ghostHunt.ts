import type { Level } from '../lib/minigames'
import { playSfx } from '../lib/sound'
import { BAD, burst, comboMultiplier, createFx, type Fx, GOOD, popup, shake, vibrate } from './gameFx'
import type { GameSpec } from './MinigameCanvas'
import { drawNight } from './nightScene'

const WIDTH = 360
const HEIGHT = 480
const GROUND_TOP = 372
const SCALE = 2
const TREE_SCALE = 1.1
const FADE_IN = 0.15
const FADE_OUT = 0.25
const POP_SECONDS = 0.25
const TAP_MARGIN = 8
const GOLD_CHANCE = 0.06
const GOLD_POINTS = 5
const BAT_PENALTY = 2
const SPAWN_TRIES = 8
const MIN_GAP = 76

const GHOST = 'rooms/halloween/ghost.png'
const BAT = 'rooms/halloween/bat.png'
const TREE = 'rooms/halloween/deadtree.png'
const DECOR = ['rooms/halloween/gravestone_a.png', 'rooms/halloween/gravestone_b.png', 'rooms/halloween/pumpkin.png', 'rooms/halloween/skull.png']

const GHOST_COLORS = ['#fff8e8', '#d8f4ff', '#ffd84d']
const GOLD_COLORS = ['#ffd84d', '#ff9a2a', '#fff8e8']

const SETTINGS: Record<Level, { life: number; minLife: number; spawn: number; minSpawn: number; bat: number; drift: number }> = {
  1: { life: 1.9, minLife: 0.9, spawn: 1.1, minSpawn: 0.45, bat: 0.12, drift: 0 },
  2: { life: 1.6, minLife: 0.8, spawn: 0.95, minSpawn: 0.4, bat: 0.2, drift: 34 },
  3: { life: 1.35, minLife: 0.7, spawn: 0.8, minSpawn: 0.34, bat: 0.28, drift: 64 },
}

interface Target {
  kind: 'ghost' | 'gold' | 'bat'
  x: number
  y: number
  drift: number
  born: number
  life: number
  hitAt: number | null
  escaped: boolean
}

interface State {
  targets: Target[]
  score: number
  combo: number
  nextSpawn: number
  fx: Fx
}

const sizeOf = (image: HTMLImageElement) => ({ width: image.naturalWidth * SCALE, height: image.naturalHeight * SCALE })
const ready = (image: HTMLImageElement) => image.complete && image.naturalWidth > 0

const xAt = (target: Target, time: number) => {
  const end = target.hitAt ?? time
  return Math.min(WIDTH - 40, Math.max(40, target.x + target.drift * (end - target.born)))
}

export const makeGhostHunt = (level: Level): GameSpec<State> => {
  const settings = SETTINGS[level]
  return {
    width: WIDTH,
    height: HEIGHT,
    seconds: 30,
    assets: [GHOST, BAT, TREE, ...DECOR],
    create: () => ({ targets: [], score: 0, combo: 0, nextSpawn: 0.4, fx: createFx() }),
    score: (state) => state.score,
    fx: (state) => state.fx,
    combo: (state) => comboMultiplier(state.combo),

    update(state, _step, pointer, time) {
      for (const target of state.targets) {
        if (target.kind !== 'bat' && target.hitAt === null && !target.escaped && time > target.born + target.life) {
          target.escaped = true
          state.combo = 0
        }
      }
      state.targets = state.targets.filter((target) => (target.hitAt ?? target.born + target.life) + (target.hitAt === null ? FADE_OUT : POP_SECONDS) > time)

      if (time >= state.nextSpawn) {
        const life = Math.max(settings.minLife, settings.life - time * 0.03)
        state.nextSpawn = time + Math.max(settings.minSpawn, settings.spawn - time * 0.02)
        for (let attempt = 0; attempt < SPAWN_TRIES; attempt += 1) {
          const x = 56 + Math.random() * (WIDTH - 112)
          const y = 110 + Math.random() * (GROUND_TOP - 170)
          const crowded = state.targets.some((target) => target.hitAt === null && Math.hypot(xAt(target, time) - x, target.y - y) < MIN_GAP)
          if (crowded) continue
          const roll = Math.random()
          const kind = roll < settings.bat ? 'bat' : roll < settings.bat + GOLD_CHANCE ? 'gold' : 'ghost'
          const drift = settings.drift * (Math.random() < 0.5 ? -1 : 1) * (0.5 + Math.random() * 0.5)
          state.targets.push({ kind, x, y, drift, born: time, life: kind === 'gold' ? life * 0.75 : life, hitAt: null, escaped: false })
          break
        }
      }

      for (const tap of pointer.taps) {
        const target = [...state.targets].reverse().find((candidate) => {
          if (candidate.hitAt !== null || time > candidate.born + candidate.life) return false
          const halfWidth = candidate.kind === 'bat' ? 56 : 44
          const halfHeight = candidate.kind === 'bat' ? 24 : 40
          return Math.abs(tap.x - xAt(candidate, time)) <= halfWidth + TAP_MARGIN && Math.abs(tap.y - candidate.y) <= halfHeight + TAP_MARGIN
        })
        if (!target) continue
        target.hitAt = time
        const x = xAt(target, time)
        if (target.kind === 'bat') {
          const lost = Math.min(BAT_PENALTY, state.score)
          state.score -= lost
          state.combo = 0
          popup(state.fx, x, target.y - 24, `-${BAT_PENALTY}`, time, BAD)
          burst(state.fx, x, target.y, [BAD, '#5a2430'], time, 8)
          shake(state.fx, time, 7)
          vibrate(120)
          playSfx('miss')
          continue
        }
        const before = comboMultiplier(state.combo)
        state.combo += 1
        const multiplier = comboMultiplier(state.combo)
        const gained = (target.kind === 'gold' ? GOLD_POINTS : 1) * multiplier
        state.score += gained
        popup(state.fx, x, target.y - 36, `+${gained}`, time, GOOD)
        burst(state.fx, x, target.y, target.kind === 'gold' ? GOLD_COLORS : GHOST_COLORS, time, target.kind === 'gold' ? 16 : 10)
        vibrate(15)
        if (multiplier > before) {
          popup(state.fx, WIDTH / 2, 150, `¡Combo ×${multiplier}!`, time, '#ff9a2a')
          playSfx('combo')
        } else {
          playSfx(target.kind === 'gold' ? 'bonus' : 'hit')
        }
      }
    },

    draw(context, state, images, time) {
      drawNight(context, WIDTH, HEIGHT, GROUND_TOP, time)

      const tree = images[TREE]
      if (ready(tree)) {
        const width = tree.naturalWidth * TREE_SCALE
        const height = tree.naturalHeight * TREE_SCALE
        context.drawImage(tree, WIDTH - width + 10, GROUND_TOP + 4 - height, width, height)
      }

      const decorBase = HEIGHT - 28
      const placements: [string, number][] = [[DECOR[0], 70], [DECOR[2], 160], [DECOR[1], 252], [DECOR[3], 320]]
      for (const [path, x] of placements) {
        const image = images[path]
        if (!ready(image)) continue
        const { width, height } = sizeOf(image)
        context.drawImage(image, x - width / 2, decorBase - height, width, height)
      }

      for (const target of state.targets) {
        const image = images[target.kind === 'bat' ? BAT : GHOST]
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
        const x = xAt(target, time)
        const bob = target.hitAt === null ? Math.sin(time * 5 + target.x) * 3 : 0
        context.save()
        context.globalAlpha = Math.max(0, alpha)
        if (target.kind === 'bat') {
          context.fillStyle = '#5a2430'
          context.beginPath()
          context.arc(x, target.y + bob, 40 * scale, 0, Math.PI * 2)
          context.fill()
        }
        if (target.kind === 'gold') {
          context.fillStyle = '#ffd84d'
          context.beginPath()
          context.arc(x, target.y + bob, 46 * scale, 0, Math.PI * 2)
          context.fill()
          context.filter = 'sepia(1) saturate(5) brightness(1.1)'
        }
        if (target.drift < 0) {
          context.translate(x, 0)
          context.scale(-1, 1)
          context.translate(-x, 0)
        }
        context.drawImage(image, x - (width * scale) / 2, target.y + bob - (height * scale) / 2, width * scale, height * scale)
        context.restore()

        if (target.hitAt === null && time <= target.born + target.life) {
          const left = 1 - (time - target.born) / target.life
          if (left < 0.35 && target.kind !== 'bat') {
            context.fillStyle = Math.floor(time * 10) % 2 === 0 ? BAD : '#fff8e8'
            context.fillRect(x - 3, target.y - height / 2 - 14 + bob, 6, 6)
          }
        }
      }
    },
  }
}
