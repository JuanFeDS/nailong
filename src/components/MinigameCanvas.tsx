import { useEffect, useRef, useState } from 'react'
import { asset } from '../lib/asset'
import { loadRecord, type MinigameId, saveRecord } from '../lib/minigames'

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
}

interface Props<State> {
  id: MinigameId
  spec: GameSpec<State>
  onExit: () => void
}

const COUNTDOWN_SECONDS = 3
const MAX_STEP = 0.05

export function MinigameCanvas<State>({ id, spec, onExit }: Props<State>) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [round, setRound] = useState(0)
  const [result, setResult] = useState<{ score: number; record: number; isNew: boolean } | null>(null)

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
      context.font = '20px monospace'
      context.textBaseline = 'top'
      context.fillStyle = '#fff'
      context.textAlign = 'left'
      context.fillText(`Puntos ${spec.score(state)}`, 12, 10)
      context.textAlign = 'right'
      context.fillText(`${Math.max(0, Math.ceil(spec.seconds - gameTime))} s`, spec.width - 12, 10)
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
        pointer.taps.length = 0
      }
      spec.draw(context, state, images, gameTime)
      drawHud()
      if (countdown > 0) {
        context.font = '96px monospace'
        context.textAlign = 'center'
        context.textBaseline = 'middle'
        context.fillStyle = '#ffd84d'
        context.fillText(String(Math.ceil(countdown)), spec.width / 2, spec.height / 2)
      }
      if (gameTime >= spec.seconds) {
        const score = spec.score(state)
        const previous = loadRecord(id)
        const isNew = score > previous
        if (isNew) saveRecord(id, score)
        setResult({ score, record: Math.max(score, previous), isNew })
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
  }, [id, spec, round])

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
            <h2 className="minigame__score">{result.score} puntos</h2>
            <p className="minigame__record">{result.isNew ? '¡Récord nuevo!' : `Récord: ${result.record}`}</p>
            <button className="btn" onClick={playAgain}>
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
