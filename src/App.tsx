import type { Session } from '@supabase/supabase-js'
import { useEffect, useState } from 'react'
import { AwayRoom } from './components/AwayRoom'
import { Login } from './components/Login'
import { NotificationToggle } from './components/NotificationToggle'
import { PixelIcon } from './components/PixelIcon'
import { Room } from './components/Room'
import { Sprite } from './components/Sprite'
import { SoundToggle } from './components/SoundToggle'
import { StatMeters } from './components/StatMeters'
import { IncomingScene, KnockingScene } from './components/TravelScenes'
import { type Action, useNailong } from './hooks/useNailong'
import { useWeatherCode } from './hooks/useWeather'
import { isSleepTime, WAKE_LABEL } from './lib/sleep'
import { playSfx } from './lib/sound'
import { supabase } from './lib/supabase'
import { PLACES, pickWindow } from './lib/weather'

const NOTICE_MS = 2500
const KNOCK_FIRST_MS = 850
const KNOCK_CYCLE_MS = 1600

function formatStay(ms: number) {
  const totalMinutes = Math.floor(ms / 60_000)
  const days = Math.floor(totalMinutes / 1440)
  const hours = Math.floor((totalMinutes % 1440) / 60)
  const minutes = totalMinutes % 60
  if (days) return `${days} d ${hours} h`
  if (hours) return `${hours} h ${minutes} min`
  return `${minutes} min`
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
  const { loaded, stats, phase, hostName, myName, otherName, stayMs, error, doAction, send, letIn } =
    useNailong(userId)

  const place = PLACES[(myName ?? '').toLowerCase()]
  const weatherCode = useWeatherCode(place)
  const [notice, setNotice] = useState<string | null>(null)

  const showNotice = (text: string) => {
    setNotice(text)
    window.setTimeout(() => setNotice(null), NOTICE_MS)
  }
  const showSleepingNotice = () => showNotice('Shh, Nailong está durmiendo')

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
  const stay = stayMs === null ? null : formatStay(stayMs)

  const windowName = pickWindow(new Date(), place?.latitude ?? 0, weatherCode)
  const sleeping = isSleepTime(new Date())

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
        <NotificationToggle userId={userId} onMessage={showNotice} />
        <SoundToggle />
        <button className="ghost" onClick={() => supabase.auth.signOut()}>
          Salir
        </button>
      </header>

      {phase === 'home' && (
        <Room
          stats={stats}
          canSend
          windowName={windowName}
          sleeping={sleeping}
          onBlockedTap={showSleepingNotice}
          onAction={act}
          onSend={sendWithSound}
        />
      )}
      {phase === 'incoming' && <IncomingScene from={otherName} />}
      {phase === 'knocking' && (
        <>
          <KnockingScene />
          <button className="btn" onClick={letInWithSound}>
            Dejar pasar
          </button>
        </>
      )}
      {(phase === 'visiting' || phase === 'outgoing' || phase === 'waiting' || phase === 'lost') && (
        <AwayRoom variant={phase} host={hostName} stay={stay} />
      )}

      <StatMeters stats={stats} />

      {isHome && sleeping && (
        <p className="door">
          <PixelIcon name="house" size={20} />
          Nailong duerme · despierta a las {WAKE_LABEL}
        </p>
      )}

      {isHome && !sleeping && (
        <p className="door door--open">
          <PixelIcon name="door" size={20} />
          La puerta está lista para enviarlo con {otherName ?? 'la otra persona'}
        </p>
      )}

      {isHome && stay && (
        <p className="door">
          <PixelIcon name="house" size={20} />
          Lleva {stay} en esta casa
        </p>
      )}

      {notice && <p className="notice">{notice}</p>}

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
