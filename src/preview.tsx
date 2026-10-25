import { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { Room } from './components/Room'
import { FLOORS, type FloorId, type HouseItem, type ItemKind, type Place, WALLS, type WallId } from './lib/house'
import { WINDOW_NAMES, type WindowName } from './lib/weather'
import './style.css'

const params = new URLSearchParams(location.search)
const requested = params.get('w') as WindowName | null
const windowName = requested && WINDOW_NAMES.includes(requested) ? requested : 'day'
const sleeping = params.get('sleep') === '1'
const editing = params.get('edit') === '1'
const wall = (WALLS.find((option) => option.id === params.get('wall'))?.id ?? 'blue') as WallId
const floor = (FLOORS.find((option) => option.id === params.get('floor'))?.id ?? 'wood') as FloorId
// ?mood=sad|hungry|sleepy|weak baja la estadística que provoca ese ánimo.
const MOOD_STATS: Record<string, { satiety: number; happiness: number; energy: number }> = {
  sad: { satiety: 80, happiness: 20, energy: 80 },
  hungry: { satiety: 20, happiness: 80, energy: 80 },
  sleepy: { satiety: 80, happiness: 80, energy: 20 },
  weak: { satiety: 5, happiness: 5, energy: 5 },
}
const stats = MOOD_STATS[params.get('mood') ?? ''] ?? { satiety: 80, happiness: 80, energy: 80 }

const DEFAULT_LAYOUT: [ItemKind, number, number][] = [
  ['rug', 360, 300], ['clock', 170, 86], ['wallshelf', 385, 100], ['bookshelf', 480, 168],
  ['sidetable', 330, 190], ['pouf', 470, 270], ['armchair', 585, 305], ['toybox', 200, 336],
  ['frame', 310, 84], ['plant', 44, 340], ['bed', 100, 236], ['bowl', 500, 330], ['ball', 300, 344], ['door', 582, 156], ['backdoor', 232, 156],
]

const PATIO_LAYOUT: [ItemKind, number, number][] = [
  ['gate', 476, 180], ['swing', 170, 285], ['goal', 830, 262], ['soccerball', 720, 322],
]

function Preview() {
  const [waterTrigger, setWaterTrigger] = useState<{ id: number; slot: number } | null>(null)
  useEffect(() => {
    if (!params.get('water')) return
    const timer = window.setTimeout(() => setWaterTrigger({ id: 1, slot: 0 }), 1500)
    return () => window.clearTimeout(timer)
  }, [])
  const [feedTrigger, setFeedTrigger] = useState(0)
  useEffect(() => {
    if (!params.get('feed')) return
    const timer = window.setTimeout(() => setFeedTrigger(1), 1500)
    return () => window.clearTimeout(timer)
  }, [])
  useEffect(() => {
    if (!params.get('kick')) return
    const timers: number[] = []
    const clickAt = (viewX: number, viewY: number) => {
      const canvas = document.querySelector('canvas')!
      const rect = canvas.getBoundingClientRect()
      canvas.dispatchEvent(
        new MouseEvent('click', {
          bubbles: true,
          clientX: rect.left + (viewX / canvas.width) * rect.width,
          clientY: rect.top + (viewY / 360) * rect.height,
        }),
      )
    }
    ;[600, 700, 800, 900].forEach((delay) => timers.push(window.setTimeout(() => clickAt(345, 215), delay)))
    timers.push(window.setTimeout(() => clickAt(720 - 592, 315), 1200))
    return () => timers.forEach((timer) => window.clearTimeout(timer))
  }, [])
  const [place, setPlace] = useState<Place>(params.get('place') === 'patio' ? 'patio' : 'room')
  const [items, setItems] = useState<HouseItem[]>([
    ...DEFAULT_LAYOUT.map(([kind, x, y]) => ({ id: kind, house_id: 'prueba', kind, place: 'room' as const, x, y })),
    ...PATIO_LAYOUT.map(([kind, x, y]) => ({ id: kind, house_id: 'prueba', kind, place: 'patio' as const, x, y })),
  ])
  return (
    <main>
      <Room
        items={items.filter((item) => item.place === place)}
        waterTrigger={waterTrigger}
        onWaterDone={(slot) => console.log('regado', slot)}
        plots={[
          { slot: 0, unlocked: true, unlock_price: 0, stage: 'empty', waterings: 0, next_water_at: null, withers_at: null },
          { slot: 1, unlocked: params.get('plots') === 'all', unlock_price: 60, stage: (params.get('stage') ?? 'empty') as 'empty', waterings: 0, next_water_at: null, withers_at: null },
          { slot: 2, unlocked: params.get('plots') === 'all', unlock_price: 120, stage: 'empty', waterings: 0, next_water_at: null, withers_at: null },
        ]}
        onPlotTap={(slot) => console.log('bancal', slot)}
        onFeedRequest={() => console.log('comer')}
        feedTrigger={feedTrigger}
        place={place}
        onTravel={setPlace}
        style={{ wall, floor }}
        editing={editing}
        onMoveItem={(itemId, x, y) =>
          setItems((current) => current.map((item) => (item.id === itemId ? { ...item, x, y } : item)))
        }
        stats={stats}
        canSend
        windowName={windowName}
        sleeping={sleeping}
        onBlockedTap={() => console.log('bloqueado')}
        onAction={(action) => console.log('acción', action)}
        onSend={() => console.log('enviar')}
      />
    </main>
  )
}

createRoot(document.getElementById('root')!).render(<Preview />)
