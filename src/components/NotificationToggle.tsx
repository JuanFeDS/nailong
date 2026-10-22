import { useEffect, useState } from 'react'
import { disablePush, enablePush, getPushState, type PushState } from '../lib/push'
import { PixelIcon } from './PixelIcon'

interface Props {
  userId: string
  onMessage: (text: string) => void
  row?: boolean
}

const MESSAGES: Record<Exclude<PushState, 'on' | 'off'>, string> = {
  unsupported: 'Este navegador no permite avisos',
  'needs-install': 'Para recibir avisos, instala la app: Compartir → Añadir a pantalla de inicio',
  denied: 'Los avisos están bloqueados en los ajustes del móvil',
}

export function NotificationToggle({ userId, onMessage, row }: Props) {
  const [state, setState] = useState<PushState>('off')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    getPushState().then(setState).catch(() => setState('unsupported'))
  }, [])

  const toggle = async () => {
    if (busy) return
    if (state !== 'on' && state !== 'off') {
      onMessage(MESSAGES[state])
      return
    }
    setBusy(true)
    try {
      const next = state === 'on' ? await disablePush() : await enablePush(userId)
      setState(next)
      if (next === 'on') onMessage('Listo: te avisaremos cuando Nailong llegue')
      else if (next === 'denied') onMessage(MESSAGES.denied)
      else if (state === 'on') onMessage('Avisos desactivados')
    } catch {
      onMessage('No se pudieron activar los avisos. Inténtalo de nuevo')
    } finally {
      setBusy(false)
    }
  }

  const label = state === 'on' ? 'Avisos activados' : 'Avisarme cuando llegue Nailong'
  return (
    <button
      className={row ? 'menu__row' : 'ghost ghost--icon'}
      onClick={toggle}
      aria-label={label}
      title={label}
    >
      <PixelIcon name={state === 'on' ? 'bell' : 'bellOff'} size={20} />
      {row && <span>{state === 'on' ? 'Avisos activados' : 'Avisos desactivados'}</span>}
    </button>
  )
}
