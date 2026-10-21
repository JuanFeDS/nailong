export type SoundMode = 'all' | 'fx' | 'off'
export type Sfx = 'feed' | 'play' | 'sleep' | 'send' | 'knock' | 'arrive' | 'welcome'

const STORAGE_KEY = 'nailong:sound'
const SFX_VOLUME = 0.22
const MUSIC_VOLUME = 0.07
const SCHEDULE_AHEAD = 0.6
const BEAT = 60 / 84
const LOOP_BEATS = 32

const NOTE = {
  C3: 130.81, A2: 110, F2: 87.31, G2: 98,
  C5: 523.25, D5: 587.33, E5: 659.25, G5: 783.99, A5: 880, C6: 1046.5, E6: 1318.5, G6: 1568,
} as const

type MusicEvent = { beat: number; freq: number; duration: number; type: OscillatorType; peak: number }

const MELODY: [number, number][] = [
  [NOTE.E5, 1], [NOTE.G5, 1], [NOTE.A5, 1], [NOTE.G5, 1],
  [NOTE.E5, 2], [NOTE.D5, 1], [NOTE.C5, 1],
  [NOTE.D5, 1], [NOTE.E5, 1], [NOTE.G5, 1], [NOTE.E5, 1],
  [NOTE.D5, 2], [NOTE.C5, 2],
  [NOTE.E5, 1], [NOTE.G5, 1], [NOTE.A5, 1], [NOTE.C6, 1],
  [NOTE.A5, 2], [NOTE.G5, 2],
  [NOTE.E5, 1], [NOTE.D5, 1], [NOTE.C5, 1], [NOTE.D5, 1],
  [NOTE.C5, 4],
]
const BASS_ROOTS = [NOTE.C3, NOTE.C3, NOTE.A2, NOTE.A2, NOTE.F2, NOTE.F2, NOTE.G2, NOTE.C3]

function buildMusic(): MusicEvent[] {
  const events: MusicEvent[] = []
  let beat = 0
  for (const [freq, length] of MELODY) {
    events.push({ beat, freq, duration: length * BEAT * 0.9, type: 'square', peak: 0.5 })
    beat += length
  }
  BASS_ROOTS.forEach((root, bar) => {
    events.push({ beat: bar * 4, freq: root, duration: BEAT * 1.8, type: 'triangle', peak: 1 })
    events.push({ beat: bar * 4 + 2, freq: root * 1.5, duration: BEAT * 1.8, type: 'triangle', peak: 0.8 })
  })
  return events.sort((first, second) => first.beat - second.beat)
}

const MUSIC = buildMusic()

let audio: AudioContext | null = null
let sfxBus: GainNode
let musicBus: GainNode
let musicTimer: number | undefined
let cursor = 0
let loopStart = 0

function readMode(): SoundMode {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    return stored === 'fx' || stored === 'off' || stored === 'all' ? stored : 'all'
  } catch {
    return 'all'
  }
}

let mode: SoundMode = readMode()

export const getSoundMode = () => mode

export function setSoundMode(next: SoundMode) {
  mode = next
  try {
    localStorage.setItem(STORAGE_KEY, next)
  } catch {
    // sin almacenamiento: el modo solo dura la sesión
  }
  syncMusic()
}

function tone(
  freq: number,
  start: number,
  duration: number,
  type: OscillatorType,
  peak: number,
  bus: GainNode,
  glideTo?: number,
) {
  if (!audio) return
  const oscillator = audio.createOscillator()
  const gain = audio.createGain()
  oscillator.type = type
  oscillator.frequency.setValueAtTime(freq, start)
  if (glideTo) oscillator.frequency.exponentialRampToValueAtTime(glideTo, start + duration)
  gain.gain.setValueAtTime(0.0001, start)
  gain.gain.exponentialRampToValueAtTime(peak, start + 0.012)
  gain.gain.exponentialRampToValueAtTime(0.0001, start + duration)
  oscillator.connect(gain).connect(bus)
  oscillator.start(start)
  oscillator.stop(start + duration + 0.02)
}

function scheduleMusic() {
  if (!audio) return
  const horizon = audio.currentTime + SCHEDULE_AHEAD
  for (;;) {
    const event = MUSIC[cursor]
    const start = loopStart + event.beat * BEAT
    if (start > horizon) return
    if (start >= audio.currentTime) tone(event.freq, start, event.duration, event.type, event.peak, musicBus)
    cursor += 1
    if (cursor >= MUSIC.length) {
      cursor = 0
      loopStart += LOOP_BEATS * BEAT
    }
  }
}

function syncMusic() {
  if (!audio) return
  if (mode === 'all' && musicTimer === undefined) {
    cursor = 0
    loopStart = audio.currentTime + 0.15
    musicTimer = window.setInterval(scheduleMusic, 120)
  } else if (mode !== 'all' && musicTimer !== undefined) {
    window.clearInterval(musicTimer)
    musicTimer = undefined
  }
}

export function unlockAudio() {
  if (!audio) {
    audio = new AudioContext()
    sfxBus = audio.createGain()
    sfxBus.gain.value = SFX_VOLUME
    sfxBus.connect(audio.destination)
    musicBus = audio.createGain()
    musicBus.gain.value = MUSIC_VOLUME
    musicBus.connect(audio.destination)
  }
  if (audio.state === 'suspended') void audio.resume()
  syncMusic()
}

export function playSfx(name: Sfx) {
  if (!audio || mode === 'off') return
  const now = audio.currentTime
  const play = (freq: number, offset: number, duration: number, type: OscillatorType, glideTo?: number) =>
    tone(freq, now + offset, duration, type, 1, sfxBus, glideTo)

  switch (name) {
    case 'feed':
      for (let bite = 0; bite < 3; bite += 1) play(220, bite * 0.14, 0.1, 'square', 110)
      break
    case 'play':
      ;[NOTE.C5, NOTE.E5, NOTE.G5, NOTE.C6].forEach((freq, index) => play(freq, index * 0.08, 0.1, 'square'))
      break
    case 'sleep':
      ;[NOTE.G5, NOTE.E5, NOTE.C5].forEach((freq, index) => play(freq, index * 0.26, 0.4, 'triangle'))
      break
    case 'send':
      play(380, 0, 0.45, 'square', 1200)
      play(NOTE.G5, 0.5, 0.2, 'triangle')
      play(NOTE.C5, 0.65, 0.3, 'triangle')
      break
    case 'knock':
      for (let hit = 0; hit < 3; hit += 1) play(170, hit * 0.2, 0.12, 'sine', 60)
      break
    case 'arrive':
      ;[NOTE.C6, NOTE.E6, NOTE.G6].forEach((freq, index) => play(freq, index * 0.12, 0.35, 'triangle'))
      break
    case 'welcome':
      ;[NOTE.C5, NOTE.G5, NOTE.C6, NOTE.E6].forEach((freq, index) => play(freq, index * 0.1, 0.18, 'square'))
      break
  }
}
