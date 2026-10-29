import { useEffect, useRef } from 'react'
import type { Plot } from '../hooks/useGarden'
import type { Action, Stats } from '../hooks/useNailong'
import { asset } from '../lib/asset'
import {
  clampPosition,
  FLOORS,
  type HouseItem,
  type HouseStyle,
  ITEM_DEFS,
  ITEM_KINDS,
  PLACE_WIDTH,
  type ItemKind,
  type Place,
  ROOM_HEIGHT as HEIGHT,
  ROOM_WIDTH as WIDTH,
  type Task,
  WALL_HEIGHT,
  WALLS,
} from '../lib/house'
import nailongSprites from '../lib/nailongSprites.json'
import { WINDOW_NAMES, type WindowName } from '../lib/weather'
const MOBILE_VIEW_WIDTH = 360
const MOBILE_QUERY = '(max-width: 767px)'
const CAMERA_FOLLOW_SPEED = 4
const MANUAL_PAN_MS = 6000
const PAN_STEP = 150
const EDGE_ZONE = 32
const DRAG_THRESHOLD = 8
const ARROW_TOP = 170
const ARROW_HEIGHT = 90
const WINDOW_POSITION = { x: 32, y: 22 }
const SPEED = 80
const EAT_URL = asset('sprites/processed/eat.png')
const PLAY_URL = asset('sprites/processed/play.png')
const ACTION_FRAMES = 8
const SLEEP_URL = asset('sprites/processed/sleep.png')
const SLEEP_FRAMES = 8
const SLEEP_INSET = 16
const SLEEP_INSET_3D = 4
const SLEEP_SHIFT_3D = -18
const NIGHT_LOOP_MS = 6000
const NIGHT_TINT = 'rgba(10, 8, 40, 0.38)'
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

const ACTION_DURATION: Record<Task, number> = {
  feed: 1800, play: 1800, sleep: 5000, send: 1800, patio: 700, room: 700, water: 2200, swing: 4800, soccer: 4400,
}
const SOCCER_URL = asset('sprites/processed/soccer.png')
const KICK_PROGRESS = 0.52
const FLIGHT_PROGRESS = 0.2
const FLIGHT_ARC = 70
const SWING_URL = asset('sprites/processed/swing_anim.png')
const SWING_FRAMES = 7
const SWING_CYCLES = 2
const WATER_URL = asset('sprites/processed/water.png')
const WATER_SIDE_OFFSET = 78
// En la sala 3D Nailong también usa las hojas generadas desde el modelo 3D
// (tools/modelo/exportar.py); el índice dice cuántos cuadros trae cada una.
type SheetName = keyof typeof nailongSprites
const WATER_SIDE_OFFSET_3D = 92
const SOCCER_FRAMES = 8
const PATIO_URL = asset('rooms/patio.png')
const PLOT_SPOTS = [
  { slot: 0, x: 400, y: 338 },
  { slot: 1, x: 520, y: 338 },
  { slot: 2, x: 640, y: 338 },
]

const OBJECT_SCALE = 2
const SWING_SCALE = 2.6
const scaleOf = (name: ItemKind) => (name === 'swing' ? SWING_SCALE : OBJECT_SCALE)
// Muebles de la sala que tienen versión renderizada desde el modelo 3D.
const OBJECTS_3D = new Set<ItemKind>([
  'rug', 'clock', 'wallshelf', 'bookshelf', 'sidetable', 'pouf', 'armchair', 'toybox',
  'frame', 'plant', 'bed', 'bowl', 'ball', 'door', 'backdoor',
])
const BACKDROP_3D = asset('rooms/fondo_sala3d.png')
const EDIT_OUTLINE = 'rgba(255, 216, 77, 0.55)'
const EDIT_OUTLINE_ACTIVE = '#ffd84d'

interface Placement {
  id: string
  name: ItemKind
  task: Task | null
  cx: number
  baseY: number
  spot?: { x: number; y: number }
  flat?: boolean
}

interface Props {
  sala3d?: boolean
  costume?: string | null
  items: HouseItem[]
  waterTrigger: { id: number; slot: number } | null
  onWaterDone: (slot: number) => void
  plots: Plot[]
  onPlotTap: (slot: number) => void
  onFeedRequest: () => void
  feedTrigger: number
  place: Place
  onTravel: (place: Place) => void
  style: HouseStyle
  editing: boolean
  onMoveItem: (itemId: string, x: number, y: number) => void
  stats: Stats
  canSend: boolean
  windowName: WindowName
  sleeping: boolean
  onBlockedTap: () => void
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
  plotSlot: number
}

const IDLE_BY_MOOD: Record<ReturnType<typeof moodOf>, SheetName> = {
  happy: 'idle_happy', idle: 'idle_happy', hungry: 'idle_hungry', sleepy: 'idle_sleepy', sad: 'idle_sad', weak: 'idle_sad',
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

export function Room({
  sala3d = false, costume = null, items, waterTrigger, onWaterDone, plots, onPlotTap, onFeedRequest, feedTrigger, place, onTravel, style, editing, onMoveItem, stats, canSend, windowName, sleeping, onBlockedTap, onAction, onSend,
}: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const latest = useRef({ sala3d, costume, items, waterTrigger, onWaterDone, plots, onPlotTap, onFeedRequest, feedTrigger, place, onTravel, style, editing, onMoveItem, stats, canSend, windowName, sleeping, onBlockedTap, onAction, onSend })
  latest.current = { sala3d, costume, items, waterTrigger, onWaterDone, plots, onPlotTap, onFeedRequest, feedTrigger, place, onTravel, style, editing, onMoveItem, stats, canSend, windowName, sleeping, onBlockedTap, onAction, onSend }

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
    const loadImages = <Id extends string>(ids: readonly { id: Id }[], folder: string) =>
      Object.fromEntries(
        ids.map(({ id }) => {
          const image = new Image()
          image.src = asset(`rooms/${folder}/${id}.png`)
          return [id, image]
        }),
      ) as Record<Id, HTMLImageElement>
    const backdropImage = new Image()
    if (latest.current.sala3d) backdropImage.src = BACKDROP_3D
    const patioImage = new Image()
    patioImage.src = PATIO_URL
    const horizon = () => WALL_HEIGHT[latest.current.place]
    const roomWidth = () => PLACE_WIDTH[latest.current.place]
    const wallImages = loadImages(WALLS, 'walls')
    const floorImages = loadImages(FLOORS, 'floors')
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
    const playSprite = new Image()
    playSprite.src = PLAY_URL
    const soccerSprite = new Image()
    soccerSprite.src = SOCCER_URL
    const swingSprite = new Image()
    swingSprite.src = SWING_URL
    const waterSprite = new Image()
    waterSprite.src = WATER_URL
    const sleepSprite = new Image()
    sleepSprite.src = SLEEP_URL
    const objects = Object.fromEntries(
      ITEM_KINDS.map((name) => {
        const image = new Image()
        image.src = asset(`rooms/${latest.current.sala3d && OBJECTS_3D.has(name) ? 'objects3d' : 'objects'}/${name}.png`)
        return [name, image]
      }),
    ) as Record<ItemKind, HTMLImageElement>
    // Los muebles 3D ya vienen a la resolución del juego; los 2D se dibujan al doble.
    const drawScale = (name: ItemKind) => (latest.current.sala3d && OBJECTS_3D.has(name) ? 1 : scaleOf(name))
    const sizeOf = (name: ItemKind) => ({
      width: objects[name].naturalWidth * drawScale(name),
      height: objects[name].naturalHeight * drawScale(name),
    })

    let carried: { id: string; x: number; y: number } | null = null
    const placements = (): Placement[] =>
      latest.current.items.map((item) => {
        const { task, spot, flat } = ITEM_DEFS[item.kind]
        const x = carried?.id === item.id ? carried.x : item.x
        const y = carried?.id === item.id ? carried.y : item.y
        return {
          id: item.id,
          name: item.kind,
          task,
          cx: x,
          baseY: y,
          spot: spot ? { x: x + spot.dx, y: y + spot.dy } : undefined,
          flat,
        }
      })
    const plotImageOf = (slot: number) => {
      const stage = latest.current.plots.find((plot) => plot.slot === slot)?.stage ?? 'empty'
      return objects[`plot_${stage}` as ItemKind]
    }
    const plotBoxes = () =>
      PLOT_SPOTS.filter((spot) => latest.current.plots.some((plot) => plot.slot === spot.slot && plot.unlocked)).map((spot) => {
        const image = plotImageOf(spot.slot)
        const width = image.naturalWidth * OBJECT_SCALE
        const height = image.naturalHeight * OBJECT_SCALE
        return { slot: spot.slot, left: spot.x - width / 2, right: spot.x + width / 2, top: spot.y - height, bottom: spot.y, image, width, height, x: spot.x, y: spot.y }
      })
    const covers = (item: Placement, pointX: number, pointY: number) => {
      const { width, height } = sizeOf(item.name)
      return (
        pointX >= item.cx - width / 2 &&
        pointX <= item.cx + width / 2 &&
        pointY >= item.baseY - height &&
        pointY <= item.baseY
      )
    }

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
      plotSlot: 0,
    }

    const mobileQuery = window.matchMedia(MOBILE_QUERY)
    let viewWidth = Math.min(roomWidth(), WIDTH)
    let cameraX = 0
    const clampCamera = (x: number) => Math.min(roomWidth() - viewWidth, Math.max(0, x - viewWidth / 2))
    const applyView = () => {
      viewWidth = mobileQuery.matches ? MOBILE_VIEW_WIDTH : Math.min(roomWidth(), WIDTH)
      canvas.width = viewWidth
      canvas.height = HEIGHT
      canvas.style.aspectRatio = `${viewWidth} / ${HEIGHT}`
      cameraX = clampCamera(walker.x)
    }

    let manualUntil = 0
    const maxCamera = () => roomWidth() - viewWidth
    const panTo = (x: number) => {
      cameraX = Math.min(maxCamera(), Math.max(0, x))
      manualUntil = performance.now() + MANUAL_PAN_MS
    }

    let pointerActive = false
    let dragging = false
    let suppressClick = false
    let dragStartX = 0
    let dragStartCamera = 0
    let grab = { x: 0, y: 0 }

    const toWorld = (event: PointerEvent | MouseEvent) => {
      const rect = canvas.getBoundingClientRect()
      return {
        x: ((event.clientX - rect.left) / rect.width) * viewWidth + cameraX,
        y: ((event.clientY - rect.top) / rect.height) * HEIGHT,
      }
    }
    const itemAt = (pointX: number, pointY: number) =>
      placements()
        .sort((first, second) => (second.flat ? -1 : second.baseY) - (first.flat ? -1 : first.baseY))
        .find((item) => covers(item, pointX, pointY))

    const handlePointerDown = (event: PointerEvent) => {
      if (latest.current.editing) {
        const point = toWorld(event)
        const item = itemAt(point.x, point.y)
        if (item) {
          carried = { id: item.id, x: item.cx, y: item.baseY }
          grab = { x: point.x - item.cx, y: point.y - item.baseY }
          canvas.setPointerCapture(event.pointerId)
          return
        }
      }
      pointerActive = true
      dragging = false
      dragStartX = event.clientX
      dragStartCamera = cameraX
    }
    const handlePointerMove = (event: PointerEvent) => {
      if (carried) {
        const point = toWorld(event)
        const kind = latest.current.items.find((item) => item.id === carried?.id)?.kind
        if (kind) carried = { id: carried.id, ...clampPosition(kind, latest.current.place, point.x - grab.x, point.y - grab.y) }
        return
      }
      if (!pointerActive || viewWidth >= roomWidth()) return
      const deltaX = event.clientX - dragStartX
      if (!dragging && Math.abs(deltaX) > DRAG_THRESHOLD) dragging = true
      if (dragging) {
        const rect = canvas.getBoundingClientRect()
        panTo(dragStartCamera - (deltaX / rect.width) * viewWidth)
      }
    }
    const handlePointerEnd = () => {
      if (carried) {
        latest.current.onMoveItem(carried.id, carried.x, carried.y)
        carried = null
        suppressClick = true
        window.setTimeout(() => {
          suppressClick = false
        }, 0)
      }
      pointerActive = false
      if (dragging) {
        suppressClick = true
        window.setTimeout(() => {
          suppressClick = false
        }, 0)
      }
      dragging = false
    }

    const handleClick = (event: MouseEvent) => {
      if (suppressClick) return
      const rect = canvas.getBoundingClientRect()
      const viewX = ((event.clientX - rect.left) / rect.width) * viewWidth
      if (viewWidth < roomWidth()) {
        if (viewX < EDGE_ZONE && cameraX > 1) {
          panTo(cameraX - PAN_STEP)
          return
        }
        if (viewX > viewWidth - EDGE_ZONE && cameraX < maxCamera() - 1) {
          panTo(cameraX + PAN_STEP)
          return
        }
      }
      if (latest.current.editing) return
      if (latest.current.sleeping) {
        latest.current.onBlockedTap()
        return
      }
      const clickX = viewX + cameraX
      const clickY = ((event.clientY - rect.top) / rect.height) * HEIGHT
      if (performance.now() < walker.busyUntil) return

      if (latest.current.place === 'patio') {
        const plotHit = plotBoxes().find((box) => clickX >= box.left && clickX <= box.right && clickY >= box.top && clickY <= box.bottom)
        if (plotHit) {
          latest.current.onPlotTap(plotHit.slot)
          return
        }
      }

      const hit = placements().find((item) => item.task && covers(item, clickX, clickY))
      if (hit?.task === 'feed') {
        latest.current.onFeedRequest()
        return
      }
      if (hit?.spot) {
        walker.target = hit.spot
        walker.task = hit.task
      } else if (clickY > horizon()) {
        walker.target = { x: clickX, y: clickY }
        walker.task = null
      }
    }
    canvas.addEventListener('click', handleClick)
    canvas.addEventListener('pointerdown', handlePointerDown)
    canvas.addEventListener('pointermove', handlePointerMove)
    canvas.addEventListener('pointerup', handlePointerEnd)
    canvas.addEventListener('pointercancel', handlePointerEnd)
    canvas.addEventListener('pointerleave', handlePointerEnd)
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
        else if (finished === 'water') latest.current.onWaterDone(walker.plotSlot)
        else if (finished === 'patio' || finished === 'room') latest.current.onTravel(finished)
        else latest.current.onAction(finished)
      }

      if (latest.current.sleeping) {
        walker.target = null
        walker.task = null
        return
      }

      if (!walker.target && time > walker.nextWanderAt) {
        walker.target = {
          x: 40 + Math.random() * (roomWidth() - 80),
          y: horizon() + 40 + Math.random() * (HEIGHT - horizon() - 50),
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
      const strip = busy === 'feed' ? eatSprite : busy === 'play' ? playSprite : busy === 'water' ? waterSprite : busy === 'soccer' ? soccerSprite : null
      const acting = strip !== null && strip.complete && strip.naturalWidth > 0
      const hop = busy === 'play' && !acting ? Math.abs(Math.sin(time / 150)) * 12 : 0
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

      const actionSheet = strip as HTMLImageElement
      const actionWidth = acting ? actionSheet.naturalWidth / ACTION_FRAMES : 0
      const spriteTop = acting ? actionSheet.naturalHeight * SPRITE_SCALE : SPRITE_SIZE

      if (acting || useWalkFrames || (sprite.complete && sprite.naturalWidth > 0)) {
        context.save()
        context.translate(baseX, baseY)
        context.scale(acting || (useWalkFrames && walkSheet !== walkSprite) ? 1 : walker.facing, 1)
        if (busy === 'sleep') context.rotate(-0.15 * walker.facing)
        context.globalAlpha = busy === 'sleep' ? 0.75 : 1
        context.filter = mood === 'weak' || mood === 'sad' ? 'saturate(0.45)' : 'none'
        if (acting) {
          const progress = 1 - (walker.busyUntil - time) / ACTION_DURATION[walker.busyTask as Task]
          const frame = Math.min(ACTION_FRAMES - 1, Math.max(0, Math.floor(progress * ACTION_FRAMES)))
          context.drawImage(
            actionSheet,
            frame * actionWidth, 0, actionWidth, actionSheet.naturalHeight,
            -(actionWidth * SPRITE_SCALE) / 2, -spriteTop, actionWidth * SPRITE_SCALE, spriteTop,
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

    const drawKickedBall = (ball: Placement, all: Placement[]) => {
      const image = objects.soccerball
      if (!image.complete || image.naturalWidth === 0) return
      const { width, height } = sizeOf('soccerball')
      const goal = all.find((item) => item.name === 'goal')
      const progress = 1 - (walker.busyUntil - performance.now()) / ACTION_DURATION.soccer
      const flight = Math.min(1, Math.max(0, (progress - KICK_PROGRESS) / FLIGHT_PROGRESS))
      const targetX = goal ? goal.cx : ball.cx
      const targetY = goal ? goal.baseY - 18 : ball.baseY
      const x = ball.cx + (targetX - ball.cx) * flight
      const y = ball.baseY + (targetY - ball.baseY) * flight - Math.sin(flight * Math.PI) * FLIGHT_ARC
      context.drawImage(image, x - width / 2, y - height, width, height)
    }
    const swingingNow = (time: number) => time < walker.busyUntil && walker.busyTask === 'swing'
    const drawSwing = (item: Placement) => {
      if (!swingSprite.complete || swingSprite.naturalWidth === 0) return
      const frameWidth = swingSprite.naturalWidth / SWING_FRAMES
      const progress = 1 - (walker.busyUntil - performance.now()) / ACTION_DURATION.swing
      const frame = Math.floor(Math.max(0, progress) * SWING_FRAMES * SWING_CYCLES) % SWING_FRAMES
      const width = frameWidth * SWING_SCALE
      const height = swingSprite.naturalHeight * SWING_SCALE
      context.drawImage(
        swingSprite,
        frame * frameWidth, 0, frameWidth, swingSprite.naturalHeight,
        item.cx - width / 2, item.baseY - height, width, height,
      )
    }

    const sheets = latest.current.sala3d
      ? (Object.fromEntries(
          (Object.keys(nailongSprites) as SheetName[]).map((name) => {
            const image = new Image()
            image.src = asset(nailongSprites[name].file)
            return [name, image]
          }),
        ) as Record<SheetName, HTMLImageElement>)
      : null
    const sleepFrames = sheets ? nailongSprites.sleep.frames : SLEEP_FRAMES
    const ready = (image: HTMLImageElement) => image.complete && image.naturalWidth > 0

    // El disfraz se carga la primera vez que se usa; mientras no llega, cada hoja cae a la de siempre.
    const costumeSheets = new Map<string, Record<SheetName, HTMLImageElement>>()
    const worn = (): Record<SheetName, HTMLImageElement> | null => {
      if (!sheets) return null
      const costume = latest.current.costume
      if (!costume) return sheets
      let own = costumeSheets.get(costume)
      if (!own) {
        own = Object.fromEntries(
          (Object.keys(nailongSprites) as SheetName[]).map((name) => {
            const image = new Image()
            image.src = asset(`sprites/nailong/${costume}/${name}.png`)
            return [name, image]
          }),
        ) as Record<SheetName, HTMLImageElement>
        costumeSheets.set(costume, own)
      }
      const mixed = {} as Record<SheetName, HTMLImageElement>
      for (const name of Object.keys(nailongSprites) as SheetName[]) mixed[name] = ready(own[name]) ? own[name] : sheets[name]
      return mixed
    }
    const sleepSheetNow = () => (sheets ? worn()!.sleep : sleepSprite)

    // Los renders del modelo 3D dejan unos píxeles vacíos bajo los pies; se mide cuántos
    // para apoyar el punto más bajo de cada hoja justo en el suelo.
    const footPads = new Map<string, number>()
    const footPadOf = (_name: string, image: HTMLImageElement) => {
      const key = image.src
      const cached = footPads.get(key)
      if (cached !== undefined) return cached
      const probe = document.createElement('canvas')
      probe.width = image.naturalWidth
      probe.height = image.naturalHeight
      const probeContext = probe.getContext('2d', { willReadFrequently: true })
      if (!probeContext) return 0
      probeContext.drawImage(image, 0, 0)
      const { data } = probeContext.getImageData(0, 0, probe.width, probe.height)
      let lowest = 0
      for (let row = probe.height - 1; row >= 0 && lowest === 0; row -= 1) {
        for (let column = 0; column < probe.width; column += 1) {
          if (data[(row * probe.width + column) * 4 + 3] > 0) {
            lowest = row + 1
            break
          }
        }
      }
      const pad = probe.height - lowest
      footPads.set(key, pad)
      return pad
    }

    const drawSoftShadow = (centerX: number, groundY: number, lift: number) => {
      const shrink = Math.max(0.55, 1 - lift / 70)
      context.fillStyle = 'rgba(52, 22, 14, 0.22)'
      context.beginPath()
      context.ellipse(centerX, groundY - 1, 34 * shrink, 8 * shrink, 0, 0, Math.PI * 2)
      context.fill()
      context.fillStyle = 'rgba(52, 22, 14, 0.28)'
      context.beginPath()
      context.ellipse(centerX, groundY - 1, 22 * shrink, 5 * shrink, 0, 0, Math.PI * 2)
      context.fill()
    }

    const drawNailong3d = (time: number, all: Record<SheetName, HTMLImageElement>) => {
      const busy = time < walker.busyUntil ? walker.busyTask : null
      const walking = walker.target !== null
      const mood = moodOf(latest.current.stats)
      const down = mood === 'sad' || mood === 'weak'
      const stripName: SheetName | null = busy === 'feed' ? 'eat' : busy === 'play' ? 'play' : busy === 'water' ? 'water' : null
      const strip = stripName ? all[stripName] : busy === 'soccer' ? soccerSprite : null
      const actionFrames = stripName ? nailongSprites[stripName].frames : SOCCER_FRAMES
      const acting = strip !== null && ready(strip)
      const hop = busy === 'play' && !acting ? Math.abs(Math.sin(time / 150)) * 12 : 0
      const walkName: SheetName = walker.heading === 'front' ? 'walk_front' : walker.heading === 'back' ? 'walk_back' : down ? 'walk_side_sad' : 'walk_side'
      const walkSheet = all[walkName]
      const sideWalk = walker.heading === 'side'
      const useWalkFrames = walking && !busy && ready(walkSheet)
      // Al enviar saluda con el cuadro de la mano en alto, que está en el quieto feliz.
      const idleName = busy === 'send' ? 'idle_happy' : IDLE_BY_MOOD[mood]
      const idleSheet = all[idleName]
      const bob = walking && !useWalkFrames ? Math.abs(Math.sin(time / 90)) * 6 : Math.sin(time / 400) * 1.5
      const baseX = Math.round(walker.x)
      const baseY = Math.round(walker.y - bob - hop)

      drawSoftShadow(baseX, walker.y, bob + hop)

      const actionSheet = strip as HTMLImageElement
      const actionWidth = acting ? actionSheet.naturalWidth / actionFrames : 0
      const spriteTop = acting ? actionSheet.naturalHeight * SPRITE_SCALE : SPRITE_SIZE
      const actionPad = acting && stripName ? footPadOf(stripName, actionSheet) * SPRITE_SCALE : 0
      const walkPad = useWalkFrames ? footPadOf(walkName, walkSheet) * (SPRITE_SIZE / SOURCE_CELL) : 0
      const idlePad = ready(idleSheet) ? footPadOf(idleName, idleSheet) * (SPRITE_SIZE / SOURCE_CELL) : 0

      if (acting || useWalkFrames || ready(idleSheet)) {
        context.save()
        context.translate(baseX, baseY)
        context.scale(acting || (useWalkFrames && !sideWalk) ? 1 : walker.facing, 1)
        if (busy === 'sleep') context.rotate(-0.15 * walker.facing)
        context.globalAlpha = busy === 'sleep' ? 0.75 : 1
        // La tristeza ya se ve en la cara y la postura; solo débil se destiñe.
        context.filter = mood === 'weak' ? 'saturate(0.45)' : 'none'
        if (acting) {
          const progress = 1 - (walker.busyUntil - time) / ACTION_DURATION[walker.busyTask as Task]
          const frame = Math.min(actionFrames - 1, Math.max(0, Math.floor(progress * actionFrames)))
          context.drawImage(
            actionSheet,
            frame * actionWidth, 0, actionWidth, actionSheet.naturalHeight,
            -(actionWidth * SPRITE_SCALE) / 2, -spriteTop + actionPad, actionWidth * SPRITE_SCALE, spriteTop,
          )
        } else if (useWalkFrames) {
          const { frames, frameMs } = nailongSprites[walkName]
          const frame = Math.floor(time / frameMs) % frames
          context.drawImage(
            walkSheet,
            frame * SOURCE_CELL, 0, SOURCE_CELL, SOURCE_CELL,
            -SPRITE_SIZE / 2, -SPRITE_SIZE + walkPad, SPRITE_SIZE, SPRITE_SIZE,
          )
        } else {
          const idleFrame =
            busy === 'send'
              ? WAVE_FRAME
              : IDLE_SEQUENCE[Math.floor(time / nailongSprites[idleName].frameMs) % IDLE_SEQUENCE.length]
          context.drawImage(
            idleSheet,
            idleFrame * SOURCE_CELL, 0, SOURCE_CELL, SOURCE_CELL,
            -SPRITE_SIZE / 2, -SPRITE_SIZE + idlePad, SPRITE_SIZE, SPRITE_SIZE,
          )
        }
        context.restore()
      }

      context.fillStyle = '#fff'
      context.font = '24px monospace'
      const bubble = busy === 'feed' ? 'ñam' : busy === 'sleep' ? 'zzz' : busy === 'play' ? '♪' : busy === 'send' ? 'adiós' : ''
      if (bubble) context.fillText(bubble, baseX - 16, baseY - spriteTop - 4)
    }

    const isSleepingOnBed = (time: number) =>
      ready(sleepSheetNow()) &&
      (latest.current.sleeping || (time < walker.busyUntil && walker.busyTask === 'sleep'))

    const drawSleeper = (time: number) => {
      const bed = placements().find((item) => item.name === 'bed')
      if (!bed) return
      const sleepSheet = sleepSheetNow()
      const frameWidth = sleepSheet.naturalWidth / sleepFrames
      const progress = latest.current.sleeping
        ? (time % NIGHT_LOOP_MS) / NIGHT_LOOP_MS
        : 1 - (walker.busyUntil - time) / ACTION_DURATION.sleep
      const frame = Math.min(sleepFrames - 1, Math.max(0, Math.floor(progress * sleepFrames)))
      const width = frameWidth * SPRITE_SCALE
      const height = sleepSheet.naturalHeight * SPRITE_SCALE
      const top = bed.baseY - (sheets ? SLEEP_INSET_3D : SLEEP_INSET) - height
      const left = bed.cx - width / 2 + (sheets ? SLEEP_SHIFT_3D : 0)
      context.drawImage(
        sleepSheet,
        frame * frameWidth, 0, frameWidth, sleepSheet.naturalHeight,
        left, top, width, height,
      )

      // En la cama 3D duerme acostado con la cabeza en la almohada, a la izquierda.
      const zzzX = sheets ? bed.cx - 40 : bed.cx + 26
      const zzzY = sheets ? top + 16 : top + 24
      context.fillStyle = '#fff'
      for (let letter = 0; letter < 3; letter += 1) {
        const rise = (time / 1400 + letter / 3) % 1
        context.globalAlpha = 1 - rise
        context.font = `${16 + letter * 4}px monospace`
        context.fillText('z', zzzX + letter * 14, zzzY - rise * 44)
      }
      context.globalAlpha = 1
    }

    const draw = (time: number) => {
      context.imageSmoothingEnabled = false
      context.clearRect(0, 0, viewWidth, HEIGHT)
      context.save()
      context.translate(-Math.round(cameraX), 0)
      const wallImage = wallImages[latest.current.style.wall]
      const floorImage = floorImages[latest.current.style.floor]
      const inPatio = latest.current.place === 'patio'
      if (latest.current.sala3d && !inPatio) {
        if (backdropImage.complete && backdropImage.naturalWidth > 0) context.drawImage(backdropImage, 0, 0, WIDTH, HEIGHT)
      } else if (inPatio) {
        if (patioImage.complete && patioImage.naturalWidth > 0) context.drawImage(patioImage, 0, 0, roomWidth(), HEIGHT)
      } else {
        if (wallImage.complete && wallImage.naturalWidth > 0) {
          context.drawImage(wallImage, 0, 0, WIDTH, WALL_HEIGHT.room)
        }
        if (floorImage.complete && floorImage.naturalWidth > 0) {
          context.drawImage(floorImage, 0, WALL_HEIGHT.room, WIDTH, HEIGHT - WALL_HEIGHT.room)
        }
      }
      const windowSprite = windows[latest.current.windowName]
      if (!inPatio && !latest.current.sala3d && windowSprite.complete && windowSprite.naturalWidth > 0) {
        context.drawImage(
          windowSprite,
          WINDOW_POSITION.x, WINDOW_POSITION.y,
          windowSprite.naturalWidth * 2, windowSprite.naturalHeight * 2,
        )
      }

      const current = placements()
      const bed = current.find((item) => item.name === 'bed')
      const gardenDrawables =
        latest.current.place === 'patio'
          ? plotBoxes().map((box) => ({
              depth: box.y,
              draw: () => {
                if (box.image.complete && box.image.naturalWidth > 0) {
                  context.drawImage(box.image, box.left, box.top, box.width, box.height)
                }
              },
            }))
          : []
      const drawables = [
        ...gardenDrawables,
        ...current.map((item) => ({
          depth: item.flat ? -1 : item.baseY,
          draw: () => {
            if (item.name === 'swing' && swingingNow(time)) {
              drawSwing(item)
              return
            }
            if (item.name === 'soccerball' && time < walker.busyUntil && walker.busyTask === 'soccer') {
              drawKickedBall(item, current)
              return
            }
            const image = objects[item.name]
            if (!image.complete || image.naturalWidth === 0) return
            const { width, height } = sizeOf(item.name)
            context.save()
            if (item.task === 'send' && !latest.current.canSend) context.filter = 'brightness(0.55)'
            context.drawImage(image, item.cx - width / 2, item.baseY - height, width, height)
            context.restore()
            if (latest.current.editing) {
              context.strokeStyle = carried?.id === item.id ? EDIT_OUTLINE_ACTIVE : EDIT_OUTLINE
              context.lineWidth = carried?.id === item.id ? 3 : 2
              context.setLineDash([6, 4])
              context.strokeRect(item.cx - width / 2, item.baseY - height, width, height)
              context.setLineDash([])
            }
          },
        })),
        bed && isSleepingOnBed(time)
          ? { depth: bed.baseY + 1, draw: () => drawSleeper(time) }
          : swingingNow(time)
            ? { depth: -2, draw: () => undefined }
            : { depth: walker.y, draw: () => (sheets ? drawNailong3d(time, worn()!) : drawNailong(time)) },
      ].sort((first, second) => first.depth - second.depth)
      drawables.forEach((drawable) => drawable.draw())
      context.restore()

      if (latest.current.sleeping) {
        context.fillStyle = NIGHT_TINT
        context.fillRect(0, 0, viewWidth, HEIGHT)
      }

      if (viewWidth < roomWidth()) {
        const arrows: [string, number, boolean][] = [
          ['‹', 0, cameraX > 1],
          ['›', viewWidth - EDGE_ZONE, cameraX < maxCamera() - 1],
        ]
        context.font = '36px monospace'
        context.textAlign = 'center'
        context.textBaseline = 'middle'
        for (const [glyph, left, visible] of arrows) {
          if (!visible) continue
          context.fillStyle = 'rgba(15, 8, 8, 0.45)'
          context.fillRect(left, ARROW_TOP, EDGE_ZONE, ARROW_HEIGHT)
          context.fillStyle = '#ffd84d'
          context.fillText(glyph, left + EDGE_ZONE / 2, ARROW_TOP + ARROW_HEIGHT / 2)
        }
        context.textAlign = 'start'
        context.textBaseline = 'alphabetic'
      }
    }

    let currentPlace = latest.current.place
    let lastFeedTrigger = latest.current.feedTrigger
    let lastWaterId = latest.current.waterTrigger?.id ?? 0
    const arriveAtDoor = () => {
      const door = placements().find((item) => item.name === (currentPlace === 'patio' ? 'gate' : 'backdoor'))
      walker.x = door?.spot?.x ?? 320
      walker.y = door?.spot?.y ?? horizon() + 60
      walker.target = null
      walker.task = null
      walker.busyUntil = 0
      walker.busyTask = null
      cameraX = clampCamera(walker.x)
    }

    const loop = (time: number) => {
      if (latest.current.place !== currentPlace) {
        currentPlace = latest.current.place
        applyView()
        arriveAtDoor()
      }
      const water = latest.current.waterTrigger
      if (water && water.id !== lastWaterId) {
        lastWaterId = water.id
        const box = plotBoxes().find((candidate) => candidate.slot === water.slot)
        if (box && time >= walker.busyUntil && !latest.current.sleeping) {
          walker.target = { x: box.x + (sheets ? WATER_SIDE_OFFSET_3D : WATER_SIDE_OFFSET), y: box.y - 8 }
          walker.task = 'water'
          walker.plotSlot = water.slot
        } else {
          latest.current.onWaterDone(water.slot)
        }
      }
      if (latest.current.feedTrigger !== lastFeedTrigger) {
        lastFeedTrigger = latest.current.feedTrigger
        const bowl = placements().find((item) => item.task === 'feed')
        if (bowl?.spot && time >= walker.busyUntil) {
          walker.target = bowl.spot
          walker.task = 'feed'
        }
      }
      canvas.style.touchAction = latest.current.editing ? 'none' : ''
      const delta = Math.min(0.05, (time - lastFrame) / 1000)
      lastFrame = time
      update(time, delta)
      if (performance.now() >= manualUntil) {
        cameraX += (clampCamera(walker.x) - cameraX) * Math.min(1, delta * CAMERA_FOLLOW_SPEED)
      }
      draw(time)
      animationId = requestAnimationFrame(loop)
    }
    animationId = requestAnimationFrame(loop)

    return () => {
      cancelAnimationFrame(animationId)
      canvas.removeEventListener('click', handleClick)
      canvas.removeEventListener('pointerdown', handlePointerDown)
      canvas.removeEventListener('pointermove', handlePointerMove)
      canvas.removeEventListener('pointerup', handlePointerEnd)
      canvas.removeEventListener('pointercancel', handlePointerEnd)
      canvas.removeEventListener('pointerleave', handlePointerEnd)
      mobileQuery.removeEventListener('change', applyView)
    }
  }, [])

  return <canvas ref={canvasRef} width={WIDTH} height={HEIGHT} className="room" />
}
