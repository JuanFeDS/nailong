import { createClient } from 'npm:@supabase/supabase-js@2'
import webpush from 'npm:web-push@3.6.7'

const GONE_STATUS_CODES = [404, 410]
const PUSH_TTL_SECONDS = 3600

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })

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

  const { data: nailong } = await supabase
    .from('nailong')
    .select('current_home, status, arrives_at, arrival_notified')
    .single()

  const due =
    nailong &&
    nailong.status === 'traveling' &&
    !nailong.arrival_notified &&
    nailong.arrives_at &&
    new Date(nailong.arrives_at) <= new Date()
  if (!due) return json({ sent: 0, reason: 'nada que avisar' })

  const { data: subscriptions } = await supabase
    .from('push_subscriptions')
    .select('endpoint, p256dh, auth')
    .eq('user_id', nailong.current_home)

  const payload = JSON.stringify({
    title: '¡Nailong está en tu puerta!',
    body: 'Ya llegó. Ábrele para que pase.',
    url: './',
  })

  let sent = 0
  for (const subscription of subscriptions ?? []) {
    try {
      await webpush.sendNotification(
        { endpoint: subscription.endpoint, keys: { p256dh: subscription.p256dh, auth: subscription.auth } },
        payload,
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

  await supabase.from('nailong').update({ arrival_notified: true }).eq('id', true)
  return json({ sent, subscriptions: subscriptions?.length ?? 0 })
})
