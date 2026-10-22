import { PixelIcon } from './PixelIcon'
import { Sprite } from './Sprite'

export type AwayVariant = 'visiting' | 'outgoing' | 'waiting' | 'lost'

interface Props {
  variant: AwayVariant
  host?: string
  stay: string | null
}

const WAVE_FRAME = 3

const NOTE_RECTS = [
  { x: 5, y: 3, w: 16, h: 20, fill: '#00000059' },
  { x: 4, y: 2, w: 16, h: 20, fill: '#f1e3bd' },
  { x: 4, y: 20, w: 16, h: 2, fill: '#d9c795' },
  { x: 9, y: 0, w: 6, h: 4, fill: '#c93a2a' },
  { x: 6, y: 7, w: 12, h: 1, fill: '#3a2a22' },
  { x: 6, y: 10, w: 10, h: 1, fill: '#3a2a22' },
  { x: 6, y: 13, w: 12, h: 1, fill: '#3a2a22' },
  { x: 6, y: 16, w: 7, h: 1, fill: '#3a2a22' },
  { x: 15, y: 17, w: 1, h: 1, fill: '#c93a2a' },
  { x: 17, y: 17, w: 1, h: 1, fill: '#c93a2a' },
  { x: 14, y: 18, w: 5, h: 2, fill: '#c93a2a' },
]

function Note() {
  return (
    <svg
      className="away__note"
      viewBox="0 0 24 24"
      shapeRendering="crispEdges"
      role="img"
      aria-label="Una nota que dejó Nailong"
    >
      {NOTE_RECTS.map((rect) => (
        <rect key={`${rect.x}-${rect.y}-${rect.w}`} x={rect.x} y={rect.y} width={rect.w} height={rect.h} fill={rect.fill} />
      ))}
    </svg>
  )
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
