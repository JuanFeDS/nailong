alter table public.shop_items
  add column place text not null default 'room' check (place in ('room', 'patio')),
  add column spawn_y integer not null default 250;

alter table public.house_items drop constraint house_items_kind_check;
alter table public.house_items add constraint house_items_kind_check check (kind in (
  'bed', 'bowl', 'ball', 'door', 'rug', 'plant',
  'bookshelf', 'clock', 'wallshelf', 'toybox', 'armchair', 'sidetable', 'pouf', 'frame',
  'lamp', 'fishtank', 'desk', 'guitar', 'cactus', 'wardrobe', 'poster', 'mirror',
  'backdoor', 'gate', 'swing', 'goal', 'soccerball', 'plot_empty', 'plot_sprout', 'plot_ripe',
  'sofa', 'cushions', 'coffeetable', 'tv', 'bigplant', 'painting', 'hangingplant',
  'bench', 'flowerpots', 'birdbath', 'lamppost'
));

insert into public.shop_items (kind, price, place, spawn_y) values
  ('cushions', 35, 'room', 250),
  ('hangingplant', 45, 'room', 100),
  ('painting', 55, 'room', 100),
  ('bigplant', 70, 'room', 250),
  ('coffeetable', 80, 'room', 250),
  ('tv', 140, 'room', 250),
  ('sofa', 160, 'room', 250),
  ('flowerpots', 40, 'patio', 280),
  ('birdbath', 75, 'patio', 280),
  ('lamppost', 90, 'patio', 280),
  ('bench', 100, 'patio', 280);

create or replace function public.buy_item(item_kind text) returns public.house_items
language plpgsql security definer set search_path = public as $$
declare
  item public.shop_items;
  bought public.house_items;
begin
  select * into item from public.shop_items where kind = item_kind;
  if item.kind is null then
    raise exception 'Ese objeto no está en la tienda';
  end if;

  update public.profiles set coins = coins - item.price
  where id = auth.uid() and coins >= item.price;
  if not found then
    raise exception 'No tienes suficientes monedas';
  end if;

  insert into public.house_items (house_id, kind, x, y, place)
  values (auth.uid(), item_kind, case when item.place = 'patio' then 476 else 320 end, item.spawn_y, item.place)
  returning * into bought;

  return bought;
end;
$$;
