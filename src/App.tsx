import type { Session } from '@supabase/supabase-js'
import { useEffect, useState } from 'react'
import { AwayRoom } from './components/AwayRoom'
import { Login } from './components/Login'
import { PixelIcon } from './components/PixelIcon'
import { Room } from './components/Room'
import { Sprite } from './components/Sprite'
import { StatMeters } from './components/StatMeters'
import { useNailong } from './hooks/useNailong'
import { supabase } from './lib/supabase'

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
  const { loaded, stats, isHome, hostName, myName, otherName, msUntilSend, error, doAction, send } = useNailong(userId)

  if (!loaded || !stats) return <Loading />

  const canSend = msUntilSend === 0
  const remaining = canSend ? null : formatRemaining(msUntilSend)

  return (
    <main className="home">
      <header className="topbar">
        <span className="wordmark">Nailong</span>
        <span className="who">
          <span className={isHome ? 'who__dot who__dot--home' : 'who__dot'} />
          Casa de {myName ?? '…'}
        </span>
        <button className="ghost" onClick={() => supabase.auth.signOut()}>
          Salir
        </button>
      </header>

      {isHome ? (
        <Room stats={stats} canSend={canSend} onAction={doAction} onSend={send} />
      ) : (
        <AwayRoom host={hostName} returnIn={remaining} />
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
