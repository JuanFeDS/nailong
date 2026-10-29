export const MINIGAMES = [
  { id: 'ghosts', art: 'minigames/ghosts.svg', title: 'Caza fantasmas', blurb: 'Toca los fantasmas antes de que se vayan. Los murciélagos restan puntos.' },
  { id: 'memory', art: 'minigames/memory.svg', title: 'Memoria de calabazas', blurb: 'Repite la secuencia de calabazas que se iluminan. Cada ronda suma una.' },
  { id: 'catch', art: 'minigames/catch.svg', title: 'Atrapa dulces', blurb: 'Mueve a Nailong y atrapa dulces y calabazas. Esquiva los fantasmas.' },
] as const

export type MinigameId = (typeof MINIGAMES)[number]['id']

const recordKey = (id: MinigameId) => `nailong-record-${id}`

export function loadRecord(id: MinigameId): number {
  try {
    return Number(localStorage.getItem(recordKey(id))) || 0
  } catch {
    return 0
  }
}

export function saveRecord(id: MinigameId, score: number) {
  try {
    localStorage.setItem(recordKey(id), String(score))
  } catch {
    // Sin almacenamiento el récord solo dura la partida.
  }
}
