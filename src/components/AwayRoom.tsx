import { asset } from '../lib/asset'
import { PixelIcon } from './PixelIcon'
import { Sprite } from './Sprite'

export type AwayVariant = 'visiting' | 'outgoing' | 'waiting' | 'lost'

interface Props {
  variant: AwayVariant
  host?: string
  stay: string | null
}

const WAVE_FRAME = 3

function Note() {
  return <img className="away__note" src={asset('sprites/processed/note.png')} alt="Una nota que dejó Nailong" />
}

export function AwayRoom({ variant, host, stay }: Props) {
  const name = host ?? 'la otra persona'
  const title = {
    visiting: <>De visita en casa de <span className="away__host">{name}</span></>,
    outgoing: <>De camino a casa de <span className="away__host">{name}</span></>,
    waiting: <>En la puerta de <span className="away__host">{name}</span></>,
    lost: <>Nailong se escapó de casa de <span className="away__host">{name}</span></>,
  }[variant]
  const note = {
    visiting: stay ? `Lleva ${stay} allí` : 'De visita',
    lost: 'Se aburrió. Volverá en unas horas',
    outgoing: 'Llegará en unos minutos',
    waiting: `Esperando que ${name} le abra`,
  }[variant]

  return (
    <div className="room away">
      <div className="away__content">
        {variant === 'lost' ? <Note /> : <Sprite scale={2} frame={WAVE_FRAME} />}
        <h2 className="away__title">{title}</h2>
        <p className="away__text">
          <PixelIcon name="house" size={18} />
          {note}
        </p>
      </div>
    </div>
  )
}
