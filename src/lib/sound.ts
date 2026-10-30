export type SoundMode = 'all' | 'fx' | 'off'
export type Sfx =
  | 'feed' | 'play' | 'sleep' | 'send' | 'knock' | 'arrive' | 'welcome'
  | 'hit' | 'bonus' | 'miss' | 'combo' | 'levelup'

const STORAGE_KEY = 'nailong:sound'
const SFX_VOLUME = 0.22
const MUSIC_VOLUME = 0.07
const SCHEDULE_AHEAD = 0.6
const BEAT = 60 / 116
const LOOP_BEATS = 32

const NOTE = {
  C3: 130.81, F3: 174.61, G3: 196,
  C5: 523.25, D5: 587.33, E5: 659.25, F5: 698.46, G5: 783.99, A5: 880, B5: 987.77,
  C6: 1046.5, D6: 1174.66, E6: 1318.5, G6: 1568,
} as const

type MusicEvent = { beat: number; freq: number; duration: number; type: OscillatorType; peak: number }

const MELODY: [number, number][] = [
  [NOTE.E5, 0.5], [NOTE.G5, 0.5], [NOTE.C6, 1], [NOTE.G5, 0.5], [NOTE.E5, 0.5], [NOTE.G5, 1],
  [NOTE.A5, 0.5], [NOTE.G5, 0.5], [NOTE.F5, 1], [NOTE.A5, 0.5], [NOTE.G5, 0.5], [NOTE.F5, 1],
  [NOTE.E5, 0.5], [NOTE.G5, 0.5], [NOTE.C6, 1], [NOTE.E6, 1], [NOTE.C6, 1],
  [NOTE.D6, 0.5], [NOTE.C6, 0.5], [NOTE.B5, 1], [NOTE.G5, 2],
  [NOTE.E5, 0.5], [NOTE.G5, 0.5], [NOTE.C6, 1], [NOTE.G5, 0.5], [NOTE.E5, 0.5], [NOTE.G5, 1],
  [NOTE.A5, 1], [NOTE.C6, 0.5], [NOTE.A5, 0.5], [NOTE.F5, 1], [NOTE.A5, 1],
  [NOTE.G5, 0.5], [NOTE.B5, 0.5], [NOTE.D6, 1], [NOTE.B5, 0.5], [NOTE.G5, 0.5], [NOTE.D6, 1],
  [NOTE.C6, 1], [NOTE.G5, 1], [NOTE.C6, 2],
]
const BASS_ROOTS = [NOTE.C3, NOTE.F3, NOTE.C3, NOTE.G3, NOTE.C3, NOTE.F3, NOTE.G3, NOTE.C3]

function buildMusic(): MusicEvent[] {
  const events: MusicEvent[] = []
  let beat = 0
  for (const [freq, length] of MELODY) {
    events.push({ beat, freq, duration: length * BEAT * 0.8, type: 'square', peak: 0.5 })
    beat += length
  }
  BASS_ROOTS.forEach((root, bar) => {
    for (let step = 0; step < 4; step += 1) {
      const freq = step % 2 === 0 ? root : root * 1.5
      events.push({ beat: bar * 4 + step, freq, duration: BEAT * 0.45, type: 'triangle', peak: 1 })
    }
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
    case 'hit':
      play(NOTE.G5, 0, 0.08, 'square', NOTE.C6)
      break
    case 'bonus':
      play(NOTE.C6, 0, 0.07, 'square')
      play(NOTE.G6, 0.07, 0.12, 'square')
      break
    case 'miss':
      play(200, 0, 0.25, 'sawtooth', 80)
      break
    case 'combo':
      ;[NOTE.E6, NOTE.G6].forEach((freq, index) => play(freq, index * 0.06, 0.1, 'triangle'))
      break
    case 'levelup':
      ;[NOTE.C5, NOTE.E5, NOTE.G5, NOTE.C6, NOTE.E6, NOTE.G6].forEach((freq, index) => play(freq, index * 0.09, 0.2, 'square'))
      break
  }
}

const PUMPKIN_NOTES = [NOTE.C5, NOTE.E5, NOTE.G5, NOTE.C6]

export function playPumpkinNote(index: number) {
  if (!audio || mode === 'off') return
  tone(PUMPKIN_NOTES[index], audio.currentTime, 0.3, 'triangle', 1, sfxBus)
}
