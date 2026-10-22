import type { FoodItem, FoodKind, Pantry } from '../hooks/useGarden'
import { FOOD_ICONS, FOOD_LABELS } from '../lib/food'
import { PixelIcon } from './PixelIcon'

interface Props {
  pantry: Pantry
  foods: FoodItem[]
  error: string | null
  onSell: (quantity: number) => void
}

export function PantryView({ pantry, foods, error, onSell }: Props) {
  const owned = foods.filter((food) => (pantry.items[food.kind] ?? 0) > 0)

  return (
    <section className="menu__section">
      <h3 className="menu__heading">Despensa</h3>
      {owned.length === 0 && (
        <p className="menu__hint">Está vacía. Compra comida en la tienda o cosecha en la huerta.</p>
      )}
      {owned.map((food) => {
        const quantity = pantry.items[food.kind as FoodKind] ?? 0
        return (
          <div key={food.kind} className="mission">
            <div className="mission__info">
              <span className="mission__label">
                <PixelIcon name={FOOD_ICONS[food.kind as FoodKind]} size={16} />{' '}
                {FOOD_LABELS[food.kind as FoodKind]} ×{quantity}
              </span>
              <span className="mission__progress">Alimenta +{food.satiety}</span>
            </div>
            {food.sell_price !== null && (
              <button className="btn btn--small" onClick={() => onSell(1)}>
                <PixelIcon name="coin" size={16} />
                Vender {food.sell_price}
              </button>
            )}
          </div>
        )
      })}
      {error && <p className="error">{error}</p>}
    </section>
  )
}
