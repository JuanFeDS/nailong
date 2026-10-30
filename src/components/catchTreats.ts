import type { Level } from '../lib/minigames'
import { playSfx } from '../lib/sound'
import { BAD, burst, comboMultiplier, createFx, type Fx, GOOD, popup, shake, vibrate } from './gameFx'
import type { GameSpec } from './MinigameCanvas'
import { drawNight } from './nightScene'

const WIDTH = 360
const HEIGHT = 480
const CELL = 64
const PLAYER_SIZE = 96
const FEET_Y = HEIGHT - 14
const PLAYER_SPEED = 430
const CATCH_HALF_WIDTH = 40
const CATCH_TOP = HEIGHT - 118
const WALK_FRAME_SECONDS = 0.07
const WALK_FRAMES = 8
const IDLE_FRAMES = 4
const IDLE_FRAME_SECONDS = 0.6
const GHOST_PENALTY = 3
const HURT_SECONDS = 0.35

const PUMPKIN = 'rooms/halloween/pumpkin_s.png'
const GHOST = 'rooms/halloween/ghost.png'
const WALK = 'sprites/nailong/walk_side.png'
const IDLE = 'sprites/nailong/idle_happy.png'
const CANDY_COLORS = ['#e8341c', '#f5a623', '#7dd33a', '#2f9be8', '#ff6bb0']
const PUMPKIN_COLORS = ['#ff9a2a', '#ffd84d', '#7dd33a']

const SETTINGS: Record<Level, { speed: number; spawn: number; minSpawn: number; ghost: number }> = {
  1: { speed: 120, spawn: 0.8, minSpawn: 0.3, ghost: 0.2 },
  2: { speed: 165, spawn: 0.7, minSpawn: 0.27, ghost: 0.27 },
  3: { speed: 210, spawn: 0.6, minSpawn: 0.24, ghost: 0.34 },
}

type Kind = 'candy' | 'pumpkin' | 'ghost'

interface Item {
  kind: Kind
  x: number
  y: number
  speed: number
  color: string
  spin: number
}

interface State {
  x: number
  facing: 1 | -1
  moving: boolean
  walkTime: number
  items: Item[]
  score: number
  combo: number
  fx: Fx
  nextSpawn: number
  hurtUntil: number
  costume: string | null
}

const ready = (image: HTMLImageElement | undefined): image is HTMLImageElement => !!image && image.complete && image.naturalWidth > 0

const drawCandy = (context: CanvasRenderingContext2D, item: Item) => {
  context.save()
  context.translate(item.x, item.y)
  context.rotate(Math.sin(item.spin) * 0.35)
  context.scale(1.7, 1.7)
  context.fillStyle = '#fff8d0'
  context.fillRect(-12, -3, 5, 6)
  context.fillRect(7, -3, 5, 6)
  context.fillStyle = item.color
  context.fillRect(-7, -5, 14, 10)
  context.fillStyle = '#fff8d0'
  context.fillRect(-1, -5, 3, 10)
  context.restore()
}

export const makeCatchTreats = (costume: string | null, level: Level): GameSpec<State> => {
  const settings = SETTINGS[level]
  const walkAssets = costume ? [`sprites/nailong/${costume}/walk_side.png`, `sprites/nailong/${costume}/idle_happy.png`] : []
  return {
    width: WIDTH,
    height: HEIGHT,
    seconds: 30,
    assets: [WALK, IDLE, PUMPKIN, GHOST, ...walkAssets],
    create: () => ({
      x: WIDTH / 2,
      facing: 1,
      moving: false,
      walkTime: 0,
      items: [],
      score: 0,
      combo: 0,
      fx: createFx(),
      nextSpawn: 0.3,
      hurtUntil: 0,
      costume,
    }),
    score: (state) => state.score,
    fx: (state) => state.fx,
    combo: (state) => comboMultiplier(state.combo),

    update(state, step, pointer, time) {
      if (pointer.x !== null) {
        const gap = pointer.x - state.x
        const move = Math.max(-PLAYER_SPEED * step, Math.min(PLAYER_SPEED * step, gap))
        state.moving = Math.abs(gap) > 3
        if (state.moving) state.facing = gap > 0 ? 1 : -1
        state.x = Math.min(WIDTH - 24, Math.max(24, state.x + move))
      } else {
        state.moving = false
      }
      state.walkTime += state.moving ? step : 0

      if (time >= state.nextSpawn) {
        state.nextSpawn = time + Math.max(settings.minSpawn, settings.spawn - time * 0.012)
        const roll = Math.random()
        const kind: Kind = roll < settings.ghost ? 'ghost' : roll < settings.ghost + 0.2 ? 'pumpkin' : 'candy'
        state.items.push({
          kind,
          x: 30 + Math.random() * (WIDTH - 60),
          y: -30,
          speed: settings.speed + time * 4 + Math.random() * 40,
          color: CANDY_COLORS[Math.floor(Math.random() * CANDY_COLORS.length)],
          spin: Math.random() * 6,
        })
      }

      state.items = state.items.filter((item) => {
        item.y += item.speed * step
        item.spin += step * 5
        if (item.y >= CATCH_TOP && item.y <= FEET_Y && Math.abs(item.x - state.x) <= CATCH_HALF_WIDTH) {
          if (item.kind === 'ghost') {
            const lost = Math.min(GHOST_PENALTY, state.score)
            state.score -= lost
            state.combo = 0
            state.hurtUntil = time + HURT_SECONDS
            popup(state.fx, state.x, CATCH_TOP, `-${GHOST_PENALTY}`, time, BAD)
            burst(state.fx, state.x, CATCH_TOP + 20, [BAD, '#fff8e8'], time, 8)
            shake(state.fx, time, 7)
            vibrate(120)
            playSfx('miss')
          } else {
            const before = comboMultiplier(state.combo)
            state.combo += 1
            const multiplier = comboMultiplier(state.combo)
            const gained = (item.kind === 'pumpkin' ? 3 : 1) * multiplier
            state.score += gained
            popup(state.fx, state.x, CATCH_TOP, `+${gained}`, time, GOOD)
            burst(state.fx, item.x, item.y, item.kind === 'pumpkin' ? PUMPKIN_COLORS : [item.color, '#fff8d0'], time, item.kind === 'pumpkin' ? 12 : 7)
            vibrate(12)
            if (multiplier > before) {
              popup(state.fx, WIDTH / 2, 150, `¡Combo ×${multiplier}!`, time, '#ff9a2a')
              playSfx('combo')
            } else {
              playSfx(item.kind === 'pumpkin' ? 'bonus' : 'hit')
            }
          }
          return false
        }
        if (item.kind !== 'ghost' && item.y > FEET_Y && item.y - item.speed * step <= FEET_Y) {
          state.combo = 0
          burst(state.fx, item.x, FEET_Y - 4, ['#24492f', '#2f6040'], time, 5)
        }
        return item.y < HEIGHT + 40
      })
    },

    draw(context, state, images, time) {
      drawNight(context, WIDTH, HEIGHT, FEET_Y - 4, time)

      context.fillStyle = '#0d1f14'
      for (const item of state.items) {
        if (item.y < HEIGHT * 0.45 || item.y > FEET_Y) continue
        const near = (item.y - HEIGHT * 0.45) / (FEET_Y - HEIGHT * 0.45)
        const half = Math.round(6 + near * 14)
        context.fillRect(Math.round(item.x - half), FEET_Y - 2, half * 2, 4)
      }

      for (const item of state.items) {
        if (item.kind === 'candy') {
          drawCandy(context, item)
          continue
        }
        const image = images[item.kind === 'pumpkin' ? PUMPKIN : GHOST]
        if (!ready(image)) continue
        const scale = item.kind === 'pumpkin' ? 1.5 : 1.1
        const width = image.naturalWidth * scale
        const height = image.naturalHeight * scale
        context.drawImage(image, item.x - width / 2, item.y - height / 2, width, height)
      }

      const walking = state.moving
      const own = images[state.costume ? `sprites/nailong/${state.costume}/${walking ? 'walk_side' : 'idle_happy'}.png` : '']
      const sheet = ready(own) ? own : images[walking ? WALK : IDLE]
      if (ready(sheet)) {
        const frame = walking
          ? Math.floor(state.walkTime / WALK_FRAME_SECONDS) % WALK_FRAMES
          : Math.floor(time / IDLE_FRAME_SECONDS) % IDLE_FRAMES
        context.save()
        context.translate(state.x, FEET_Y)
        context.scale(state.facing, 1)
        if (time < state.hurtUntil) context.filter = 'brightness(0.6) sepia(1) saturate(6) hue-rotate(-30deg)'
        context.drawImage(sheet, frame * CELL, 0, CELL, CELL, -PLAYER_SIZE / 2, -PLAYER_SIZE, PLAYER_SIZE, PLAYER_SIZE)
        context.restore()
      }
    },
  }
}
