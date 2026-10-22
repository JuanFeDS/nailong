import { useCallback, useEffect, useState } from 'react'
import type { HouseItem } from '../lib/house'
import { supabase } from '../lib/supabase'

export function useHouse(userId: string) {
  const [items, setItems] = useState<HouseItem[]>([])

  const load = useCallback(
    () =>
      supabase
        .from('house_items')
        .select('*')
        .eq('house_id', userId)
        .then(({ data }) => data && setItems(data as HouseItem[])),
    [userId],
  )

  useEffect(() => {
    load()
  }, [load])

  const moveItem = useCallback(
    async (itemId: string, x: number, y: number) => {
      setItems((current) => current.map((item) => (item.id === itemId ? { ...item, x, y } : item)))
      const { error } = await supabase.rpc('move_item', { item_id: itemId, new_x: x, new_y: y })
      if (error) load()
    },
    [load],
  )

  return { items, moveItem }
}
