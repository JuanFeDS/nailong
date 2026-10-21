import { PixelIcon } from './PixelIcon'
import { Sprite } from './Sprite'

interface Props {
  host?: string
  returnIn: string | null
}

const WAVE_FRAME = 3

export function AwayRoom({ host, returnIn }: Props) {
  return (
    <div className="room away">
      <div className="away__content">
        <Sprite scale={2} frame={WAVE_FRAME} />
        <h2 className="away__title">
          De visita en casa de <span className="away__host">{host ?? 'la otra persona'}</span>
        </h2>
        <p className="away__text">
          <PixelIcon name="house" size={18} />
          {returnIn ? `Vuelve en ${returnIn}` : 'Ya puede volver'}
        </p>
      </div>
    </div>
  )
}
