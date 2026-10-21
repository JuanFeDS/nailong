import { createClient } from '@supabase/supabase-js'

export const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY,
)

export interface NailongRow {
  satiety: number
  happiness: number
  energy: number
  last_updated_at: string
  current_home: string | null
  last_sent_at: string | null
  status: 'home' | 'traveling'
  arrives_at: string | null
  last_entered_at: string | null
}

export interface Profile {
  id: string
  display_name: string
}

export const SEND_COOLDOWN_MS = 3 * 24 * 60 * 60 * 1000
