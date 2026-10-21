import { PixelIcon } from './PixelIcon'
import { Sprite } from './Sprite'

export type AwayVariant = 'visiting' | 'outgoing' | 'waiting'

interface Props {
  variant: AwayVariant
  host?: string
  returnIn: string | null
}

const WAVE_FRAME = 3

export function AwayRoom({ variant, host, returnIn }: Props) {
  const name = host ?? 'la otra persona'
  const title = {
    visiting: <>De visita en casa de <span className="away__host">{name}</span></>,
    outgoing: <>De camino a casa de <span className="away__host">{name}</span></>,
    waiting: <>En la puerta de <span className="away__host">{name}</span></>,
  }[variant]
  const note = {
    visiting: returnIn ? `Vuelve en ${returnIn}` : 'Ya puede volver',
    outgoing: 'Llegará en unos minutos',
    waiting: `Esperando que ${name} le abra`,
  }[variant]

  return (
    <div className="room away">
      <div className="away__content">
        <Sprite scale={2} frame={WAVE_FRAME} />
        <h2 className="away__title">{title}</h2>
        <p className="away__text">
          <PixelIcon name="house" size={18} />
          {note}
        </p>
      </div>
    </div>
  )
}
