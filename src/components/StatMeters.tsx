import type { CSSProperties } from 'react'
import type { Stats } from '../hooks/useNailong'
import { PixelIcon, type PixelIconName } from './PixelIcon'

const LOW_THRESHOLD = 30

const METERS: { key: keyof Stats; label: string; icon: PixelIconName; tone: string }[] = [
  { key: 'satiety', label: 'Comida', icon: 'bowl', tone: 'hot' },
  { key: 'happiness', label: 'Alegría', icon: 'heart', tone: 'sun' },
  { key: 'energy', label: 'Energía', icon: 'bolt', tone: 'teal' },
]

export function StatMeters({ stats }: { stats: Stats }) {
  return (
    <section className="meters" aria-label="Estado de Nailong">
      {METERS.map(({ key, label, icon, tone }) => {
        const value = Math.round(stats[key])
        const style = { '--v': value } as CSSProperties
        return (
          <div key={key} className={`meter meter--${tone}${value < LOW_THRESHOLD ? ' meter--low' : ''}`} style={style}>
            <div className="meter__head">
              <PixelIcon name={icon} size={22} />
              <span className="meter__value">{value}</span>
            </div>
            <div className="meter__bar" role="progressbar" aria-label={label} aria-valuenow={value} aria-valuemin={0} aria-valuemax={100}>
              <span className="meter__fill" />
            </div>
            <span className="meter__label">{label}</span>
          </div>
        )
      })}
    </section>
  )
}
