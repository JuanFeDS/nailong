const HOUR_MS = 3_600_000
const DAY_MS = 24 * HOUR_MS
const COLOMBIA_OFFSET_MS = -5 * HOUR_MS
const BEDTIME_MS = 22.5 * HOUR_MS
const WAKE_MS = 8 * HOUR_MS

export const WAKE_LABEL = '8:00'

export const AWAKE_RATES = { satiety: -4, happiness: -4, energy: -3 }
export const ASLEEP_RATES = { satiety: -1.5, happiness: -1.5, energy: 7 }

export function travelFactor(tripTimes: string[], now: number) {
  const recent = tripTimes.filter((trip) => now - new Date(trip).getTime() < DAY_MS).length
  if (recent >= 5) return 2
  if (recent >= 3) return 1.5
  return 1
}

function msOfColombianDay(timestamp: number) {
  const local = timestamp + COLOMBIA_OFFSET_MS
  return ((local % DAY_MS) + DAY_MS) % DAY_MS
}

export function isSleepTime(date: Date) {
  const msOfDay = msOfColombianDay(date.getTime())
  return msOfDay >= BEDTIME_MS || msOfDay < WAKE_MS
}

export function nightHours(fromMs: number, toMs: number) {
  if (toMs <= fromMs) return 0
  const firstDay = Math.floor((fromMs + COLOMBIA_OFFSET_MS) / DAY_MS) - 1
  const lastDay = Math.floor((toMs + COLOMBIA_OFFSET_MS) / DAY_MS)
  let overlap = 0
  for (let day = firstDay; day <= lastDay; day += 1) {
    const start = day * DAY_MS + BEDTIME_MS - COLOMBIA_OFFSET_MS
    const end = (day + 1) * DAY_MS + WAKE_MS - COLOMBIA_OFFSET_MS
    overlap += Math.max(0, Math.min(toMs, end) - Math.max(fromMs, start))
  }
  return overlap / HOUR_MS
}
