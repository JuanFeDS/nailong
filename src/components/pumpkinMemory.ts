import type { GameSpec } from './MinigameCanvas'

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
}

const nextPumpkin = () => Math.floor(Math.random() * CENTERS.length)
const showSeconds = (rounds: number) => Math.max(0.28, 0.55 - rounds * 0.02)

export const pumpkinMemory: GameSpec<State> = {
  width: WIDTH,
  height: HEIGHT,
  seconds: 70,
  assets: [PUMPKIN],
  create: () => ({
    sequence: [nextPumpkin()],
    phase: 'pause',
    clock: ROUND_PAUSE,
    showIndex: 0,
    inputIndex: 0,
    lit: null,
    litLeft: 0,
    rounds: 0,
    failed: false,
    endDelay: FAIL_PAUSE,
  }),
  score: (state) => state.rounds,
  over: (state) => state.failed && state.endDelay <= 0,

  update(state, step, pointer) {
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
        state.showIndex += 1
        state.clock = onTime + SHOW_GAP
      }
    } else {
      for (const tap of pointer.taps) {
        const index = CENTERS.findIndex(([x, y]) => Math.abs(tap.x - x) <= HALF_WIDTH && Math.abs(tap.y - y) <= HALF_HEIGHT)
        if (index < 0) continue
        state.lit = index
        state.litLeft = TAP_LIT_SECONDS
        if (index !== state.sequence[state.inputIndex]) {
          state.failed = true
          return
        }
        state.inputIndex += 1
        if (state.inputIndex === state.sequence.length) {
          state.rounds += 1
          state.sequence.push(nextPumpkin())
          state.phase = 'pause'
          state.clock = ROUND_PAUSE
          return
        }
      }
    }
  },

  draw(context, state, images) {
    context.fillStyle = '#15112c'
    context.fillRect(0, 0, WIDTH, HEIGHT)
    context.fillStyle = '#f4ecc0'
    context.beginPath()
    context.arc(300, 64, 22, 0, Math.PI * 2)
    context.fill()

    const image = images[PUMPKIN]
    const loaded = image.complete && image.naturalWidth > 0
    CENTERS.forEach(([x, y], index) => {
      const lit = state.lit === index
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

    context.font = '22px monospace'
    context.textAlign = 'center'
    context.textBaseline = 'middle'
    context.fillStyle = state.failed ? '#ff6b5a' : '#fff'
    const message = state.failed ? '¡Fallaste!' : state.phase === 'input' ? '¡Tu turno!' : 'Mira…'
    context.fillText(message, WIDTH / 2, 112)
    context.font = '16px monospace'
    context.fillStyle = '#d8cc98'
    context.fillText(`Ronda ${state.rounds + 1}`, WIDTH / 2, 142)
  },
}
