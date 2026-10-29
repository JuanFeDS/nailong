export const COSTUMES = [
  { id: 'calabaza', label: 'Calabaza' },
  { id: 'fantasma', label: 'Fantasma' },
  { id: 'bruja', label: 'Bruja' },
  { id: 'murcielago', label: 'Murciélago' },
  { id: 'vampiro', label: 'Vampiro' },
  { id: 'spiderman', label: 'Hombre Araña' },
  { id: 'pollito', label: 'Pollito' },
] as const

const STORAGE_KEY = 'nailong-costume'

export function loadCostume(): string | null {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    return COSTUMES.some((costume) => costume.id === saved) ? saved : null
  } catch {
    return null
  }
}

export function saveCostume(id: string | null) {
  try {
    if (id) localStorage.setItem(STORAGE_KEY, id)
    else localStorage.removeItem(STORAGE_KEY)
  } catch {
    // Sin almacenamiento el disfraz solo dura la sesión.
  }
}
