export const ROOM_WIDTH = 640
export const ROOM_HEIGHT = 360

export const ROOMS = ['bedroom', 'kitchen', 'bathroom', 'playroom'] as const
export type RoomName = (typeof ROOMS)[number]
export type Place = 'room' | 'patio' | RoomName
export const PLACES: Place[] = ['room', 'patio', ...ROOMS]
export const PLACE_WIDTH: Record<Place, number> = { room: 640, patio: 952, bedroom: 640, kitchen: 640, bathroom: 640, playroom: 640 }
export const WALL_HEIGHT: Record<Place, number> = { room: 148, patio: 172, bedroom: 148, kitchen: 148, bathroom: 148, playroom: 148 }
export const isPlace = (value: string): value is Place => (PLACES as string[]).includes(value)

export const ROOM_LABELS: Record<RoomName, string> = {
  bedroom: 'Dormitorio',
  kitchen: 'Cocina',
  bathroom: 'Baño',
  playroom: 'Cuarto de juegos',
}
export const ROOM_BLURBS: Record<RoomName, string> = {
  bedroom: 'Con cama para dormir y mesita de noche',
  kitchen: 'Con nevera para dar de comer y estufa',
  bathroom: 'Con tina y lavamanos',
  playroom: 'Con maquinita de minijuegos y tobogán',
}
// Paredes y pisos fijos de cada cuarto; la sala usa el estilo que elige el usuario.
export const ROOM_STYLES: Record<RoomName, { wall: WallId; floor: FloorId }> = {
  bedroom: { wall: 'rose', floor: 'wood' },
  kitchen: { wall: 'cream', floor: 'gray' },
  bathroom: { wall: 'blue', floor: 'light' },
  playroom: { wall: 'green', floor: 'light' },
}

export const ITEM_KINDS = [
  'bed', 'bowl', 'ball', 'door', 'rug', 'plant',
  'bookshelf', 'clock', 'wallshelf', 'toybox', 'armchair', 'sidetable', 'pouf', 'frame',
  'lamp', 'fishtank', 'desk', 'guitar', 'cactus', 'wardrobe', 'poster', 'mirror',
  'sofa', 'cushions', 'coffeetable', 'tv', 'bigplant', 'painting', 'hangingplant',
  'bench', 'flowerpots', 'birdbath', 'lamppost',
  'door_bedroom', 'door_kitchen', 'door_bathroom', 'door_playroom', 'exitdoor',
  'nightstand', 'fridge', 'stove', 'bathtub', 'sink', 'arcade', 'slide',
  'backdoor', 'gate', 'swing', 'goal', 'soccerball', 'plot_empty', 'plot_sprout', 'plot_growing', 'plot_ripe', 'plot_wilted',
] as const
export type ItemKind = (typeof ITEM_KINDS)[number]

export type Task = 'feed' | 'play' | 'sleep' | 'send' | 'water' | 'swing' | 'soccer' | 'minigames' | Place
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
  sofa: { task: null, zone: 'floor' },
  cushions: { task: null, zone: 'floor' },
  coffeetable: { task: null, zone: 'floor' },
  tv: { task: null, zone: 'floor' },
  bigplant: { task: null, zone: 'floor' },
  painting: { task: null, zone: 'wall' },
  hangingplant: { task: null, zone: 'wall' },
  bench: { task: null, zone: 'floor' },
  flowerpots: { task: null, zone: 'floor' },
  birdbath: { task: null, zone: 'floor' },
  lamppost: { task: null, zone: 'floor' },
  door_bedroom: { task: 'bedroom', spot: { dx: 0, dy: 30 }, zone: 'door' },
  door_kitchen: { task: 'kitchen', spot: { dx: 0, dy: 30 }, zone: 'door' },
  door_bathroom: { task: 'bathroom', spot: { dx: 0, dy: 30 }, zone: 'door' },
  door_playroom: { task: 'playroom', spot: { dx: 0, dy: 30 }, zone: 'door' },
  exitdoor: { task: 'room', spot: { dx: 0, dy: 30 }, zone: 'door' },
  nightstand: { task: null, zone: 'floor' },
  fridge: { task: 'feed', spot: { dx: 40, dy: 10 }, zone: 'floor' },
  stove: { task: null, zone: 'floor' },
  bathtub: { task: null, zone: 'floor' },
  sink: { task: null, zone: 'floor' },
  arcade: { task: 'minigames', spot: { dx: 0, dy: 16 }, zone: 'floor' },
  slide: { task: null, zone: 'floor' },
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
  sofa: 'Sofá',
  cushions: 'Cojines',
  coffeetable: 'Mesa de centro',
  tv: 'Televisor',
  bigplant: 'Planta grande',
  painting: 'Cuadro del mar',
  hangingplant: 'Planta colgante',
  bench: 'Banca',
  flowerpots: 'Macetas con flores',
  birdbath: 'Bebedero de pájaros',
  lamppost: 'Farol',
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
