import { useEffect, useRef } from 'react'
import type { Action, Stats } from '../hooks/useNailong'
import { asset } from '../lib/asset'
import { WINDOW_NAMES, type WindowName } from '../lib/weather'
const WIDTH = 640
const HEIGHT = 360
const MOBILE_VIEW_WIDTH = 360
const MOBILE_QUERY = '(max-width: 767px)'
const CAMERA_FOLLOW_SPEED = 4
const WALL_HEIGHT = 148
const BACKGROUND_URL = asset('rooms/room_a.png')
const WINDOW_POSITION = { x: 32, y: 22 }
const SPEED = 80
const EAT_URL = asset('sprites/processed/eat.png')
const EAT_FRAMES = 8
const SLEEP_URL = asset('sprites/processed/sleep.png')
const SLEEP_FRAMES = 8
const SLEEP_INSET = 16
const SPRITE_SCALE = 2
const IDLE_URL = asset('sprites/processed/idle.png')
const IDLE_SEQUENCE = [0, 1, 0, 1, 0, 2, 0, 1, 0, 3]
const IDLE_FRAME_MS = 600
const WAVE_FRAME = 3
const WALK_URL = asset('sprites/processed/walk_side_v2.png')
const WALK_FRONT_URL = asset('sprites/processed/walk_front.png')
const WALK_BACK_URL = asset('sprites/processed/walk_back.png')
const WALK_FRAMES = 4
const WALK_FRAME_MS = 140
const SOURCE_CELL = 64
const SPRITE_SIZE = 128

type Task = Action | 'send'

const ACTION_DURATION: Record<Task, number> = { feed: 1800, play: 1800, sleep: 5000, send: 1800 }

const OBJECT_NAMES = [
  'bed', 'bowl', 'ball', 'door', 'rug', 'plant',
  'bookshelf', 'clock', 'wallshelf', 'toybox', 'armchair', 'sidetable', 'pouf',
] as const
type ObjectName = (typeof OBJECT_NAMES)[number]
const OBJECT_SCALE = 2

interface Placement {
  name: ObjectName
  task: Task | null
  cx: number
  baseY: number
  spot?: { x: number; y: number }
  flat?: boolean
}

const PLACEMENTS: Placement[] = [
  { name: 'rug', task: null, cx: 360, baseY: 300, flat: true },
  { name: 'clock', task: null, cx: 200, baseY: 86 },
  { name: 'wallshelf', task: null, cx: 385, baseY: 100 },
  { name: 'bookshelf', task: null, cx: 480, baseY: 168 },
  { name: 'sidetable', task: null, cx: 200, baseY: 190 },
  { name: 'pouf', task: null, cx: 470, baseY: 270 },
  { name: 'armchair', task: null, cx: 585, baseY: 305 },
  { name: 'toybox', task: null, cx: 200, baseY: 336 },
  { name: 'plant', task: null, cx: 44, baseY: 340 },
  { name: 'bed', task: 'sleep', cx: 100, baseY: 236, spot: { x: 100, y: 254 } },
  { name: 'bowl', task: 'feed', cx: 500, baseY: 330, spot: { x: 500, y: 346 } },
  { name: 'ball', task: 'play', cx: 300, baseY: 344, spot: { x: 300, y: 354 } },
  { name: 'door', task: 'send', cx: 582, baseY: WALL_HEIGHT + 8, spot: { x: 582, y: 186 } },
]

interface Props {
  stats: Stats
  canSend: boolean
  windowName: WindowName
  onAction: (action: Action) => void
  onSend: () => void
}

interface Walker {
  x: number
  y: number
  facing: 1 | -1
  heading: 'front' | 'back' | 'side'
  target: { x: number; y: number } | null
  task: Task | null
  busyUntil: number
  busyTask: Task | null
  nextWanderAt: number
}

function moodOf(stats: Stats): 'weak' | 'sad' | 'hungry' | 'sleepy' | 'happy' | 'idle' {
  const lowest = Math.min(stats.satiety, stats.happiness, stats.energy)
  if (lowest < 10) return 'weak'
  if (stats.happiness < 30) return 'sad'
  if (stats.satiety < 30) return 'hungry'
  if (stats.energy < 30) return 'sleepy'
  if (lowest > 70) return 'happy'
  return 'idle'
}

export function Room({ stats, canSend, windowName, onAction, onSend }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const latest = useRef({ stats, canSend, windowName, onAction, onSend })
  latest.current = { stats, canSend, windowName, onAction, onSend }

  useEffect(() => {
    const canvas = canvasRef.current
    const context = canvas?.getContext('2d')
    if (!canvas || !context) return

    const sprite = new Image()
    sprite.src = IDLE_URL
    const walkSprite = new Image()
    walkSprite.src = WALK_URL
    const walkFrontSprite = new Image()
    walkFrontSprite.src = WALK_FRONT_URL
    const background = new Image()
    background.src = BACKGROUND_URL
    const windows = Object.fromEntries(
      WINDOW_NAMES.map((name) => {
        const image = new Image()
        image.src = asset(`rooms/windows/${name}.png`)
        return [name, image]
      }),
    ) as Record<WindowName, HTMLImageElement>
    const walkBackSprite = new Image()
    walkBackSprite.src = WALK_BACK_URL
    const eatSprite = new Image()
    eatSprite.src = EAT_URL
    const sleepSprite = new Image()
    sleepSprite.src = SLEEP_URL
    const objects = Object.fromEntries(
      OBJECT_NAMES.map((name) => {
        const image = new Image()
        image.src = asset(`rooms/objects/${name}.png`)
        return [name, image]
      }),
    ) as Record<ObjectName, HTMLImageElement>
    const sizeOf = (name: ObjectName) => ({
      width: objects[name].naturalWidth * OBJECT_SCALE,
      height: objects[name].naturalHeight * OBJECT_SCALE,
    })

    const walker: Walker = {
      x: 320,
      y: 260,
      facing: 1,
      heading: 'side',
      target: null,
      task: null,
      busyUntil: 0,
      busyTask: null,
      nextWanderAt: 0,
    }

    const mobileQuery = window.matchMedia(MOBILE_QUERY)
    let viewWidth = WIDTH
    let cameraX = 0
    const clampCamera = (x: number) => Math.min(WIDTH - viewWidth, Math.max(0, x - viewWidth / 2))
    const applyView = () => {
      viewWidth = mobileQuery.matches ? MOBILE_VIEW_WIDTH : WIDTH
      canvas.width = viewWidth
      canvas.height = HEIGHT
      canvas.style.aspectRatio = `${viewWidth} / ${HEIGHT}`
      cameraX = clampCamera(walker.x)
    }

    const handleClick = (event: MouseEvent) => {
      const rect = canvas.getBoundingClientRect()
      const clickX = ((event.clientX - rect.left) / rect.width) * viewWidth + cameraX
      const clickY = ((event.clientY - rect.top) / rect.height) * HEIGHT
      if (performance.now() < walker.busyUntil) return

      const hit = PLACEMENTS.find((item) => {
        if (!item.task) return false
        const { width, height } = sizeOf(item.name)
        return (
          clickX >= item.cx - width / 2 &&
          clickX <= item.cx + width / 2 &&
          clickY >= item.baseY - height &&
          clickY <= item.baseY
        )
      })
      if (hit?.spot) {
        walker.target = hit.spot
        walker.task = hit.task
      } else if (clickY > WALL_HEIGHT) {
        walker.target = { x: clickX, y: clickY }
        walker.task = null
      }
    }
    canvas.addEventListener('click', handleClick)
    applyView()
    mobileQuery.addEventListener('change', applyView)

    let lastFrame = performance.now()
    let animationId = 0

    const update = (time: number, delta: number) => {
      if (time < walker.busyUntil) return
      if (walker.busyTask) {
        const finished = walker.busyTask
        walker.busyTask = null
        if (finished === 'send') latest.current.onSend()
        else latest.current.onAction(finished)
      }

      if (!walker.target && time > walker.nextWanderAt) {
        walker.target = {
          x: 40 + Math.random() * (WIDTH - 80),
          y: WALL_HEIGHT + 40 + Math.random() * (HEIGHT - WALL_HEIGHT - 50),
        }
        walker.nextWanderAt = time + 2500 + Math.random() * 4000
      }

      if (!walker.target) return
      const dx = walker.target.x - walker.x
      const dy = walker.target.y - walker.y
      const distance = Math.hypot(dx, dy)
      const step = SPEED * delta
      if (distance <= step) {
        walker.x = walker.target.x
        walker.y = walker.target.y
        walker.target = null
        if (walker.task && (walker.task !== 'send' || latest.current.canSend)) {
          walker.busyTask = walker.task
          walker.busyUntil = time + ACTION_DURATION[walker.task]
        }
        walker.task = null
        return
      }
      walker.x += (dx / distance) * step
      walker.y += (dy / distance) * step
      if (Math.abs(dx) > 1) walker.facing = dx > 0 ? 1 : -1
      walker.heading = Math.abs(dy) > Math.abs(dx) ? (dy > 0 ? 'front' : 'back') : 'side'
    }

    const drawNailong = (time: number) => {
      const busy = time < walker.busyUntil ? walker.busyTask : null
      const walking = walker.target !== null
      const mood = moodOf(latest.current.stats)
      const hop = busy === 'play' ? Math.abs(Math.sin(time / 150)) * 12 : 0
      const directional = walker.heading === 'front' ? walkFrontSprite : walker.heading === 'back' ? walkBackSprite : walkSprite
      const walkSheet = directional.naturalWidth > 0 ? directional : walkSprite
      const useWalkFrames = walking && !busy && walkSheet.complete && walkSheet.naturalWidth > 0
      const bob = walking && !useWalkFrames ? Math.abs(Math.sin(time / 90)) * 6 : Math.sin(time / 400) * 1.5
      const baseX = Math.round(walker.x)
      const baseY = Math.round(walker.y - bob - hop)

      context.fillStyle = 'rgba(0,0,0,0.25)'
      context.beginPath()
      context.ellipse(baseX, walker.y - 2, 40, 9, 0, 0, Math.PI * 2)
      context.fill()

      const eating = busy === 'feed' && eatSprite.complete && eatSprite.naturalWidth > 0
      const eatWidth = eatSprite.naturalWidth / EAT_FRAMES
      const spriteTop = eating ? eatSprite.naturalHeight * SPRITE_SCALE : SPRITE_SIZE

      if (eating || useWalkFrames || (sprite.complete && sprite.naturalWidth > 0)) {
        context.save()
        context.translate(baseX, baseY)
        context.scale(eating || (useWalkFrames && walkSheet !== walkSprite) ? 1 : walker.facing, 1)
        if (busy === 'sleep') context.rotate(-0.15 * walker.facing)
        context.globalAlpha = busy === 'sleep' ? 0.75 : 1
        context.filter = mood === 'weak' || mood === 'sad' ? 'saturate(0.45)' : 'none'
        if (eating) {
          const progress = 1 - (walker.busyUntil - time) / ACTION_DURATION.feed
          const frame = Math.min(EAT_FRAMES - 1, Math.max(0, Math.floor(progress * EAT_FRAMES)))
          context.drawImage(
            eatSprite,
            frame * eatWidth, 0, eatWidth, eatSprite.naturalHeight,
            -(eatWidth * SPRITE_SCALE) / 2, -spriteTop, eatWidth * SPRITE_SCALE, spriteTop,
          )
        } else if (useWalkFrames) {
          const frame = Math.floor(time / WALK_FRAME_MS) % WALK_FRAMES
          context.drawImage(
            walkSheet,
            frame * SOURCE_CELL, 0, SOURCE_CELL, SOURCE_CELL,
            -SPRITE_SIZE / 2, -SPRITE_SIZE, SPRITE_SIZE, SPRITE_SIZE,
          )
        } else {
          const idleFrame =
            busy === 'send'
              ? WAVE_FRAME
              : IDLE_SEQUENCE[Math.floor(time / IDLE_FRAME_MS) % IDLE_SEQUENCE.length]
          context.drawImage(
            sprite,
            idleFrame * SOURCE_CELL, 0, SOURCE_CELL, SOURCE_CELL,
            -SPRITE_SIZE / 2, -SPRITE_SIZE, SPRITE_SIZE, SPRITE_SIZE,
          )
        }
        context.restore()
      }

      context.fillStyle = '#fff'
      context.font = '24px monospace'
      const bubble = busy === 'feed' ? 'ñam' : busy === 'sleep' ? 'zzz' : busy === 'play' ? '♪' : busy === 'send' ? 'adiós' : ''
      if (bubble) context.fillText(bubble, baseX - 16, baseY - spriteTop - 4)
    }

    const bed = PLACEMENTS.find((item) => item.name === 'bed')!

    const isSleepingOnBed = (time: number) =>
      time < walker.busyUntil && walker.busyTask === 'sleep' && sleepSprite.complete && sleepSprite.naturalWidth > 0

    const drawSleeper = (time: number) => {
      const frameWidth = sleepSprite.naturalWidth / SLEEP_FRAMES
      const progress = 1 - (walker.busyUntil - time) / ACTION_DURATION.sleep
      const frame = Math.min(SLEEP_FRAMES - 1, Math.max(0, Math.floor(progress * SLEEP_FRAMES)))
      const width = frameWidth * SPRITE_SCALE
      const height = sleepSprite.naturalHeight * SPRITE_SCALE
      const top = bed.baseY - SLEEP_INSET - height
      context.drawImage(
        sleepSprite,
        frame * frameWidth, 0, frameWidth, sleepSprite.naturalHeight,
        bed.cx - width / 2, top, width, height,
      )

      context.fillStyle = '#fff'
      for (let letter = 0; letter < 3; letter += 1) {
        const rise = (time / 1400 + letter / 3) % 1
        context.globalAlpha = 1 - rise
        context.font = `${16 + letter * 4}px monospace`
        context.fillText('z', bed.cx + 26 + letter * 14, top + 24 - rise * 44)
      }
      context.globalAlpha = 1
    }

    const draw = (time: number) => {
      context.imageSmoothingEnabled = false
      context.clearRect(0, 0, viewWidth, HEIGHT)
      context.save()
      context.translate(-Math.round(cameraX), 0)
      if (background.complete && background.naturalWidth > 0) {
        context.drawImage(background, 0, 0, WIDTH, HEIGHT)
      }
      const windowSprite = windows[latest.current.windowName]
      if (windowSprite.complete && windowSprite.naturalWidth > 0) {
        context.drawImage(
          windowSprite,
          WINDOW_POSITION.x, WINDOW_POSITION.y,
          windowSprite.naturalWidth * 2, windowSprite.naturalHeight * 2,
        )
      }

      const drawables = [
        ...PLACEMENTS.map((item) => ({
          depth: item.flat ? -1 : item.baseY,
          draw: () => {
            const image = objects[item.name]
            if (!image.complete || image.naturalWidth === 0) return
            const { width, height } = sizeOf(item.name)
            context.save()
            if (item.task === 'send' && !latest.current.canSend) context.filter = 'brightness(0.55)'
            context.drawImage(image, item.cx - width / 2, item.baseY - height, width, height)
            context.restore()
          },
        })),
        isSleepingOnBed(time)
          ? { depth: bed.baseY + 1, draw: () => drawSleeper(time) }
          : { depth: walker.y, draw: () => drawNailong(time) },
      ].sort((first, second) => first.depth - second.depth)
      drawables.forEach((drawable) => drawable.draw())
      context.restore()
    }

    const loop = (time: number) => {
      const delta = Math.min(0.05, (time - lastFrame) / 1000)
      lastFrame = time
      update(time, delta)
      cameraX += (clampCamera(walker.x) - cameraX) * Math.min(1, delta * CAMERA_FOLLOW_SPEED)
      draw(time)
      animationId = requestAnimationFrame(loop)
    }
    animationId = requestAnimationFrame(loop)

    return () => {
      cancelAnimationFrame(animationId)
      canvas.removeEventListener('click', handleClick)
      mobileQuery.removeEventListener('change', applyView)
    }
  }, [])

  return <canvas ref={canvasRef} width={WIDTH} height={HEIGHT} className="room" />
}
