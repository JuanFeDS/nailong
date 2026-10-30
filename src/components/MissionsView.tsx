import type { MissionId, Wallet } from '../hooks/useEconomy'
import { PixelIcon } from './PixelIcon'

interface Props {
  wallet: Wallet
  careOk: boolean
  error: string | null
  onClaim: (mission: MissionId) => void
}

const REWARD = 10
const BONUS = 10
const DAILY_CAP = 30

export function MissionsView({ wallet, careOk, error, onClaim }: Props) {
  const missions: { id: MissionId; label: string; progress: number; target: number }[] = [
    { id: 'feed', label: 'Dale de comer 2 veces', progress: Math.min(wallet.feeds, 2), target: 2 },
    { id: 'play', label: 'Juega con él', progress: Math.min(wallet.plays, 1), target: 1 },
    { id: 'care', label: 'Ten las tres barras sobre 50', progress: careOk ? 1 : 0, target: 1 },
  ]

  return (
    <>
      <section className="menu__section">
        <h3 className="menu__heading">Misiones de hoy</h3>
        {missions.map((mission) => {
          const claimed = wallet.claimed.includes(mission.id)
          const done = mission.progress >= mission.target
          return (
            <div key={mission.id} className="mission">
              <div className="mission__info">
                <span className="mission__label">{mission.label}</span>
                <span className="mission__progress">
                  {mission.progress}/{mission.target} · +{REWARD}
                </span>
              </div>
              {claimed ? (
                <span className="mission__done">Hecha</span>
              ) : (
                <button className="btn btn--small" disabled={!done} onClick={() => onClaim(mission.id)}>
                  Reclamar
                </button>
              )}
            </div>
          )
        })}
        <p className="menu__hint">
          <PixelIcon name="coin" size={16} />
          Las tres: +{BONUS} extra ({wallet.claimed.length}/3)
        </p>
      </section>

      <section className="menu__section">
        <h3 className="menu__heading">Por cuidarlo</h3>
        <p className="menu__hint">
          5 monedas por cada comer, jugar o dormir · hoy {wallet.earned_today}/{DAILY_CAP}
        </p>
      </section>

      {error && <p className="error">{error}</p>}
    </>
  )
}
