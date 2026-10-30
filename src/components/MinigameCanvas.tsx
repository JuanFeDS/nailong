import { useEffect, useRef, useState } from 'react'
import { asset } from '../lib/asset'
import { type Level, loadProgress, type MinigameId, saveProgress, starsFor } from '../lib/minigames'
import { playSfx } from '../lib/sound'
import { drawFx, type Fx, shakeOffset, stepFx, vibrate } from './gameFx'

export interface Pointer {
  x: number | null
  y: number | null
  taps: { x: number; y: number }[]
}

export interface GameSpec<State> {
  width: number
  height: number
  seconds: number
  assets: string[]
  create: () => State
  update: (state: State, dt: number, pointer: Pointer, time: number) => void
  draw: (context: CanvasRenderingContext2D, state: State, images: Record<string, HTMLImageElement>, time: number) => void
  score: (state: State) => number
  fx: (state: State) => Fx
  combo?: (state: State) => number
  over?: (state: State) => boolean
}

interface Props<State> {
  id: MinigameId
  level: Level
  spec: GameSpec<State>
  reward: (score: number) => Promise<number | null>
  onNext: (() => void) | null
  onExit: () => void
}

interface Result {
  score: number
  stars: number
  record: number
  isNew: boolean
  unlocked: boolean
  coins: number | null | 'pending'
}

const COUNTDOWN_SECONDS = 3
const MAX_STEP = 0.05
const HUD_FONT = '"Pixelify Sans", monospace'
const INK = '#fff8e8'
const OUTLINE = '#120c0a'
const SUN = '#ffd84d'
const HOT = '#ff5a4a'

const outlined = (context: CanvasRenderingContext2D, text: string, x: number, y: number, color: string, width = 4) => {
  context.lineWidth = width
  context.strokeStyle = OUTLINE
  context.strokeText(text, x, y)
  context.fillStyle = color
  context.fillText(text, x, y)
}

export function MinigameCanvas<State>({ id, level, spec, reward, onNext, onExit }: Props<State>) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [round, setRound] = useState(0)
  const [result, setResult] = useState<Result | null>(null)
  const rewardRef = useRef(reward)
  rewardRef.current = reward

  useEffect(() => {
    const canvas = canvasRef.current
    const context = canvas?.getContext('2d')
    if (!canvas || !context) return
    context.imageSmoothingEnabled = false

    const images = Object.fromEntries(
      spec.assets.map((path) => {
        const image = new Image()
        image.src = asset(path)
        return [path, image]
      }),
    )
    const state = spec.create()
    const pointer: Pointer = { x: null, y: null, taps: [] }
    let countdown = COUNTDOWN_SECONDS
    let gameTime = 0
    let last = performance.now()
    let frame = 0
    let lastBeep = Math.ceil(COUNTDOWN_SECONDS)
    let finished = false

    const toGame = (event: PointerEvent) => {
      const rect = canvas.getBoundingClientRect()
      return {
        x: ((event.clientX - rect.left) / rect.width) * spec.width,
        y: ((event.clientY - rect.top) / rect.height) * spec.height,
      }
    }
    const handleDown = (event: PointerEvent) => {
      const point = toGame(event)
      pointer.x = point.x
      pointer.y = point.y
      pointer.taps.push(point)
    }
    const handleMove = (event: PointerEvent) => {
      const point = toGame(event)
      pointer.x = point.x
      pointer.y = point.y
    }
    canvas.addEventListener('pointerdown', handleDown)
    canvas.addEventListener('pointermove', handleMove)

    const drawHud = () => {
      const left = Math.max(0, spec.seconds - gameTime)
      const share = left / spec.seconds
      const urgent = left <= 5 && countdown <= 0

      context.fillStyle = OUTLINE
      context.fillRect(0, 0, spec.width, 8)
      context.fillStyle = urgent && Math.floor(gameTime * 4) % 2 === 0 ? HOT : SUN
      context.fillRect(0, 0, Math.round(spec.width * share), 8)

      context.textBaseline = 'top'
      context.font = `24px ${HUD_FONT}`
      context.textAlign = 'left'
      outlined(context, `★ ${spec.score(state)}`, 12, 16, SUN)
      context.textAlign = 'right'
      outlined(context, `${Math.ceil(left)} s`, spec.width - 12, 16, urgent ? HOT : INK)
      context.font = `16px ${HUD_FONT}`
      context.textAlign = 'center'
      outlined(context, `Nivel ${level}`, spec.width / 2, 20, INK, 3)

      const multiplier = spec.combo?.(state) ?? 1
      if (multiplier > 1) {
        const pulse = 1 + Math.sin(gameTime * 14) * 0.06
        context.save()
        context.translate(42, 58)
        context.scale(pulse, pulse)
        context.fillStyle = HOT
        context.fillRect(-30, -13, 60, 26)
        context.fillStyle = OUTLINE
        context.fillRect(-30, 11, 60, 4)
        context.font = `20px ${HUD_FONT}`
        context.textBaseline = 'middle'
        outlined(context, `×${multiplier}`, 0, 0, INK, 3)
        context.restore()
      }
    }

    const drawCountdown = () => {
      const number = Math.ceil(countdown)
      if (number !== lastBeep) {
        lastBeep = number
        playSfx('hit')
      }
      const progress = 1 - (countdown - Math.floor(countdown))
      context.save()
      context.globalAlpha = 0.45
      context.fillStyle = OUTLINE
      context.fillRect(0, 0, spec.width, spec.height)
      context.restore()
      context.save()
      context.translate(spec.width / 2, spec.height / 2)
      const scale = 1.4 - Math.min(1, progress * 3) * 0.4
      context.scale(scale, scale)
      context.font = `96px ${HUD_FONT}`
      context.textAlign = 'center'
      context.textBaseline = 'middle'
      outlined(context, String(number), 0, 0, SUN, 8)
      context.restore()
    }

    const finish = () => {
      finished = true
      spec.draw(context, state, images, gameTime)
      const score = spec.score(state)
      const stars = starsFor(id, level, score)
      const progress = loadProgress(id)
      const index = level - 1
      const previousRecord = progress.records[index]
      const unlocked = level < 3 && progress.stars[index] === 0 && stars > 0
      progress.records[index] = Math.max(previousRecord, score)
      progress.stars[index] = Math.max(progress.stars[index], stars)
      saveProgress(id, progress)
      if (stars > 0) playSfx('levelup')
      vibrate(stars > 0 ? [30, 60, 30] : 80)
      setResult({ score, stars, record: progress.records[index], isNew: score > previousRecord, unlocked, coins: score > 0 ? 'pending' : null })
      if (score > 0) rewardRef.current(score).catch(() => null).then((coins) => setResult((current) => current && { ...current, coins }))
    }

    const loop = (now: number) => {
      const step = document.hidden ? 0 : Math.min(MAX_STEP, (now - last) / 1000)
      last = now
      if (countdown > 0) {
        countdown -= step
        pointer.taps.length = 0
      } else {
        gameTime += step
        spec.update(state, step, pointer, gameTime)
        stepFx(spec.fx(state), step, gameTime)
        pointer.taps.length = 0
      }
      const [shakeX, shakeY] = shakeOffset(spec.fx(state), gameTime)
      context.save()
      context.translate(shakeX, shakeY)
      spec.draw(context, state, images, gameTime)
      drawFx(context, spec.fx(state), gameTime)
      context.restore()
      drawHud()
      if (countdown > 0) drawCountdown()
      if (!finished && (gameTime >= spec.seconds || spec.over?.(state))) {
        finish()
        return
      }
      frame = requestAnimationFrame(loop)
    }
    frame = requestAnimationFrame(loop)

    return () => {
      cancelAnimationFrame(frame)
      canvas.removeEventListener('pointerdown', handleDown)
      canvas.removeEventListener('pointermove', handleMove)
    }
  }, [id, level, spec, round])

  const playAgain = () => {
    setResult(null)
    setRound((count) => count + 1)
  }

  return (
    <div className="minigame">
      <div className="minigame__stage">
        <canvas ref={canvasRef} className="minigame__canvas" width={spec.width} height={spec.height} />
        {result && (
          <div className="minigame__result" role="dialog" aria-label="Resultado">
            <p className="minigame__level">Nivel {level}</p>
            <div className="minigame__stars" aria-label={`${result.stars} de 3 estrellas`}>
              {[0, 1, 2].map((index) => (
                <span
                  key={index}
                  className={`minigame__star${index < result.stars ? ' is-on' : ''}`}
                  style={{ animationDelay: `${0.15 + index * 0.18}s` }}
                >
                  ★
                </span>
              ))}
            </div>
            <h2 className="minigame__score">{result.score} puntos</h2>
            <p className="minigame__record">{result.isNew ? '¡Récord nuevo!' : `Récord: ${result.record}`}</p>
            {result.coins === 'pending' && <p className="minigame__coins">Contando monedas…</p>}
            {typeof result.coins === 'number' && (
              <p className="minigame__coins">{result.coins > 0 ? `+${result.coins} monedas` : 'Ya ganaste el tope de monedas de hoy'}</p>
            )}
            {result.unlocked && <p className="minigame__unlock">¡Nivel {level + 1} desbloqueado!</p>}
            {result.stars === 0 && level < 3 && <p className="minigame__hint">Consigue una estrella para abrir el siguiente nivel.</p>}
            {onNext && result.stars > 0 ? (
              <button className="btn" onClick={onNext}>
                Siguiente nivel
              </button>
            ) : null}
            <button className={onNext && result.stars > 0 ? 'ghost' : 'btn'} onClick={playAgain}>
              Jugar otra vez
            </button>
            <button className="ghost" onClick={onExit}>
              Volver
            </button>
          </div>
        )}
      </div>
      {!result && (
        <button className="ghost" onClick={onExit}>
          Salir
        </button>
      )}
    </div>
  )
}
