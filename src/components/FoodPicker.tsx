import type { FoodItem, FoodKind, Pantry } from '../hooks/useGarden'
import { FOOD_ICONS, FOOD_LABELS, RATION_SATIETY } from '../lib/food'
import { formatDuration } from '../lib/time'
import { PixelIcon } from './PixelIcon'

interface Props {
  pantry: Pantry
  foods: FoodItem[]
  now: number
  onPick: (food: string) => void
  onClose: () => void
}

export function FoodPicker({ pantry, foods, now, onPick, onClose }: Props) {
  const owned = foods.filter((food) => (pantry.items[food.kind] ?? 0) > 0)
  const rationWait = pantry.ration_at ? new Date(pantry.ration_at).getTime() - now : 0

  return (
    <div className="menu" onClick={onClose}>
      <div className="menu__sheet" role="dialog" aria-label="Dar de comer" onClick={(event) => event.stopPropagation()}>
        <header className="menu__header">
          <h2 className="menu__title">¿Qué le das?</h2>
          <button className="ghost" onClick={onClose}>
            Cancelar
          </button>
        </header>

        <section className="menu__section">
          {owned.map((food) => (
            <button key={food.kind} className="menu__row" onClick={() => onPick(food.kind)}>
              <PixelIcon name={FOOD_ICONS[food.kind as FoodKind]} size={20} />
              <span>
                {FOOD_LABELS[food.kind as FoodKind]} ×{pantry.items[food.kind as FoodKind]} · +{food.satiety}
              </span>
            </button>
          ))}
          {pantry.ration_ready && (
            <button className="menu__row" onClick={() => onPick('ration')}>
              <PixelIcon name="bowl" size={20} />
              <span>Ración de emergencia · +{RATION_SATIETY}</span>
            </button>
          )}
          {owned.length === 0 && !pantry.ration_ready && (
            <p className="menu__hint">
              No te queda comida. Compra en la tienda
              {rationWait > 0 ? ` o espera la ración de emergencia (${formatDuration(rationWait)})` : ''}.
            </p>
          )}
        </section>
      </div>
    </div>
  )
}
