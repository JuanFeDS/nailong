import type { Place } from './house'

export type DecorKind = 'floor' | 'top' | 'topRight' | 'float'

export interface Decor {
  sprite: string
  kind: DecorKind
  x: number
  y: number
  depth?: number
  bob?: number
  thread?: boolean
  action?: 'minigames'
  alpha?: number
  glow?: { radius: number; color?: string; flicker?: boolean }
}

const pumpkinGlow = (radius: number) => ({ radius })
const candleGlow = { radius: 30, flicker: true }
const brewGlow = { radius: 54, color: '110, 255, 70' }

export const HALLOWEEN_DECOR: Record<Place, Decor[]> = {
  room: [
    { sprite: 'lights', kind: 'top', x: 187, y: 4 },
    { sprite: 'web', kind: 'top', x: 2, y: 0 },
    { sprite: 'web', kind: 'topRight', x: 638, y: 0 },
    { sprite: 'bat', kind: 'top', x: 410, y: 44 },
    { sprite: 'bat', kind: 'top', x: 246, y: 30 },
    { sprite: 'pumpkin', kind: 'floor', x: 400, y: 352, glow: pumpkinGlow(70), action: 'minigames' },
    { sprite: 'pumpkin_m', kind: 'floor', x: 536, y: 348, glow: pumpkinGlow(54) },
    { sprite: 'pumpkin_s', kind: 'floor', x: 600, y: 354 },
    { sprite: 'cauldron', kind: 'floor', x: 258, y: 322, glow: brewGlow },
    { sprite: 'candles', kind: 'floor', x: 462, y: 332, glow: candleGlow },
    { sprite: 'skull', kind: 'floor', x: 342, y: 340 },
    { sprite: 'ghost', kind: 'float', x: 278, y: 128, bob: 5, alpha: 0.85 },
    { sprite: 'ghost', kind: 'float', x: 470, y: 120, bob: 4, alpha: 0.8 },
    { sprite: 'spider', kind: 'float', x: 524, y: 58, bob: 14, thread: true },
  ],
  patio: [
    { sprite: 'bat', kind: 'top', x: 140, y: 18 },
    { sprite: 'bat', kind: 'top', x: 430, y: 38 },
    { sprite: 'bat', kind: 'top', x: 770, y: 24 },
    { sprite: 'crow', kind: 'floor', x: 150, y: 90, depth: 40 },
    { sprite: 'crow', kind: 'floor', x: 700, y: 88, depth: 40 },
    { sprite: 'gravestone_a', kind: 'floor', x: 270, y: 222 },
    { sprite: 'gravestone_b', kind: 'floor', x: 326, y: 240 },
    { sprite: 'skull', kind: 'floor', x: 376, y: 258 },
    { sprite: 'pumpkin', kind: 'floor', x: 600, y: 236, glow: pumpkinGlow(70) },
    { sprite: 'pumpkin_m', kind: 'floor', x: 664, y: 226, glow: pumpkinGlow(54) },
    { sprite: 'pumpkin_s', kind: 'floor', x: 712, y: 238 },
    { sprite: 'pumpkin_m', kind: 'floor', x: 420, y: 232, glow: pumpkinGlow(54) },
    { sprite: 'cauldron', kind: 'floor', x: 520, y: 292, glow: brewGlow },
    { sprite: 'candles', kind: 'floor', x: 478, y: 302, glow: candleGlow },
    { sprite: 'deadtree', kind: 'floor', x: 900, y: 236 },
    { sprite: 'ghost', kind: 'float', x: 190, y: 150, bob: 6, alpha: 0.8 },
    { sprite: 'ghost', kind: 'float', x: 560, y: 160, bob: 5, alpha: 0.75 },
    { sprite: 'ghost', kind: 'float', x: 800, y: 140, bob: 6, alpha: 0.8 },
  ],
}

const STORAGE_KEY = 'nailong-halloween'

export function isHalloweenSeason(date: Date = new Date()): boolean {
  const month = date.getMonth()
  return (month === 9 && date.getDate() >= 20) || (month === 10 && date.getDate() <= 2)
}

export function loadHalloween(): boolean {
  try {
    return isHalloweenSeason() && localStorage.getItem(STORAGE_KEY) !== 'off'
  } catch {
    return isHalloweenSeason()
  }
}

export function saveHalloween(on: boolean) {
  try {
    if (on) localStorage.removeItem(STORAGE_KEY)
    else localStorage.setItem(STORAGE_KEY, 'off')
  } catch {
    // Sin almacenamiento el ajuste solo dura la sesión.
  }
}
