import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import './style.css'

// En la app instalada 100dvh puede medir más que la ventana visible; el alto real
// de la ventana evita que el cuerpo sobre y fuerce el desplazamiento.
const syncAppHeight = () => document.documentElement.style.setProperty('--app-height', `${window.innerHeight}px`)
syncAppHeight()
window.addEventListener('resize', syncAppHeight)
window.addEventListener('orientationchange', syncAppHeight)

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
