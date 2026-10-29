import { useMemo, useState } from 'react'
import { asset } from '../lib/asset'
import { loadRecord, MINIGAMES, type MinigameId } from '../lib/minigames'
import { makeCatchTreats } from './catchTreats'
import { ghostHunt } from './ghostHunt'
import { pumpkinMemory } from './pumpkinMemory'
import { MinigameCanvas } from './MinigameCanvas'

interface Props {
  costume: string | null
  onExit: () => void
}

export function Minigames({ costume, onExit }: Props) {
  const [playing, setPlaying] = useState<MinigameId | null>(null)
  const catchTreats = useMemo(() => makeCatchTreats(costume), [costume])

  if (playing === 'ghosts') return <MinigameCanvas id="ghosts" spec={ghostHunt} onExit={() => setPlaying(null)} />
  if (playing === 'memory') return <MinigameCanvas id="memory" spec={pumpkinMemory} onExit={() => setPlaying(null)} />
  if (playing === 'catch') return <MinigameCanvas id="catch" spec={catchTreats} onExit={() => setPlaying(null)} />

  return (
    <section className="minigames">
      <h2 className="minigames__title">Minijuegos</h2>
      {MINIGAMES.map((game) => (
        <button key={game.id} className="minigames__card" onClick={() => setPlaying(game.id)}>
          <img className="minigames__art" src={asset(game.art)} alt="" />
          <span className="minigames__name">{game.title}</span>
          <span className="minigames__blurb">{game.blurb}</span>
          <span className="minigames__record">Récord: {loadRecord(game.id)}</span>
        </button>
      ))}
      <button className="ghost" onClick={onExit}>
        Volver a la casa
      </button>
    </section>
  )
}
