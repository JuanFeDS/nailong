export const ROOM_WIDTH = 640
export const ROOM_HEIGHT = 360

export type Place = 'room' | 'patio'
export const PLACE_WIDTH: Record<Place, number> = { room: 640, patio: 952 }
export const WALL_HEIGHT: Record<Place, number> = { room: 148, patio: 172 }

export const ITEM_KINDS = [
  'bed', 'bowl', 'ball', 'door', 'rug', 'plant',
  'bookshelf', 'clock', 'wallshelf', 'toybox', 'armchair', 'sidetable', 'pouf', 'frame',
  'lamp', 'fishtank', 'desk', 'guitar', 'cactus', 'wardrobe', 'poster', 'mirror',
  'backdoor', 'gate', 'swing', 'goal', 'soccerball', 'plot_empty', 'plot_sprout', 'plot_growing', 'plot_ripe', 'plot_wilted',
] as const
export type ItemKind = (typeof ITEM_KINDS)[number]

export type Task = 'feed' | 'play' | 'sleep' | 'send' | 'patio' | 'room' | 'water' | 'swing' | 'soccer'
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
  frame: { task: null, zone: 'wall' },
  poster: { task: null, zone: 'wall' },
  mirror: { task: null, zone: 'wall' },
  lamp: { task: null, zone: 'floor' },
  fishtank: { task: null, zone: 'floor' },
  desk: { task: null, zone: 'floor' },
  guitar: { task: null, zone: 'floor' },
  cactus: { task: null, zone: 'floor' },
  wardrobe: { task: null, zone: 'floor' },
  backdoor: { task: 'patio', spot: { dx: 0, dy: 30 }, zone: 'door' },
  gate: { task: 'room', spot: { dx: 0, dy: 22 }, zone: 'door' },
  swing: { task: 'swing', spot: { dx: 0, dy: 14 }, zone: 'floor' },
  goal: { task: null, zone: 'floor' },
  soccerball: { task: 'soccer', spot: { dx: -80, dy: 0 }, zone: 'floor' },
  plot_empty: { task: null, zone: 'floor' },
  plot_sprout: { task: null, zone: 'floor' },
  plot_growing: { task: null, zone: 'floor' },
  plot_ripe: { task: null, zone: 'floor' },
  plot_wilted: { task: null, zone: 'floor' },
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

export const ITEM_LABELS: Partial<Record<ItemKind, string>> = {
  lamp: 'Lámpara de pie',
  desk: 'Escritorio',
  fishtank: 'Pecera',
  wardrobe: 'Armario',
}

export const WALLS = [
  { id: 'blue', label: 'Azul' },
  { id: 'green', label: 'Verde' },
  { id: 'rose', label: 'Rosa' },
  { id: 'cream', label: 'Crema' },
  { id: 'gray', label: 'Gris' },
] as const
export const FLOORS = [
  { id: 'wood', label: 'Madera' },
  { id: 'dark', label: 'Oscuro' },
  { id: 'light', label: 'Claro' },
  { id: 'gray', label: 'Gris' },
] as const
export type WallId = (typeof WALLS)[number]['id']
export type FloorId = (typeof FLOORS)[number]['id']

export interface HouseStyle {
  wall: WallId
  floor: FloorId
}

export const DEFAULT_STYLE: HouseStyle = { wall: 'blue', floor: 'wood' }

export interface HouseItem {
  id: string
  house_id: string
  kind: ItemKind
  place: Place
  x: number
  y: number
}

const EDGE_MARGIN = 24
const WALL_TOP = 60

export function clampPosition(kind: ItemKind, place: Place, x: number, y: number) {
  const horizon = WALL_HEIGHT[place]
  const clampedX = Math.round(Math.min(PLACE_WIDTH[place] - EDGE_MARGIN, Math.max(EDGE_MARGIN, x)))
  const { zone } = ITEM_DEFS[kind]
  if (zone === 'door') return { x: clampedX, y: horizon + 8 }
  const [top, bottom] = zone === 'wall' ? [WALL_TOP, horizon - 4] : [horizon + 10, ROOM_HEIGHT - 4]
  return { x: clampedX, y: Math.round(Math.min(bottom, Math.max(top, y))) }
}
