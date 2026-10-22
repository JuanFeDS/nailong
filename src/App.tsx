import type { Session } from '@supabase/supabase-js'
import { useEffect, useRef, useState } from 'react'
import { AwayRoom } from './components/AwayRoom'
import { FoodPicker } from './components/FoodPicker'
import { GardenSheet } from './components/GardenSheet'
import { Login } from './components/Login'
import { MenuSheet } from './components/MenuSheet'
import { PixelIcon } from './components/PixelIcon'
import { Room } from './components/Room'
import { Sprite } from './components/Sprite'
import { StatMeters } from './components/StatMeters'
import { IncomingScene, KnockingScene } from './components/TravelScenes'
import { type Action, useNailong } from './hooks/useNailong'
import { useEconomy } from './hooks/useEconomy'
import { useGarden } from './hooks/useGarden'
import { useHouse } from './hooks/useHouse'
import { useWeatherCode } from './hooks/useWeather'
import { ITEM_LABELS } from './lib/house'
import { isSleepTime, WAKE_LABEL } from './lib/sleep'
import { formatDuration } from './lib/time'
import { playSfx } from './lib/sound'
import { supabase } from './lib/supabase'
import { PLACES, pickWindow } from './lib/weather'

const NOTICE_MS = 2500
const KNOCK_FIRST_MS = 850
const KNOCK_CYCLE_MS = 1600


function Loading() {
  return (
    <div className="loading">
      <Sprite scale={2} animate />
      <p className="loading__text">Despertando a Nailong…</p>
    </div>
  )
}

function Home({ userId }: { userId: string }) {
  const { loaded, stats, phase, hostName, myName, otherName, stayMs, updatedAt, place: location, setPlace, error, doAction, feedWith, send, letIn } =
    useNailong(userId)

  const { items, moveItem, style, changeStyle, reload } = useHouse(userId)
  const economy = useEconomy(updatedAt)
  const garden = useGarden(updatedAt, economy.refresh)
  const [foodPicking, setFoodPicking] = useState(false)
  const [feedTrigger, setFeedTrigger] = useState(0)
  const [plotSlot, setPlotSlot] = useState<number | null>(null)
  const [waterTrigger, setWaterTrigger] = useState<{ id: number; slot: number } | null>(null)
  const pendingFood = useRef<string | null>(null)
  const isAsleep = () => isSleepTime(new Date())
  const [tinkering, setTinkering] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)

  const place = PLACES[(myName ?? '').toLowerCase()]
  const weatherCode = useWeatherCode(place)
  const [notice, setNotice] = useState<string | null>(null)

  const showNotice = (text: string) => {
    setNotice(text)
    window.setTimeout(() => setNotice(null), NOTICE_MS)
  }
  const showSleepingNotice = () => showNotice('Shh, Nailong está durmiendo')

  useEffect(() => {
    if (phase !== 'home' || location !== 'patio') return
    const bringInside = () => isAsleep() && setPlace('room')
    bringInside()
    const timer = window.setInterval(bringInside, 30_000)
    return () => window.clearInterval(timer)
  }, [phase, location])

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

  if (!loaded || !stats || !phase || items.length === 0) return <Loading />

  const isHome = phase === 'home'
  const stay = stayMs === null ? null : formatDuration(stayMs)

  const windowName = pickWindow(new Date(), place?.latitude ?? 0, weatherCode)
  const sleeping = isAsleep()

  const act = (action: Action) => {
    playSfx(action === 'swing' || action === 'soccer' ? 'play' : action)
    if (action !== 'feed') {
      doAction(action)
      return
    }
    if (pendingFood.current) feedWith(pendingFood.current)
    pendingFood.current = null
  }
  const pickFood = (food: string) => {
    pendingFood.current = food
    setFoodPicking(false)
    setFeedTrigger((count) => count + 1)
  }
  const buy = async (kind: string) => {
    const bought = await economy.buy(kind)
    if (!bought) return
    reload()
    showNotice(`Comprado: ${ITEM_LABELS[bought.kind] ?? bought.kind}. Colócalo con el trasteo`)
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
        <span className="coins" title="Monedas">
          <PixelIcon name="coin" size={18} />
          {economy.wallet.coins}
        </span>
        <button className="ghost ghost--icon" onClick={() => setMenuOpen(true)} aria-label="Abrir el menú">
          <PixelIcon name="menu" size={20} />
        </button>
      </header>

      {menuOpen && (
        <MenuSheet
          userId={userId}
          canTinker={isHome}
          economy={economy}
          garden={garden}
          careOk={Math.min(stats.satiety, stats.happiness, stats.energy) > 50}
          onBuy={buy}
          style={style}
          onStyle={changeStyle}
          notice={notice}
          onNotice={showNotice}
          onTinker={() => {
            setTinkering(true)
            setMenuOpen(false)
          }}
          onSignOut={() => supabase.auth.signOut()}
          onClose={() => setMenuOpen(false)}
        />
      )}

      {phase === 'home' && (
        <Room
          items={items.filter((item) => item.place === location)}
          plots={garden.plots}
          waterTrigger={waterTrigger}
          onWaterDone={garden.water}
          onPlotTap={setPlotSlot}
          onFeedRequest={() => setFoodPicking(true)}
          feedTrigger={feedTrigger}
          place={location}
          onTravel={setPlace}
          style={style}
          editing={tinkering}
          onMoveItem={moveItem}
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

      {isHome && tinkering && (
        <>
          <p className="door door--open">Arrastra los objetos para cambiarlos de sitio</p>
          <button className="btn" onClick={() => setTinkering(false)}>
            Listo
          </button>
        </>
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

      {foodPicking && (
        <FoodPicker
          pantry={garden.pantry}
          foods={garden.foods}
          now={Date.now()}
          onPick={pickFood}
          onClose={() => setFoodPicking(false)}
        />
      )}

      {plotSlot !== null && garden.plots.find((plot) => plot.slot === plotSlot) && (
        <GardenSheet
          plot={garden.plots.find((plot) => plot.slot === plotSlot)!}
          coins={economy.wallet.coins}
          now={Date.now()}
          error={garden.error}
          onPlant={() => garden.plant(plotSlot)}
          onWater={() => {
            setWaterTrigger({ id: Date.now(), slot: plotSlot })
            setPlotSlot(null)
          }}
          onHarvest={() => garden.harvest(plotSlot)}
          onClear={() => garden.clear(plotSlot)}
          onClose={() => setPlotSlot(null)}
        />
      )}

      {notice && !menuOpen && <p className="notice">{notice}</p>}

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
