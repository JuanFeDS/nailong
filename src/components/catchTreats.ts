import type { GameSpec } from './MinigameCanvas'

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

type Kind = 'candy' | 'pumpkin' | 'ghost'

interface Item {
  kind: Kind
  x: number
  y: number
  speed: number
  color: string
  spin: number
}

interface Popup {
  x: number
  y: number
  text: string
  born: number
}

interface State {
  x: number
  facing: 1 | -1
  moving: boolean
  walkTime: number
  items: Item[]
  popups: Popup[]
  score: number
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

export const makeCatchTreats = (costume: string | null): GameSpec<State> => {
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
      popups: [],
      score: 0,
      nextSpawn: 0.3,
      hurtUntil: 0,
      costume,
    }),
    score: (state) => state.score,

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
        state.nextSpawn = time + Math.max(0.3, 0.8 - time * 0.012)
        const roll = Math.random()
        const kind: Kind = roll < 0.6 ? 'candy' : roll < 0.8 ? 'pumpkin' : 'ghost'
        state.items.push({
          kind,
          x: 30 + Math.random() * (WIDTH - 60),
          y: -30,
          speed: 120 + time * 4 + Math.random() * 40,
          color: CANDY_COLORS[Math.floor(Math.random() * CANDY_COLORS.length)],
          spin: Math.random() * 6,
        })
      }

      state.popups = state.popups.filter((popup) => time - popup.born < 0.7)
      state.items = state.items.filter((item) => {
        item.y += item.speed * step
        item.spin += step * 5
        if (item.y >= CATCH_TOP && item.y <= FEET_Y && Math.abs(item.x - state.x) <= CATCH_HALF_WIDTH) {
          if (item.kind === 'ghost') {
            const lost = Math.min(GHOST_PENALTY, state.score)
            state.score -= lost
            state.hurtUntil = time + HURT_SECONDS
            state.popups.push({ x: state.x, y: CATCH_TOP, text: `-${GHOST_PENALTY}`, born: time })
          } else {
            const gained = item.kind === 'pumpkin' ? 3 : 1
            state.score += gained
            state.popups.push({ x: state.x, y: CATCH_TOP, text: `+${gained}`, born: time })
          }
          return false
        }
        return item.y < HEIGHT + 40
      })
    },

    draw(context, state, images, time) {
      context.fillStyle = '#15112c'
      context.fillRect(0, 0, WIDTH, HEIGHT)
      context.fillStyle = '#f4ecc0'
      context.beginPath()
      context.arc(300, 64, 22, 0, Math.PI * 2)
      context.fill()
      context.fillStyle = '#16301f'
      context.fillRect(0, FEET_Y - 4, WIDTH, HEIGHT - FEET_Y + 4)

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
}
