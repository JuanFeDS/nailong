import { useState } from 'react'
import { createRoot } from 'react-dom/client'
import { AwayRoom } from './components/AwayRoom'
import { MenuSheet } from './components/MenuSheet'
import { Minigames } from './components/Minigames'
import { PixelIcon } from './components/PixelIcon'
import { IncomingScene, KnockingScene } from './components/TravelScenes'
import './style.css'

const mode = new URLSearchParams(location.search).get('s') ?? 'incoming'

function TopbarPreview() {
  const [notice, setNotice] = useState<string | null>(null)
  const [open, setOpen] = useState(true)
  return (
    <>
      <header className="topbar">
        <span className="wordmark">Nailong</span>
        <span className="who">Casa de juan</span>
        <button className="ghost ghost--icon" onClick={() => setOpen(true)}>
          <PixelIcon name="menu" size={20} />
        </button>
      </header>
      {open && (
        <MenuSheet
          userId="prueba"
          canTinker
          costume={null}
          halloween
          onHalloween={() => undefined}
          onCostume={() => undefined}
          initialView={mode === 'costume' ? 'costume' : mode === 'shop' ? 'shop' : mode === 'missions' ? 'missions' : mode === 'pantry' ? 'pantry' : 'main'}
          economy={{
            wallet: { coins: 85, earned_today: 25, feeds: 1, plays: 1, claimed: ['play'] },
            shop: [
              { kind: 'cushions', price: 35, place: 'room' },
              { kind: 'hangingplant', price: 45, place: 'room' },
              { kind: 'painting', price: 55, place: 'room' },
              { kind: 'lamp', price: 60, place: 'room' },
              { kind: 'bigplant', price: 70, place: 'room' },
              { kind: 'coffeetable', price: 80, place: 'room' },
              { kind: 'desk', price: 110, place: 'room' },
              { kind: 'fishtank', price: 120, place: 'room' },
              { kind: 'tv', price: 140, place: 'room' },
              { kind: 'wardrobe', price: 150, place: 'room' },
              { kind: 'sofa', price: 160, place: 'room' },
              { kind: 'flowerpots', price: 40, place: 'patio' },
              { kind: 'birdbath', price: 75, place: 'patio' },
              { kind: 'lamppost', price: 90, place: 'patio' },
              { kind: 'bench', price: 100, place: 'patio' },
            ],
            error: null,
            refresh: async () => undefined,
            claim: async () => undefined,
            buy: async () => null,
          }}
          garden={{
            pantry: { items: { bread: 2, tomato: 1 }, ration_ready: false, ration_at: null },
            plots: [
              { slot: 0, unlocked: true, unlock_price: 0, stage: 'empty', waterings: 0, next_water_at: null, withers_at: null },
              { slot: 1, unlocked: false, unlock_price: 60, stage: 'empty', waterings: 0, next_water_at: null, withers_at: null },
            ],
            foods: [
              { kind: 'bread', price: 6, satiety: 15, sell_price: null },
              { kind: 'meal', price: 14, satiety: 30, sell_price: null },
              { kind: 'tomato', price: null, satiety: 40, sell_price: 25 },
            ],
            error: null,
            buyFood: async () => true,
            plant: async () => true,
            water: async () => true,
            harvest: async () => true,
            clear: async () => true,
            buyPlot: async () => true,
            sell: async () => true,
          }}
          careOk
          onBuy={() => undefined}
          style={{ wall: 'blue', floor: 'wood' }}
          onStyle={() => undefined}
          notice={notice}
          onNotice={setNotice}
          onTinker={() => setOpen(false)}
          onSignOut={() => setNotice('Salir')}
          onClose={() => setOpen(false)}
        />
      )}
    </>
  )
}

createRoot(document.getElementById('root')!).render(
  <main className="home">
    {mode === 'incoming' && <IncomingScene from="gabi" />}
    {mode === 'minigames' && <Minigames onReward={() => {}} costume={new URLSearchParams(location.search).get('costume')} onExit={() => console.log('volver')} />}
    {mode === 'knocking' && (
      <>
        <KnockingScene />
        <button className="btn">Dejar pasar</button>
      </>
    )}
    {mode === 'outgoing' && <AwayRoom variant="outgoing" host="gabi" stay={null} />}
    {mode === 'waiting' && <AwayRoom variant="waiting" host="gabi" stay={null} />}
    {mode === 'lost' && <AwayRoom variant="lost" host="juan" stay={null} />}
    {mode === 'visiting' && <AwayRoom variant="visiting" host="gabi" stay="5 h 12 min" />}
    {(mode === 'topbar' || mode === 'shop' || mode === 'missions' || mode === 'pantry' || mode === 'costume') && <TopbarPreview />}
  </main>,
)
