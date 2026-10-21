import { useCallback, useEffect, useState } from 'react'
import {
  DECAY_PER_HOUR,
  type NailongRow,
  type Profile,
  SEND_COOLDOWN_MS,
  supabase,
} from '../lib/supabase'

export interface Stats {
  satiety: number
  happiness: number
  energy: number
}

export type Action = 'feed' | 'play' | 'sleep'

function decayedStats(row: NailongRow, now: number): Stats {
  const hours = Math.max(0, now - new Date(row.last_updated_at).getTime()) / 3_600_000
  const decay = (value: number, perHour: number) => Math.max(0, value - perHour * hours)
  return {
    satiety: decay(row.satiety, DECAY_PER_HOUR.satiety),
    happiness: decay(row.happiness, DECAY_PER_HOUR.happiness),
    energy: decay(row.energy, DECAY_PER_HOUR.energy),
  }
}

export type Phase = 'home' | 'visiting' | 'incoming' | 'knocking' | 'outgoing' | 'waiting'

function phaseOf(row: NailongRow, userId: string, now: number): Phase {
  const toMe = row.current_home === userId
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

  useEffect(() => {
    supabase.from('nailong').select('*').single().then(({ data }) => data && setRow(data))
    supabase.from('profiles').select('*').then(({ data }) => data && setProfiles(data))

    const channel = supabase
      .channel('nailong')
      .on('postgres_changes', { event: '*', schema: 'public', table: 'nailong' }, (payload) =>
        setRow(payload.new as NailongRow),
      )
      .subscribe()

    const timer = setInterval(() => setNow(Date.now()), 1000)
    return () => {
      clearInterval(timer)
      supabase.removeChannel(channel)
    }
  }, [])

  const run = useCallback(async (call: PromiseLike<{ data: unknown; error: { message: string } | null }>) => {
    const { data, error: rpcError } = await call
    if (rpcError) {
      setError(rpcError.message)
      return
    }
    setError(null)
    setRow(data as NailongRow)
  }, [])

  const doAction = (action: Action) => run(supabase.rpc('do_action', { action }))
  const send = () => run(supabase.rpc('send_nailong'))
  const letIn = () => run(supabase.rpc('let_in'))

  const hostName = profiles.find((profile) => profile.id === row?.current_home)?.display_name
  const myName = profiles.find((profile) => profile.id === userId)?.display_name
  const otherName = profiles.find((profile) => profile.id !== userId)?.display_name
  const sendAvailableAt = row?.last_entered_at ? new Date(row.last_entered_at).getTime() + SEND_COOLDOWN_MS : 0

  return {
    loaded: row !== null,
    stats: row ? decayedStats(row, now) : null,
    phase: row ? phaseOf(row, userId, now) : null,
    hostName,
    myName,
    otherName,
    msUntilSend: Math.max(0, sendAvailableAt - now),
    error,
    doAction,
    send,
    letIn,
  }
}
