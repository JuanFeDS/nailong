import { useCallback, useEffect, useState } from 'react'
import { DEFAULT_STYLE, type HouseItem, type HouseStyle } from '../lib/house'
import { supabase } from '../lib/supabase'

export function useHouse(userId: string) {
  const [items, setItems] = useState<HouseItem[]>([])
  const [style, setStyle] = useState<HouseStyle>(DEFAULT_STYLE)

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
    supabase
      .from('profiles')
      .select('wall, floor')
      .eq('id', userId)
      .single()
      .then(({ data }) => data && setStyle(data as HouseStyle))
  }, [load, userId])

  const changeStyle = useCallback(async (next: HouseStyle) => {
    setStyle(next)
    await supabase.rpc('set_house_style', { new_wall: next.wall, new_floor: next.floor })
  }, [])

  const moveItem = useCallback(
    async (itemId: string, x: number, y: number) => {
      setItems((current) => current.map((item) => (item.id === itemId ? { ...item, x, y } : item)))
      const { error } = await supabase.rpc('move_item', { item_id: itemId, new_x: x, new_y: y })
      if (error) load()
    },
    [load],
  )

  return { items, moveItem, style, changeStyle, reload: load }
}
