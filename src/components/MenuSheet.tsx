import { useEffect } from 'react'
import { NotificationToggle } from './NotificationToggle'
import { PixelIcon } from './PixelIcon'
import { SoundToggle } from './SoundToggle'

interface Props {
  userId: string
  canTinker: boolean
  notice: string | null
  onNotice: (text: string) => void
  onTinker: () => void
  onSignOut: () => void
  onClose: () => void
}

export function MenuSheet({ userId, canTinker, notice, onNotice, onTinker, onSignOut, onClose }: Props) {
  useEffect(() => {
    const closeOnEscape = (event: KeyboardEvent) => event.key === 'Escape' && onClose()
    window.addEventListener('keydown', closeOnEscape)
    return () => window.removeEventListener('keydown', closeOnEscape)
  }, [onClose])

  return (
    <div className="menu" onClick={onClose}>
      <div className="menu__sheet" role="dialog" aria-label="Menú" onClick={(event) => event.stopPropagation()}>
        <header className="menu__header">
          <h2 className="menu__title">Menú</h2>
          <button className="ghost" onClick={onClose}>
            Cerrar
          </button>
        </header>

        {canTinker && (
          <section className="menu__section">
            <h3 className="menu__heading">Casa</h3>
            <button className="menu__row" onClick={onTinker}>
              <PixelIcon name="house" size={20} />
              <span>Trastear con la casa</span>
            </button>
          </section>
        )}

        <section className="menu__section">
          <h3 className="menu__heading">Ajustes</h3>
          <NotificationToggle row userId={userId} onMessage={onNotice} />
          <SoundToggle row />
        </section>

        <section className="menu__section">
          <h3 className="menu__heading">Cuenta</h3>
          <button className="menu__row" onClick={onSignOut}>
            <PixelIcon name="door" size={20} />
            <span>Salir</span>
          </button>
        </section>

        {notice && <p className="notice">{notice}</p>}
      </div>
    </div>
  )
}
