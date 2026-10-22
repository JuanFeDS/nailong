import type { PixelIconName } from '../components/PixelIcon'
import type { FoodKind } from '../hooks/useGarden'

export const FOOD_LABELS: Record<FoodKind, string> = {
  bread: 'Pan',
  meal: 'Comida casera',
  tomato: 'Tomate',
}

export const FOOD_ICONS: Record<FoodKind, PixelIconName> = {
  bread: 'bread',
  meal: 'bowl',
  tomato: 'tomato',
}

export const RATION_SATIETY = 10
