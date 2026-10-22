import type { Plot } from '../hooks/useGarden'
import { formatDuration } from '../lib/time'
import { PixelIcon } from './PixelIcon'

interface Props {
  plot: Plot
  coins: number
  now: number
  error: string | null
  onPlant: () => void
  onWater: () => void
  onHarvest: () => void
  onClose: () => void
}

const SEED_PRICE = 5
const WATERINGS_NEEDED = 3
const WITHER_WARNING_MS = 12 * 3_600_000

export function GardenSheet({ plot, coins, now, error, onPlant, onWater, onHarvest, onClose }: Props) {
  const waitMs = plot.next_water_at ? new Date(plot.next_water_at).getTime() - now : 0
  const witherMs = plot.withers_at ? new Date(plot.withers_at).getTime() - now : 0

  return (
    <div className="menu" onClick={onClose}>
      <div className="menu__sheet" role="dialog" aria-label="Huerta" onClick={(event) => event.stopPropagation()}>
        <header className="menu__header">
          <h2 className="menu__title">Huerta</h2>
          <button className="ghost" onClick={onClose}>
            Cerrar
          </button>
        </header>

        <section className="menu__section">
          {plot.stage === 'empty' && (
            <>
              <p className="menu__hint">Bancal libre. Siembra y riega 3 veces, con 2 horas entre riegos.</p>
              <button className="menu__row" disabled={coins < SEED_PRICE} onClick={onPlant}>
                <PixelIcon name="seed" size={20} />
                <span>Sembrar tomates · {SEED_PRICE} monedas</span>
              </button>
            </>
          )}

          {plot.stage === 'sprout' && (
            <>
              <p className="menu__hint">
                Riegos: {plot.waterings}/{WATERINGS_NEEDED}
                {witherMs > 0 && witherMs < WITHER_WARNING_MS ? ` · se marchita en ${formatDuration(witherMs)}` : ''}
              </p>
              <button className="menu__row" disabled={waitMs > 0} onClick={onWater}>
                <PixelIcon name="drop" size={20} />
                <span>{waitMs > 0 ? `Todavía húmedo · ${formatDuration(waitMs)}` : 'Regar'}</span>
              </button>
            </>
          )}

          {plot.stage === 'ripe' && (
            <>
              <p className="menu__hint">¡Están maduros! Rinde 2 tomates.</p>
              <button className="menu__row" onClick={onHarvest}>
                <PixelIcon name="tomato" size={20} />
                <span>Cosechar</span>
              </button>
            </>
          )}
        </section>

        {error && <p className="error">{error}</p>}
      </div>
    </div>
  )
}
