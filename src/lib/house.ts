export const ROOM_WIDTH = 640
export const ROOM_HEIGHT = 360
export const WALL_HEIGHT = 148

export const ITEM_KINDS = [
  'bed', 'bowl', 'ball', 'door', 'rug', 'plant',
  'bookshelf', 'clock', 'wallshelf', 'toybox', 'armchair', 'sidetable', 'pouf',
] as const
export type ItemKind = (typeof ITEM_KINDS)[number]

export type Task = 'feed' | 'play' | 'sleep' | 'send'
type Zone = 'floor' | 'wall' | 'door'

interface ItemDef {
  task: Task | null
  spot?: { dx: number; dy: number }
  flat?: boolean
  zone: Zone
}

export const ITEM_DEFS: Record<ItemKind, ItemDef> = {
  rug: { task: null, flat: true, zone: 'floor' },
  clock: { task: null, zone: 'wall' },
  wallshelf: { task: null, zone: 'wall' },
  bookshelf: { task: null, zone: 'floor' },
  sidetable: { task: null, zone: 'floor' },
  pouf: { task: null, zone: 'floor' },
  armchair: { task: null, zone: 'floor' },
  toybox: { task: null, zone: 'floor' },
  plant: { task: null, zone: 'floor' },
  bed: { task: 'sleep', spot: { dx: 0, dy: 18 }, zone: 'floor' },
  bowl: { task: 'feed', spot: { dx: 0, dy: 16 }, zone: 'floor' },
  ball: { task: 'play', spot: { dx: 0, dy: 10 }, zone: 'floor' },
  door: { task: 'send', spot: { dx: 0, dy: 30 }, zone: 'door' },
}

export interface HouseItem {
  id: string
  house_id: string
  kind: ItemKind
  x: number
  y: number
}

const EDGE_MARGIN = 24
const WALL_TOP = 60
const FLOOR_TOP = WALL_HEIGHT + 10
const DOOR_BASE_Y = WALL_HEIGHT + 8

export function clampPosition(kind: ItemKind, x: number, y: number) {
  const clampedX = Math.round(Math.min(ROOM_WIDTH - EDGE_MARGIN, Math.max(EDGE_MARGIN, x)))
  const { zone } = ITEM_DEFS[kind]
  if (zone === 'door') return { x: clampedX, y: DOOR_BASE_Y }
  const [top, bottom] = zone === 'wall' ? [WALL_TOP, WALL_HEIGHT - 4] : [FLOOR_TOP, ROOM_HEIGHT - 4]
  return { x: clampedX, y: Math.round(Math.min(bottom, Math.max(top, y))) }
}
