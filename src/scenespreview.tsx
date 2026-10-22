import { useState } from 'react'
import { createRoot } from 'react-dom/client'
import { AwayRoom } from './components/AwayRoom'
import { NotificationToggle } from './components/NotificationToggle'
import { SoundToggle } from './components/SoundToggle'
import { IncomingScene, KnockingScene } from './components/TravelScenes'
import './style.css'

const mode = new URLSearchParams(location.search).get('s') ?? 'incoming'

function TopbarPreview() {
  const [notice, setNotice] = useState<string | null>(null)
  return (
    <>
      <header className="topbar">
        <span className="wordmark">Nailong</span>
        <span className="who">Casa de juan</span>
        <NotificationToggle userId="prueba" onMessage={setNotice} />
        <SoundToggle />
        <button className="ghost">Salir</button>
      </header>
      {notice && <p className="notice">{notice}</p>}
    </>
  )
}

createRoot(document.getElementById('root')!).render(
  <main className="home">
    {mode === 'incoming' && <IncomingScene from="gabi" />}
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
    {mode === 'topbar' && <TopbarPreview />}
  </main>,
)
