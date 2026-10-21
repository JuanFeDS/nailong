import { createRoot } from 'react-dom/client'
import { AwayRoom } from './components/AwayRoom'
import { IncomingScene, KnockingScene } from './components/TravelScenes'
import './style.css'

const mode = new URLSearchParams(location.search).get('s') ?? 'incoming'

createRoot(document.getElementById('root')!).render(
  <main className="home">
    {mode === 'incoming' && <IncomingScene from="gabi" />}
    {mode === 'knocking' && (
      <>
        <KnockingScene />
        <button className="btn">Dejar pasar</button>
      </>
    )}
    {mode === 'outgoing' && <AwayRoom variant="outgoing" host="gabi" returnIn={null} />}
    {mode === 'waiting' && <AwayRoom variant="waiting" host="gabi" returnIn={null} />}
  </main>,
)
