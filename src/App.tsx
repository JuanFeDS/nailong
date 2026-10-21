import type { Session } from '@supabase/supabase-js'
import { useEffect, useState } from 'react'
import { AwayRoom } from './components/AwayRoom'
import { Login } from './components/Login'
import { PixelIcon } from './components/PixelIcon'
import { Room } from './components/Room'
import { Sprite } from './components/Sprite'
import { SoundToggle } from './components/SoundToggle'
import { StatMeters } from './components/StatMeters'
import { IncomingScene, KnockingScene } from './components/TravelScenes'
import { type Action, useNailong } from './hooks/useNailong'
import { playSfx } from './lib/sound'
import { supabase } from './lib/supabase'

const KNOCK_FIRST_MS = 850
const KNOCK_CYCLE_MS = 1600

function formatRemaining(ms: number) {
  const totalSeconds = Math.ceil(ms / 1000)
  const days = Math.floor(totalSeconds / 86_400)
  const hours = Math.floor((totalSeconds % 86_400) / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const seconds = totalSeconds % 60
  const pad = (value: number) => String(value).padStart(2, '0')
  const clock = days || hours ? `${pad(hours)}:${pad(minutes)}:${pad(seconds)}` : `${pad(minutes)}:${pad(seconds)}`
  return days ? `${days} d ${clock}` : clock
}

function Loading() {
  return (
    <div className="loading">
      <Sprite scale={2} animate />
      <p className="loading__text">Despertando a Nailong…</p>
    </div>
  )
}

function Home({ userId }: { userId: string }) {
  const { loaded, stats, phase, hostName, myName, otherName, msUntilSend, error, doAction, send, letIn } =
    useNailong(userId)

  useEffect(() => {
    if (phase !== 'knocking') return
    playSfx('arrive')
    let knockTimer: number | undefined
    const firstKnock = window.setTimeout(() => {
      playSfx('knock')
      knockTimer = window.setInterval(() => playSfx('knock'), KNOCK_CYCLE_MS)
    }, KNOCK_FIRST_MS)
    return () => {
      window.clearTimeout(firstKnock)
      window.clearInterval(knockTimer)
    }
  }, [phase])

  if (!loaded || !stats || !phase) return <Loading />

  const isHome = phase === 'home'
  const canSend = msUntilSend === 0
  const remaining = canSend ? null : formatRemaining(msUntilSend)

  const act = (action: Action) => {
    playSfx(action)
    doAction(action)
  }
  const sendWithSound = () => {
    playSfx('send')
    send()
  }
  const letInWithSound = () => {
    playSfx('welcome')
    letIn()
  }

  return (
    <main className="home">
      <header className="topbar">
        <span className="wordmark">Nailong</span>
        <span className="who">
          <span className={isHome ? 'who__dot who__dot--home' : 'who__dot'} />
          Casa de {myName ?? '…'}
        </span>
        <SoundToggle />
        <button className="ghost" onClick={() => supabase.auth.signOut()}>
          Salir
        </button>
      </header>

      {phase === 'home' && <Room stats={stats} canSend={canSend} onAction={act} onSend={sendWithSound} />}
      {phase === 'incoming' && <IncomingScene from={otherName} />}
      {phase === 'knocking' && (
        <>
          <KnockingScene />
          <button className="btn" onClick={letInWithSound}>
            Dejar pasar
          </button>
        </>
      )}
      {(phase === 'visiting' || phase === 'outgoing' || phase === 'waiting') && (
        <AwayRoom variant={phase} host={hostName} returnIn={remaining} />
      )}

      <StatMeters stats={stats} />

      {isHome && (
        <p className={canSend ? 'door door--open' : 'door'}>
          <PixelIcon name="door" size={20} />
          {canSend ? `La puerta está lista para enviarlo con ${otherName ?? 'la otra persona'}` : `Puerta cerrada · ${remaining}`}
        </p>
      )}

      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
    </main>
  )
}

export default function App() {
  const [session, setSession] = useState<Session | null | undefined>(undefined)

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => setSession(data.session))
    const { data } = supabase.auth.onAuthStateChange((_event, nextSession) => setSession(nextSession))
    return () => data.subscription.unsubscribe()
  }, [])

  if (session === undefined) return null
  return session ? <Home userId={session.user.id} /> : <Login />
}
