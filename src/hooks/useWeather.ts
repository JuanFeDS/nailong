import { useEffect, useState } from 'react'
import { fetchWeatherCode, type Place, REFRESH_MS } from '../lib/weather'

export function useWeatherCode(place: Place | undefined) {
  const [code, setCode] = useState<number | null>(null)

  useEffect(() => {
    if (!place) return
    let cancelled = false
    const load = () =>
      fetchWeatherCode(place).then((value) => {
        if (!cancelled) setCode(value)
      })
    load()
    const timer = window.setInterval(load, REFRESH_MS)
    return () => {
      cancelled = true
      window.clearInterval(timer)
    }
  }, [place])

  return code
}
