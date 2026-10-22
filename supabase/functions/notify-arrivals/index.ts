import { createClient } from 'npm:@supabase/supabase-js@2'
import webpush from 'npm:web-push@3.6.7'

const GONE_STATUS_CODES = [404, 410]
const PUSH_TTL_SECONDS = 3600
const SOFT_LEVEL = 30
const URGENT_LEVEL = 10
const REARM_LEVEL = 40

type StatKey = 'satiety' | 'happiness' | 'energy'
type Level = 0 | 1 | 2
type Payload = { title: string; body: string; tag: string; url: string }

const STAT_KEYS: StatKey[] = ['satiety', 'happiness', 'energy']

const NEEDS: Record<StatKey, { phrase: string; soft: [string, string]; urgent: [string, string] }> = {
  satiety: {
    phrase: 'tiene hambre',
    soft: ['Nailong tiene hambre', 'Dale de comer.'],
    urgent: ['¡Nailong tiene mucha hambre!', 'Dale de comer cuanto antes.'],
  },
  happiness: {
    phrase: 'está aburrido',
    soft: ['Nailong está aburrido', 'Juega un rato con él.'],
    urgent: ['¡Nailong está muy triste!', 'Juega con él cuanto antes.'],
  },
  energy: {
    phrase: 'tiene sueño',
    soft: ['Nailong tiene sueño', 'Mándalo a la cama un rato.'],
    urgent: ['¡Nailong está agotado!', 'Necesita descansar ya.'],
  },
}

export function nextLevel(value: number, current: Level): Level {
  if (value < URGENT_LEVEL) return 2
  if (value < SOFT_LEVEL) return 1
  if (value >= REARM_LEVEL) return 0
  return current
}

function joinPhrases(phrases: string[]) {
  const text =
    phrases.length === 1
      ? phrases[0]
      : `${phrases.slice(0, -1).join(', ')} y ${phrases[phrases.length - 1]}`
  return `${text.charAt(0).toUpperCase()}${text.slice(1)}.`
}

export function needsPayload(raised: StatKey[], levels: Record<StatKey, Level>): Payload {
  if (raised.length === 1) {
    const key = raised[0]
    const [title, body] = levels[key] === 2 ? NEEDS[key].urgent : NEEDS[key].soft
    return { title, body, tag: 'nailong-needs', url: './' }
  }
  const urgent = raised.some((key) => levels[key] === 2)
  return {
    title: urgent ? '¡Nailong te necesita ya!' : '¡Nailong te necesita!',
    body: joinPhrases(raised.map((key) => NEEDS[key].phrase)),
    tag: 'nailong-needs',
    url: './',
  }
}

const ARRIVAL_PAYLOAD: Payload = {
  title: '¡Nailong está en tu puerta!',
  body: 'Ya llegó. Ábrele para que pase.',
  tag: 'nailong-arrival',
  url: './',
}

function coinsPhrase(amount: number, verb: string) {
  return amount > 0 ? ` ${verb} ${amount} ${amount === 1 ? 'moneda' : 'monedas'}.` : ''
}

function escapePayload(stolen: number): Payload {
  return {
    title: '¡Nailong se escapó!',
    body: `Se aburrió y salió a dar una vuelta.${coinsPhrase(stolen, 'Se llevó')} Volverá en unas horas.`,
    tag: 'nailong-escape',
    url: './',
  }
}

function returnPayload(refund: number): Payload {
  return {
    title: '¡Nailong volvió!',
    body: `Ya está de vuelta en casa.${coinsPhrase(refund, 'Trajo de vuelta')}`,
    tag: 'nailong-escape',
    url: './',
  }
}

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })

// deno-lint-ignore no-explicit-any
async function notify(supabase: any, userId: string, payload: Payload) {
  const { data: subscriptions } = await supabase
    .from('push_subscriptions')
    .select('endpoint, p256dh, auth')
    .eq('user_id', userId)

  let sent = 0
  for (const subscription of subscriptions ?? []) {
    try {
      await webpush.sendNotification(
        { endpoint: subscription.endpoint, keys: { p256dh: subscription.p256dh, auth: subscription.auth } },
        JSON.stringify(payload),
        { TTL: PUSH_TTL_SECONDS },
      )
      sent += 1
    } catch (error) {
      const statusCode = (error as { statusCode?: number }).statusCode
      if (statusCode !== undefined && GONE_STATUS_CODES.includes(statusCode)) {
        await supabase.from('push_subscriptions').delete().eq('endpoint', subscription.endpoint)
      }
    }
  }
  return sent
}

Deno.serve(async (request) => {
  if (request.headers.get('x-cron-secret') !== Deno.env.get('CRON_SECRET')) {
    return json({ error: 'forbidden' }, 403)
  }

  webpush.setVapidDetails(
    Deno.env.get('VAPID_SUBJECT')!,
    Deno.env.get('VAPID_PUBLIC_KEY')!,
    Deno.env.get('VAPID_PRIVATE_KEY')!,
  )
  const supabase = createClient(Deno.env.get('SUPABASE_URL')!, Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!)
  const result = { arrival: 0, escape: 0, needs: 0, raised: [] as StatKey[] }

  const { data: nailong } = await supabase
    .from('nailong')
    .select('current_home, status, arrives_at, arrival_notified')
    .single()

  const arrivalDue =
    nailong &&
    nailong.status === 'traveling' &&
    !nailong.arrival_notified &&
    nailong.arrives_at &&
    new Date(nailong.arrives_at) <= new Date()
  if (arrivalDue) {
    result.arrival = await notify(supabase, nailong.current_home, ARRIVAL_PAYLOAD)
    await supabase.from('nailong').update({ arrival_notified: true }).eq('id', true)
  }

  const { data: roaming } = await supabase.rpc('run_escape_check')
  if (roaming?.escaped || roaming?.returned) {
    result.escape = await notify(supabase, roaming.home, roaming.escaped ? escapePayload(roaming.stolen ?? 0) : returnPayload(roaming.refund ?? 0))
  }

  const { data: current } = await supabase.rpc('current_stats').single()
  if (current && current.status === 'home' && !current.sleeping) {
    const levels = {} as Record<StatKey, Level>
    const updates: Record<string, number> = {}
    for (const key of STAT_KEYS) {
      const previous = Number(current[`${key}_alert`]) as Level
      const next = nextLevel(Number(current[key]), previous)
      levels[key] = next
      if (next !== previous) updates[`${key}_alert`] = next
      if (next > previous) result.raised.push(key)
    }
    if (result.raised.length > 0) {
      result.needs = await notify(supabase, current.current_home, needsPayload(result.raised, levels))
    }
    if (Object.keys(updates).length > 0) {
      await supabase.from('nailong').update(updates).eq('id', true)
    }
  }

  return json(result)
})
