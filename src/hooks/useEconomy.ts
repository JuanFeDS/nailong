import { useCallback, useEffect, useState } from 'react'
import type { HouseItem } from '../lib/house'
import { supabase } from '../lib/supabase'

export type MissionId = 'feed' | 'play' | 'care'

export interface Wallet {
  coins: number
  earned_today: number
  feeds: number
  plays: number
  claimed: MissionId[]
}

export interface ShopItem {
  kind: string
  price: number
}

const EMPTY_WALLET: Wallet = { coins: 0, earned_today: 0, feeds: 0, plays: 0, claimed: [] }

export function useEconomy(refreshKey: string | undefined) {
  const [wallet, setWallet] = useState<Wallet>(EMPTY_WALLET)
  const [shop, setShop] = useState<ShopItem[]>([])
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(
    () => supabase.rpc('wallet_status').then(({ data }) => data && setWallet(data as Wallet)),
    [],
  )

  useEffect(() => {
    refresh()
  }, [refresh, refreshKey])

  useEffect(() => {
    supabase
      .from('shop_items')
      .select('kind, price')
      .order('price')
      .then(({ data }) => data && setShop(data as ShopItem[]))
  }, [])

  const claim = useCallback(async (mission: MissionId) => {
    const { data, error: rpcError } = await supabase.rpc('claim_mission', { mission })
    if (rpcError) setError(rpcError.message)
    else {
      setError(null)
      setWallet(data as Wallet)
    }
  }, [])

  const buy = useCallback(
    async (kind: string): Promise<HouseItem | null> => {
      const { data, error: rpcError } = await supabase.rpc('buy_item', { item_kind: kind })
      if (rpcError) {
        setError(rpcError.message)
        return null
      }
      setError(null)
      await refresh()
      return data as HouseItem
    },
    [refresh],
  )

  return { wallet, shop, error, claim, buy, refresh }
}
