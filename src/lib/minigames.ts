export const MINIGAMES = [
  { id: 'ghosts', art: 'minigames/ghosts.svg', title: 'Caza fantasmas', blurb: 'Toca los fantasmas antes de que se vayan. Los murciélagos restan puntos.' },
  { id: 'memory', art: 'minigames/memory.svg', title: 'Memoria de calabazas', blurb: 'Repite la secuencia de calabazas que se iluminan. Cada ronda suma una.' },
  { id: 'catch', art: 'minigames/catch.svg', title: 'Atrapa dulces', blurb: 'Mueve a Nailong y atrapa dulces y calabazas. Esquiva los fantasmas.' },
] as const

export type MinigameId = (typeof MINIGAMES)[number]['id']
export type Level = 1 | 2 | 3

export const LEVELS: Level[] = [1, 2, 3]

const STAR_SCORES: Record<MinigameId, Record<Level, [number, number, number]>> = {
  ghosts: { 1: [12, 28, 45], 2: [16, 34, 52], 3: [20, 40, 60] },
  catch: { 1: [20, 40, 60], 2: [25, 48, 70], 3: [30, 55, 80] },
  memory: { 1: [3, 6, 9], 2: [4, 7, 10], 3: [5, 8, 11] },
}

export const starsFor = (id: MinigameId, level: Level, score: number) =>
  STAR_SCORES[id][level].filter((needed) => score >= needed).length

export const starGoal = (id: MinigameId, level: Level) => STAR_SCORES[id][level][0]

export interface Progress {
  stars: [number, number, number]
  records: [number, number, number]
}

const progressKey = (id: MinigameId) => `nailong-minigame-${id}`
const legacyRecordKey = (id: MinigameId) => `nailong-record-${id}`

export function loadProgress(id: MinigameId): Progress {
  try {
    const stored = localStorage.getItem(progressKey(id))
    if (stored) return JSON.parse(stored) as Progress
    const legacy = Number(localStorage.getItem(legacyRecordKey(id))) || 0
    return { stars: [starsFor(id, 1, legacy), 0, 0], records: [legacy, 0, 0] }
  } catch {
    return { stars: [0, 0, 0], records: [0, 0, 0] }
  }
}

export function saveProgress(id: MinigameId, progress: Progress) {
  try {
    localStorage.setItem(progressKey(id), JSON.stringify(progress))
  } catch {
    // Sin almacenamiento el progreso solo dura la partida.
  }
}

export const isUnlocked = (progress: Progress, level: Level) => level === 1 || progress.stars[level - 2] > 0
