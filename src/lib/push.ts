import { asset } from './asset'
import { supabase } from './supabase'

const PUBLIC_KEY = import.meta.env.VITE_VAPID_PUBLIC_KEY as string | undefined

export type PushState = 'unsupported' | 'needs-install' | 'denied' | 'off' | 'on'

const isIos =
  /iPad|iPhone|iPod/.test(navigator.userAgent) ||
  (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1)

const isInstalled = () =>
  window.matchMedia('(display-mode: standalone)').matches ||
  (navigator as { standalone?: boolean }).standalone === true

function toKey(base64Url: string) {
  const padded = base64Url + '='.repeat((4 - (base64Url.length % 4)) % 4)
  const raw = atob(padded.replace(/-/g, '+').replace(/_/g, '/'))
  return Uint8Array.from(raw, (char) => char.charCodeAt(0))
}

async function registration() {
  await navigator.serviceWorker.register(asset('sw.js'))
  return navigator.serviceWorker.ready
}

export async function getPushState(): Promise<PushState> {
  if (!PUBLIC_KEY) return 'unsupported'
  if (isIos && !isInstalled()) return 'needs-install'
  if (!('serviceWorker' in navigator) || !('PushManager' in window) || !('Notification' in window)) {
    return 'unsupported'
  }
  if (Notification.permission === 'denied') return 'denied'
  if (Notification.permission !== 'granted') return 'off'
  const subscription = await (await registration()).pushManager.getSubscription()
  return subscription ? 'on' : 'off'
}

export async function enablePush(userId: string): Promise<PushState> {
  const permission = await Notification.requestPermission()
  if (permission !== 'granted') return permission === 'denied' ? 'denied' : 'off'

  const worker = await registration()
  const subscription =
    (await worker.pushManager.getSubscription()) ??
    (await worker.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: toKey(PUBLIC_KEY!) }))
  const { endpoint, keys } = subscription.toJSON()
  if (!endpoint || !keys) return 'off'

  const { error } = await supabase
    .from('push_subscriptions')
    .upsert({ endpoint, user_id: userId, p256dh: keys.p256dh, auth: keys.auth })
  if (error) throw new Error(error.message)
  return 'on'
}

export async function disablePush(): Promise<PushState> {
  const subscription = await (await registration()).pushManager.getSubscription()
  if (subscription) {
    await supabase.from('push_subscriptions').delete().eq('endpoint', subscription.endpoint)
    await subscription.unsubscribe()
  }
  return 'off'
}
