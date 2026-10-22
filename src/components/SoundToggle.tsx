import { useEffect, useState } from 'react'
import { getSoundMode, setSoundMode, type SoundMode, unlockAudio } from '../lib/sound'
import { PixelIcon, type PixelIconName } from './PixelIcon'

const NEXT: Record<SoundMode, SoundMode> = { all: 'fx', fx: 'off', off: 'all' }
const ICON: Record<SoundMode, PixelIconName> = { all: 'sound', fx: 'soundfx', off: 'mute' }
const LABEL: Record<SoundMode, string> = {
  all: 'Música y efectos',
  fx: 'Solo efectos',
  off: 'Sin sonido',
}

export function SoundToggle({ row }: { row?: boolean }) {
  const [mode, setMode] = useState<SoundMode>(getSoundMode)

  useEffect(() => {
    window.addEventListener('pointerdown', unlockAudio, { once: true })
    return () => window.removeEventListener('pointerdown', unlockAudio)
  }, [])

  const cycle = () => {
    unlockAudio()
    const next = NEXT[mode]
    setSoundMode(next)
    setMode(next)
  }

  return (
    <button
      className={row ? 'menu__row' : 'ghost ghost--icon'}
      onClick={cycle}
      aria-label={`Sonido: ${LABEL[mode]}`}
      title={LABEL[mode]}
    >
      <PixelIcon name={ICON[mode]} size={20} />
      {row && <span>Sonido: {LABEL[mode]}</span>}
    </button>
  )
}
