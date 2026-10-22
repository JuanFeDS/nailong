import { useCallback, useEffect, useState } from 'react'
import { ASLEEP_RATES, AWAKE_RATES, nightHours, travelFactor } from '../lib/sleep'
import type { Place } from '../lib/house'
import { type NailongRow, type Profile, supabase } from '../lib/supabase'

export interface Stats {
  satiety: number
  happiness: number
  energy: number
}

export type Action = 'feed' | 'play' | 'sleep' | 'swing' | 'soccer'

function decayedStats(row: NailongRow, now: number): Stats {
  const from = new Date(row.last_updated_at).getTime()
  const totalHours = Math.max(0, now - from) / 3_600_000
  const asleepHours = nightHours(from, now)
  const awakeHours = totalHours - asleepHours
  const tiredness = travelFactor(row.trip_times ?? [], now)
  const evolve = (value: number, key: keyof Stats) =>
    Math.min(
      100,
      Math.max(0, value + AWAKE_RATES[key] * tiredness * awakeHours + ASLEEP_RATES[key] * asleepHours),
    )
  return {
    satiety: evolve(row.satiety, 'satiety'),
    happiness: evolve(row.happiness, 'happiness'),
    energy: evolve(row.energy, 'energy'),
  }
}

export type Phase = 'home' | 'visiting' | 'incoming' | 'knocking' | 'outgoing' | 'waiting' | 'lost'

function phaseOf(row: NailongRow, userId: string, now: number): Phase {
  const toMe = row.current_home === userId
  if (row.status === 'lost') return 'lost'
  if ((row.status ?? 'home') === 'home') return toMe ? 'home' : 'visiting'
  const arrived = row.arrives_at !== null && now >= new Date(row.arrives_at).getTime()
  if (toMe) return arrived ? 'knocking' : 'incoming'
  return arrived ? 'waiting' : 'outgoing'
}

export function useNailong(userId: string) {
  const [row, setRow] = useState<NailongRow | null>(null)
  const [profiles, setProfiles] = useState<Profile[]>([])
  const [now, setNow] = useState(Date.now())
  const [error, setError] = useState<string | null>(null)

  const refetchRow = useCallback(
    () => supabase.from('nailong').select('*').single().then(({ data }) => data && setRow(data)),
    [],
  )

  useEffect(() => {
    refetchRow()
    supabase.from('profiles').select('*').then(({ data }) => data && setProfiles(data))

    const channel = supabase
      .channel('nailong')
      .on('postgres_changes', { event: '*', schema: 'public', table: 'nailong' }, (payload) =>
        setRow(payload.new as NailongRow),
      )
      .subscribe()

    const timer = setInterval(() => setNow(Date.now()), 1000)
    const refetchWhenVisible = () => document.visibilityState === 'visible' && refetchRow()
    document.addEventListener('visibilitychange', refetchWhenVisible)
    return () => {
      clearInterval(timer)
      document.removeEventListener('visibilitychange', refetchWhenVisible)
      supabase.removeChannel(channel)
    }
  }, [refetchRow])

  const run = useCallback(async (call: PromiseLike<{ data: unknown; error: { message: string } | null }>) => {
    const { data, error: rpcError } = await call
    if (rpcError) {
      setError(rpcError.message)
      refetchRow()
      return
    }
    setError(null)
    setRow(data as NailongRow)
  }, [refetchRow])

  const doAction = (action: Action) => run(supabase.rpc('do_action', { action }))
  const feedWith = (food: string) => run(supabase.rpc('feed_nailong', { food }))
  const send = () => run(supabase.rpc('send_nailong'))
  const letIn = () => run(supabase.rpc('let_in'))
  const setPlace = (place: Place) => run(supabase.rpc('set_place', { new_place: place }))

  const hostName = profiles.find((profile) => profile.id === row?.current_home)?.display_name
  const myName = profiles.find((profile) => profile.id === userId)?.display_name
  const otherName = profiles.find((profile) => profile.id !== userId)?.display_name
  const stayMs = row?.last_entered_at ? Math.max(0, now - new Date(row.last_entered_at).getTime()) : null

  return {
    loaded: row !== null,
    stats: row ? decayedStats(row, now) : null,
    phase: row ? phaseOf(row, userId, now) : null,
    hostName,
    myName,
    otherName,
    stayMs,
    updatedAt: row?.last_updated_at,
    awakeUntil: row?.awake_until ?? null,
    place: (row?.place ?? 'room') as Place,
    setPlace,
    error,
    doAction,
    feedWith,
    send,
    letIn,
  }
}
