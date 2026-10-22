import { useCallback, useEffect, useState } from 'react'
import { supabase } from '../lib/supabase'

export type FoodKind = 'bread' | 'meal' | 'tomato'
export type PlotStage = 'empty' | 'sprout' | 'growing' | 'ripe' | 'wilted'

export interface Pantry {
  items: Partial<Record<FoodKind, number>>
  ration_ready: boolean
  ration_at: string | null
}

export interface Plot {
  slot: number
  unlocked: boolean
  unlock_price: number
  stage: PlotStage
  waterings: number
  next_water_at: string | null
  withers_at: string | null
}

export interface FoodItem {
  kind: FoodKind
  price: number | null
  satiety: number
  sell_price: number | null
}

const EMPTY_PANTRY: Pantry = { items: {}, ration_ready: false, ration_at: null }

export function useGarden(refreshKey: string | undefined, onChanged: () => void) {
  const [pantry, setPantry] = useState<Pantry>(EMPTY_PANTRY)
  const [plots, setPlots] = useState<Plot[]>([])
  const [foods, setFoods] = useState<FoodItem[]>([])
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    const [pantryResult, gardenResult] = await Promise.all([
      supabase.rpc('pantry_status'),
      supabase.rpc('garden_status'),
    ])
    if (pantryResult.data) setPantry(pantryResult.data as Pantry)
    if (gardenResult.data) setPlots(gardenResult.data as Plot[])
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh, refreshKey])

  useEffect(() => {
    supabase
      .from('food_catalog')
      .select('kind, price, satiety, sell_price')
      .then(({ data }) => data && setFoods(data as FoodItem[]))
  }, [])

  const call = useCallback(
    async (name: string, args: Record<string, unknown>) => {
      const { error: rpcError } = await supabase.rpc(name, args)
      if (rpcError) {
        setError(rpcError.message)
        return false
      }
      setError(null)
      await refresh()
      onChanged()
      return true
    },
    [refresh, onChanged],
  )

  return {
    pantry,
    plots,
    foods,
    error,
    buyFood: (food: FoodKind) => call('buy_food', { food }),
    plant: (slot: number) => call('plant_seed', { plot_slot: slot }),
    water: (slot: number) => call('water_plot', { plot_slot: slot }),
    harvest: (slot: number) => call('harvest_plot', { plot_slot: slot }),
    clear: (slot: number) => call('clear_plot', { plot_slot: slot }),
    buyPlot: () => call('buy_plot', {}),
    sell: (quantity: number) => call('sell_fruit', { quantity }),
  }
}
