import { createRoot } from 'react-dom/client'
import { Room } from './components/Room'
import { WINDOW_NAMES, type WindowName } from './lib/weather'
import './style.css'

const params = new URLSearchParams(location.search)
const requested = params.get('w') as WindowName | null
const windowName = requested && WINDOW_NAMES.includes(requested) ? requested : 'day'
const sleeping = params.get('sleep') === '1'

createRoot(document.getElementById('root')!).render(
  <main>
    <Room
      stats={{ satiety: 80, happiness: 80, energy: 80 }}
      canSend
      windowName={windowName}
      sleeping={sleeping}
      onBlockedTap={() => console.log('bloqueado')}
      onAction={(action) => console.log('acción', action)}
      onSend={() => console.log('enviar')}
    />
  </main>,
)
