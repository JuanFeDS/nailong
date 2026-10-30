import type { Level } from '../lib/minigames'
import { playPumpkinNote, playSfx } from '../lib/sound'
import { BAD, burst, createFx, type Fx, GOOD, popup, shake, vibrate } from './gameFx'
import type { GameSpec } from './MinigameCanvas'
import { drawNight } from './nightScene'

const WIDTH = 360
const HEIGHT = 480
const SCALE = 2
const PUMPKIN = 'rooms/halloween/pumpkin.png'
const CENTERS: [number, number][] = [[100, 210], [260, 210], [100, 360], [260, 360]]
const COLORS = ['#ff9a2a', '#7dd33a', '#2f9be8', '#ff4d6d']
const TAP_LIT_SECONDS = 0.28
const SHOW_GAP = 0.2
const ROUND_PAUSE = 0.8
const FAIL_PAUSE = 0.7
const HALF_WIDTH = 64
const HALF_HEIGHT = 60
const GROUND_TOP = 440
const STONE = '#3a4150'
const STONE_EDGE = '#525b6e'

const SETTINGS: Record<Level, { start: number; show: number; minShow: number }> = {
  1: { start: 1, show: 0.55, minShow: 0.28 },
  2: { start: 3, show: 0.45, minShow: 0.24 },
  3: { start: 4, show: 0.36, minShow: 0.2 },
}

type Phase = 'pause' | 'show' | 'input'

interface State {
  sequence: number[]
  phase: Phase
  clock: number
  showIndex: number
  inputIndex: number
  lit: number | null
  litLeft: number
  rounds: number
  failed: boolean
  endDelay: number
  fx: Fx
}

const nextPumpkin = () => Math.floor(Math.random() * CENTERS.length)

export const makePumpkinMemory = (level: Level): GameSpec<State> => {
  const settings = SETTINGS[level]
  const showSeconds = (rounds: number) => Math.max(settings.minShow, settings.show - rounds * 0.02)
  return {
  width: WIDTH,
  height: HEIGHT,
  seconds: 70,
  assets: [PUMPKIN],
  create: () => ({
    sequence: Array.from({ length: settings.start }, nextPumpkin),
    phase: 'pause',
    clock: ROUND_PAUSE,
    showIndex: 0,
    inputIndex: 0,
    lit: null,
    litLeft: 0,
    rounds: 0,
    failed: false,
    endDelay: FAIL_PAUSE,
    fx: createFx(),
  }),
  score: (state) => state.rounds,
  fx: (state) => state.fx,
  over: (state) => state.failed && state.endDelay <= 0,

  update(state, step, pointer, time) {
    if (state.failed) {
      state.endDelay -= step
      return
    }
    if (state.litLeft > 0) {
      state.litLeft -= step
      if (state.litLeft <= 0) state.lit = null
    }

    if (state.phase === 'pause') {
      state.clock -= step
      if (state.clock <= 0) {
        state.phase = 'show'
        state.showIndex = 0
        state.clock = 0
      }
    } else if (state.phase === 'show') {
      state.clock -= step
      if (state.clock <= 0) {
        if (state.showIndex >= state.sequence.length) {
          state.phase = 'input'
          state.inputIndex = 0
          return
        }
        const onTime = showSeconds(state.rounds)
        state.lit = state.sequence[state.showIndex]
        state.litLeft = onTime
        playPumpkinNote(state.lit)
        state.showIndex += 1
        state.clock = onTime + SHOW_GAP
      }
    } else {
      for (const tap of pointer.taps) {
        const index = CENTERS.findIndex(([x, y]) => Math.abs(tap.x - x) <= HALF_WIDTH && Math.abs(tap.y - y) <= HALF_HEIGHT)
        if (index < 0) continue
        state.lit = index
        state.litLeft = TAP_LIT_SECONDS
        const [x, y] = CENTERS[index]
        if (index !== state.sequence[state.inputIndex]) {
          state.failed = true
          shake(state.fx, time, 9, 0.35)
          burst(state.fx, x, y, [BAD, '#5a2430'], time, 12)
          vibrate(200)
          playSfx('miss')
          return
        }
        playPumpkinNote(index)
        burst(state.fx, x, y - 20, [COLORS[index], '#fff8d0'], time, 6)
        vibrate(10)
        state.inputIndex += 1
        if (state.inputIndex === state.sequence.length) {
          state.rounds += 1
          popup(state.fx, WIDTH / 2, 176, `¡Ronda ${state.rounds}!`, time, GOOD)
          window.setTimeout(() => playSfx('combo'), 160)
          state.sequence.push(nextPumpkin())
          state.phase = 'pause'
          state.clock = ROUND_PAUSE
          return
        }
      }
    }
  },

  draw(context, state, images, time) {
    drawNight(context, WIDTH, HEIGHT, GROUND_TOP, time)

    const image = images[PUMPKIN]
    const loaded = image.complete && image.naturalWidth > 0
    CENTERS.forEach(([x, y], index) => {
      const lit = state.lit === index
      context.fillStyle = STONE
      context.fillRect(x - 52, y + 30, 104, 20)
      context.fillStyle = STONE_EDGE
      context.fillRect(x - 52, y + 30, 104, 4)
      context.fillStyle = COLORS[index]
      context.fillRect(x - 16, y + 40, 32, 4)
      if (lit) {
        context.fillStyle = state.failed ? '#ff4d6d' : COLORS[index]
        context.globalAlpha = 0.55
        context.beginPath()
        context.arc(x, y, 76, 0, Math.PI * 2)
        context.fill()
        context.globalAlpha = 1
      }
      if (!loaded) return
      const width = image.naturalWidth * SCALE
      const height = image.naturalHeight * SCALE
      context.save()
      if (!lit) context.filter = 'brightness(0.45)'
      context.drawImage(image, x - width / 2, y + height / 2 - height, width, height)
      context.restore()
    })

    context.font = '24px "Pixelify Sans", monospace'
    context.textAlign = 'center'
    context.textBaseline = 'middle'
    context.fillStyle = state.failed ? '#ff6b5a' : '#fff'
    const message = state.failed ? '¡Fallaste!' : state.phase === 'input' ? '¡Tu turno!' : 'Mira…'
    context.fillText(message, WIDTH / 2, 112)
    context.font = '16px "Pixelify Sans", monospace'
    context.fillStyle = '#d8cc98'
    context.fillText(`Ronda ${state.rounds + 1} · ${state.sequence.length} calabazas`, WIDTH / 2, 142)
    if (state.phase === 'input' && !state.failed) {
      const dot = 10
      const total = state.sequence.length
      const startX = WIDTH / 2 - ((total - 1) * (dot + 6)) / 2
      for (let index = 0; index < total; index += 1) {
        context.fillStyle = index < state.inputIndex ? GOOD : '#3a4150'
        context.fillRect(Math.round(startX + index * (dot + 6) - dot / 2), 158, dot, dot)
      }
    }
  },
  }
}
