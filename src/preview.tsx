import { useState } from 'react'
import { createRoot } from 'react-dom/client'
import { Room } from './components/Room'
import type { HouseItem, ItemKind } from './lib/house'
import { WINDOW_NAMES, type WindowName } from './lib/weather'
import './style.css'

const params = new URLSearchParams(location.search)
const requested = params.get('w') as WindowName | null
const windowName = requested && WINDOW_NAMES.includes(requested) ? requested : 'day'
const sleeping = params.get('sleep') === '1'
const editing = params.get('edit') === '1'

const DEFAULT_LAYOUT: [ItemKind, number, number][] = [
  ['rug', 360, 300], ['clock', 200, 86], ['wallshelf', 385, 100], ['bookshelf', 480, 168],
  ['sidetable', 200, 190], ['pouf', 470, 270], ['armchair', 585, 305], ['toybox', 200, 336],
  ['plant', 44, 340], ['bed', 100, 236], ['bowl', 500, 330], ['ball', 300, 344], ['door', 582, 156],
]

function Preview() {
  const [items, setItems] = useState<HouseItem[]>(
    DEFAULT_LAYOUT.map(([kind, x, y]) => ({ id: kind, house_id: 'prueba', kind, x, y })),
  )
  return (
    <main>
      <Room
        items={items}
        editing={editing}
        onMoveItem={(itemId, x, y) =>
          setItems((current) => current.map((item) => (item.id === itemId ? { ...item, x, y } : item)))
        }
        stats={{ satiety: 80, happiness: 80, energy: 80 }}
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
