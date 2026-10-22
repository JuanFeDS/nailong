import { useEffect, useState } from 'react'
import type { useEconomy } from '../hooks/useEconomy'
import type { useGarden } from '../hooks/useGarden'
import { asset } from '../lib/asset'
import { FLOORS, type HouseStyle, WALLS } from '../lib/house'
import { MissionsView } from './MissionsView'
import { NotificationToggle } from './NotificationToggle'
import { PantryView } from './PantryView'
import { PixelIcon } from './PixelIcon'
import { ShopView } from './ShopView'
import { SoundToggle } from './SoundToggle'

interface Props {
  userId: string
  canTinker: boolean
  economy: ReturnType<typeof useEconomy>
  garden: ReturnType<typeof useGarden>
  careOk: boolean
  onBuy: (kind: string) => void
  style: HouseStyle
  onStyle: (style: HouseStyle) => void
  notice: string | null
  onNotice: (text: string) => void
  onTinker: () => void
  onSignOut: () => void
  onClose: () => void
  initialView?: 'main' | 'style' | 'missions' | 'shop' | 'pantry'
}

const TITLES = {
  main: 'Menú',
  style: 'Paredes y suelo',
  missions: 'Misiones',
  shop: 'Tienda',
  pantry: 'Despensa',
}

export function MenuSheet({ userId, canTinker, economy, garden, careOk, onBuy, style, onStyle, notice, onNotice, onTinker, onSignOut, onClose, initialView = 'main' }: Props) {
  const lockedPlot = garden.plots.find((plot) => !plot.unlocked)
  const nextPlot = lockedPlot ? { slot: lockedPlot.slot, price: lockedPlot.unlock_price } : null
  const [view, setView] = useState<'main' | 'style' | 'missions' | 'shop' | 'pantry'>(initialView)

  useEffect(() => {
    const closeOnEscape = (event: KeyboardEvent) => event.key === 'Escape' && onClose()
    window.addEventListener('keydown', closeOnEscape)
    return () => window.removeEventListener('keydown', closeOnEscape)
  }, [onClose])

  return (
    <div className="menu" onClick={onClose}>
      <div className="menu__sheet" role="dialog" aria-label="Menú" onClick={(event) => event.stopPropagation()}>
        <header className="menu__header">
          <h2 className="menu__title">{TITLES[view]}</h2>
          {view === 'main' ? (
            <button className="ghost" onClick={onClose}>
              Cerrar
            </button>
          ) : (
            <button className="ghost" onClick={() => setView('main')}>
              Atrás
            </button>
          )}
        </header>

        {view === 'missions' && (
          <MissionsView wallet={economy.wallet} careOk={careOk} error={economy.error} onClaim={economy.claim} />
        )}

        {view === 'shop' && (
          <ShopView
            coins={economy.wallet.coins}
            shop={economy.shop}
            error={economy.error ?? garden.error}
            onBuy={onBuy}
            foods={garden.foods}
            onBuyFood={garden.buyFood}
            nextPlot={nextPlot}
            onBuyPlot={garden.buyPlot}
          />
        )}

        {view === 'pantry' && (
          <PantryView pantry={garden.pantry} foods={garden.foods} error={garden.error} onSell={garden.sell} />
        )}

        {view === 'style' && (
          <>
            <section className="menu__section">
              <h3 className="menu__heading">Pared</h3>
              <div className="swatches">
                {WALLS.map((option) => (
                  <button
                    key={option.id}
                    className={style.wall === option.id ? 'swatch swatch--on' : 'swatch'}
                    style={{ backgroundImage: `url(${asset(`rooms/walls/${option.id}.png`)})` }}
                    onClick={() => onStyle({ ...style, wall: option.id })}
                    aria-label={`Pared ${option.label}`}
                    aria-pressed={style.wall === option.id}
                  />
                ))}
              </div>
            </section>
            <section className="menu__section">
              <h3 className="menu__heading">Suelo</h3>
              <div className="swatches">
                {FLOORS.map((option) => (
                  <button
                    key={option.id}
                    className={style.floor === option.id ? 'swatch swatch--on' : 'swatch'}
                    style={{ backgroundImage: `url(${asset(`rooms/floors/${option.id}.png`)})` }}
                    onClick={() => onStyle({ ...style, floor: option.id })}
                    aria-label={`Suelo ${option.label}`}
                    aria-pressed={style.floor === option.id}
                  />
                ))}
              </div>
            </section>
          </>
        )}

        {view === 'main' && canTinker && (
          <section className="menu__section">
            <h3 className="menu__heading">Casa</h3>
            <button className="menu__row" onClick={onTinker}>
              <PixelIcon name="house" size={20} />
              <span>Trastear con la casa</span>
            </button>
            <button className="menu__row" onClick={() => setView('style')}>
              <PixelIcon name="house" size={20} />
              <span>Paredes y suelo</span>
            </button>
          </section>
        )}

        {view === 'main' && (
          <section className="menu__section">
            <h3 className="menu__heading">Monedas · {economy.wallet.coins}</h3>
            <button className="menu__row" onClick={() => setView('missions')}>
              <PixelIcon name="coin" size={20} />
              <span>Misiones diarias</span>
            </button>
            <button className="menu__row" onClick={() => setView('shop')}>
              <PixelIcon name="coin" size={20} />
              <span>Tienda</span>
            </button>
            <button className="menu__row" onClick={() => setView('pantry')}>
              <PixelIcon name="bread" size={20} />
              <span>Despensa</span>
            </button>
          </section>
        )}

        {view === 'main' && (
          <>
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
          </>
        )}

        {notice && <p className="notice">{notice}</p>}
      </div>
    </div>
  )
}
