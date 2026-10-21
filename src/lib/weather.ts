export const WINDOW_NAMES = [
  'night', 'dawn', 'day', 'sunset',
  'winter', 'spring', 'summer', 'autumn',
  'rain', 'fog', 'storm', 'aurora',
] as const

export type WindowName = (typeof WINDOW_NAMES)[number]

export interface Place {
  label: string
  latitude: number
  longitude: number
}

export const PLACES: Record<string, Place> = {
  juan: { label: 'Bogotá', latitude: 4.711, longitude: -74.072 },
  gabi: { label: 'Cusco', latitude: -13.532, longitude: -71.967 },
}

const REFRESH_MS = 15 * 60 * 1000
const AURORA_EVERY_DAYS = 9

const STORM_CODES = [95, 96, 99]
const SNOW_CODES = [71, 73, 75, 77, 85, 86]
const FOG_CODES = [45, 48]
const CLEAR_CODES = [0, 1]

function isRain(code: number) {
  return (code >= 51 && code <= 67) || (code >= 80 && code <= 82)
}

export async function fetchWeatherCode(place: Place): Promise<number | null> {
  const url = `https://api.open-meteo.com/v1/forecast?latitude=${place.latitude}&longitude=${place.longitude}&current=weather_code&timezone=auto`
  try {
    const response = await fetch(url)
    if (!response.ok) return null
    const data = await response.json()
    return typeof data.current?.weather_code === 'number' ? data.current.weather_code : null
  } catch {
    return null
  }
}

function seasonWindow(month: number, latitude: number): WindowName {
  const southern = latitude < 0
  const shifted = southern ? (month + 6) % 12 : month
  if (shifted >= 2 && shifted <= 4) return 'spring'
  if (shifted >= 5 && shifted <= 7) return 'summer'
  if (shifted >= 8 && shifted <= 10) return 'autumn'
  return 'day'
}

function dayOfYear(date: Date) {
  const start = new Date(date.getFullYear(), 0, 0).getTime()
  return Math.floor((date.getTime() - start) / 86_400_000)
}

export function pickWindow(date: Date, latitude: number, code: number | null): WindowName {
  if (code !== null) {
    if (STORM_CODES.includes(code)) return 'storm'
    if (isRain(code)) return 'rain'
    if (FOG_CODES.includes(code)) return 'fog'
    if (SNOW_CODES.includes(code)) return 'winter'
  }

  const hour = date.getHours()
  if (hour >= 21 || hour < 5) {
    const clear = code === null || CLEAR_CODES.includes(code)
    return clear && dayOfYear(date) % AURORA_EVERY_DAYS === 0 ? 'aurora' : 'night'
  }
  if (hour < 8) return 'dawn'
  if (hour >= 17) return 'sunset'
  return code !== null && CLEAR_CODES.includes(code) ? seasonWindow(date.getMonth(), latitude) : 'day'
}

export { REFRESH_MS }
