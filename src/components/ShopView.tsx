import type { ShopItem } from '../hooks/useEconomy'
import type { FoodItem, FoodKind } from '../hooks/useGarden'
import { asset } from '../lib/asset'
import { FOOD_ICONS, FOOD_LABELS } from '../lib/food'
import { ITEM_LABELS, type ItemKind } from '../lib/house'
import { PixelIcon } from './PixelIcon'

interface Props {
  coins: number
  shop: ShopItem[]
  error: string | null
  onBuy: (kind: string) => void
  foods: FoodItem[]
  onBuyFood: (food: FoodKind) => void
  nextPlot: { slot: number; price: number } | null
  onBuyPlot: () => void
}

export function ShopView({ coins, shop, error, onBuy, foods, onBuyFood, nextPlot, onBuyPlot }: Props) {
  return (
    <section className="menu__section">
      <h3 className="menu__heading">Comida</h3>
      {foods
        .filter((food) => food.price !== null)
        .map((food) => (
          <div key={food.kind} className="mission">
            <div className="mission__info">
              <span className="mission__label">
                <PixelIcon name={FOOD_ICONS[food.kind]} size={16} /> {FOOD_LABELS[food.kind]}
              </span>
              <span className="mission__progress">Alimenta +{food.satiety}</span>
            </div>
            <button
              className="btn btn--small"
              disabled={coins < (food.price ?? 0)}
              onClick={() => onBuyFood(food.kind)}
            >
              <PixelIcon name="coin" size={16} />
              {food.price}
            </button>
          </div>
        ))}
      <h3 className="menu__heading">Huerta</h3>
      <div className="mission">
        <div className="mission__info">
          <span className="mission__label">
            <PixelIcon name="seed" size={16} /> Bancal extra
          </span>
          <span className="mission__progress">
            {nextPlot ? 'Un bancal más para cultivar' : 'Ya tienes todos los bancales'}
          </span>
        </div>
        {nextPlot && (
          <button className="btn btn--small" disabled={coins < nextPlot.price} onClick={onBuyPlot}>
            <PixelIcon name="coin" size={16} />
            {nextPlot.price}
          </button>
        )}
      </div>
      <h3 className="menu__heading">Muebles</h3>
      <div className="shop">
        {shop.map((item) => (
          <div key={item.kind} className="shop__item">
            <img
              className="shop__image"
              src={asset(`rooms/objects/${item.kind}.png`)}
              alt={ITEM_LABELS[item.kind as ItemKind] ?? item.kind}
            />
            <span className="shop__name">{ITEM_LABELS[item.kind as ItemKind] ?? item.kind}</span>
            <button className="btn btn--small" disabled={coins < item.price} onClick={() => onBuy(item.kind)}>
              <PixelIcon name="coin" size={16} />
              {item.price}
            </button>
          </div>
        ))}
      </div>
      {error && <p className="error">{error}</p>}
    </section>
  )
}
