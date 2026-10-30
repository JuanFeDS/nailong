import { useCallback, useMemo, useState } from 'react'
import { asset } from '../lib/asset'
import { isUnlocked, type Level, LEVELS, loadProgress, MINIGAMES, type MinigameId, starGoal } from '../lib/minigames'
import { supabase } from '../lib/supabase'
import { makeCatchTreats } from './catchTreats'
import { makeGhostHunt } from './ghostHunt'
import { makePumpkinMemory } from './pumpkinMemory'
import { MinigameCanvas } from './MinigameCanvas'

interface Props {
  costume: string | null
  onReward: () => void
  onExit: () => void
}

interface Playing {
  id: MinigameId
  level: Level
}

export function Minigames({ costume, onReward, onExit }: Props) {
  const [playing, setPlaying] = useState<Playing | null>(null)

  const ghostSpec = useMemo(() => playing?.id === 'ghosts' && makeGhostHunt(playing.level), [playing])
  const memorySpec = useMemo(() => playing?.id === 'memory' && makePumpkinMemory(playing.level), [playing])
  const catchSpec = useMemo(() => playing?.id === 'catch' && makeCatchTreats(costume, playing.level), [playing, costume])

  const reward = useCallback(
    async (score: number) => {
      if (!playing) return null
      const { data, error } = await supabase.rpc('finish_minigame', { game: playing.id, level: playing.level, score })
      if (error) return null
      onReward()
      return data as number
    },
    [playing, onReward],
  )

  if (playing) {
    const next = playing.level < 3 ? ((playing.level + 1) as Level) : null
    const key = `${playing.id}-${playing.level}`
    const shared = {
      id: playing.id,
      level: playing.level,
      reward,
      onNext: next ? () => setPlaying({ id: playing.id, level: next }) : null,
      onExit: () => setPlaying(null),
    }
    if (ghostSpec) return <MinigameCanvas key={key} {...shared} spec={ghostSpec} />
    if (memorySpec) return <MinigameCanvas key={key} {...shared} spec={memorySpec} />
    if (catchSpec) return <MinigameCanvas key={key} {...shared} spec={catchSpec} />
  }

  return (
    <section className="minigames">
      <h2 className="minigames__title">Minijuegos</h2>
      {MINIGAMES.map((game) => {
        const progress = loadProgress(game.id)
        return (
          <article key={game.id} className="minigames__card">
            <img className="minigames__art" src={asset(game.art)} alt="" />
            <span className="minigames__name">{game.title}</span>
            <span className="minigames__blurb">{game.blurb}</span>
            <div className="minigames__levels">
              {LEVELS.map((level) => {
                const open = isUnlocked(progress, level)
                const stars = progress.stars[level - 1]
                return (
                  <button
                    key={level}
                    className="minigames__level"
                    disabled={!open}
                    onClick={() => setPlaying({ id: game.id, level })}
                    aria-label={open ? `Nivel ${level}, ${stars} estrellas` : `Nivel ${level} bloqueado`}
                  >
                    <span className="minigames__level-name">Nivel {level}</span>
                    {open ? (
                      <span className="minigames__level-stars">
                        {[0, 1, 2].map((index) => (
                          <span key={index} className={index < stars ? 'is-on' : ''}>
                            ★
                          </span>
                        ))}
                      </span>
                    ) : (
                      <span className="minigames__level-lock">{starGoal(game.id, (level - 1) as Level)} pts en nivel {level - 1}</span>
                    )}
                    {open && progress.records[level - 1] > 0 && (
                      <span className="minigames__level-record">Récord {progress.records[level - 1]}</span>
                    )}
                  </button>
                )
              })}
            </div>
          </article>
        )
      })}
      <button className="ghost" onClick={onExit}>
        Volver a la casa
      </button>
    </section>
  )
}
