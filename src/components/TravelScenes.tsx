import { Sprite } from './Sprite'

export function IncomingScene({ from }: { from?: string }) {
  return (
    <div className="room scene scene--road">
      <div className="road">
        <div className="road__walker">
          <Sprite scale={2} sheet="walk" />
        </div>
      </div>
      <div className="scene__text">
        <h2 className="scene__title">Nailong va de camino</h2>
        <p className="scene__sub">
          Sale de casa de {from ?? 'la otra persona'}
          <span className="dots" aria-hidden="true" />
        </p>
      </div>
    </div>
  )
}

export function KnockingScene() {
  return (
    <div className="room scene scene--door">
      <div className="knock" role="img" aria-label="Nailong llamando a la puerta" />
      <div className="scene__text">
        <h2 className="scene__title">Nailong está en la puerta</h2>
      </div>
    </div>
  )
}
