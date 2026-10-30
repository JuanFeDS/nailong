create table public.room_catalog (
  room text primary key,
  price integer not null check (price > 0)
);

alter table public.room_catalog enable row level security;

create policy "ver los cuartos" on public.room_catalog
  for select to authenticated using (true);

insert into public.room_catalog (room, price) values
  ('bedroom', 1200),
  ('kitchen', 1500),
  ('bathroom', 1800),
  ('playroom', 2200);

create table public.house_rooms (
  house_id uuid not null references public.profiles(id) on delete cascade,
  room text not null references public.room_catalog(room),
  bought_at timestamptz not null default now(),
  primary key (house_id, room)
);

alter table public.house_rooms enable row level security;

create policy "ver mis cuartos" on public.house_rooms
  for select to authenticated using (house_id = (select auth.uid()));

alter table public.house_items drop constraint house_items_place_check;
alter table public.house_items add constraint house_items_place_check
  check (place in ('room', 'patio', 'bedroom', 'kitchen', 'bathroom', 'playroom'));

alter table public.nailong drop constraint nailong_place_check;
alter table public.nailong add constraint nailong_place_check
  check (place in ('room', 'patio', 'bedroom', 'kitchen', 'bathroom', 'playroom'));

alter table public.house_items drop constraint house_items_kind_check;
alter table public.house_items add constraint house_items_kind_check check (kind in (
  'bed', 'bowl', 'ball', 'door', 'rug', 'plant',
  'bookshelf', 'clock', 'wallshelf', 'toybox', 'armchair', 'sidetable', 'pouf', 'frame',
  'lamp', 'fishtank', 'desk', 'guitar', 'cactus', 'wardrobe', 'poster', 'mirror',
  'backdoor', 'gate', 'swing', 'goal', 'soccerball', 'plot_empty', 'plot_sprout', 'plot_ripe',
  'sofa', 'cushions', 'coffeetable', 'tv', 'bigplant', 'painting', 'hangingplant',
  'bench', 'flowerpots', 'birdbath', 'lamppost',
  'door_bedroom', 'door_kitchen', 'door_bathroom', 'door_playroom', 'exitdoor',
  'nightstand', 'fridge', 'stove', 'bathtub', 'sink', 'arcade', 'slide'
));

create function public.buy_room(room_name text) returns text
language plpgsql security definer set search_path = public as $$
declare
  room_price integer;
  door_x integer;
begin
  select price into room_price from public.room_catalog where room = room_name;
  if room_price is null then
    raise exception 'Ese cuarto no está en la tienda';
  end if;

  if exists (select 1 from public.house_rooms where house_id = auth.uid() and room = room_name) then
    raise exception 'Ya tienes ese cuarto';
  end if;

  update public.profiles set coins = coins - room_price
  where id = auth.uid() and coins >= room_price;
  if not found then
    raise exception 'No tienes suficientes monedas';
  end if;

  insert into public.house_rooms (house_id, room) values (auth.uid(), room_name);

  -- Primer hueco de la pared de la sala sin otra puerta cerca; si no hay, el usuario la mueve.
  select candidate into door_x
  from unnest(array[400, 470, 330, 540, 610, 190, 260]) with ordinality as spots (candidate, priority)
  where not exists (
    select 1 from public.house_items
    where house_id = auth.uid() and place = 'room'
      and kind in ('door', 'backdoor', 'door_bedroom', 'door_kitchen', 'door_bathroom', 'door_playroom')
      and abs(x - candidate) < 70
  )
  order by priority limit 1;

  insert into public.house_items (house_id, kind, x, y, place) values
    (auth.uid(), 'door_' || room_name, coalesce(door_x, 320), 156, 'room'),
    (auth.uid(), 'exitdoor', 560, 156, room_name);

  insert into public.house_items (house_id, kind, x, y, place)
  select auth.uid(), fixture.kind, fixture.x, fixture.y, room_name
  from (values
    ('bedroom', 'bed', 300, 262), ('bedroom', 'nightstand', 400, 236),
    ('kitchen', 'fridge', 120, 214), ('kitchen', 'stove', 230, 214),
    ('bathroom', 'bathtub', 220, 250), ('bathroom', 'sink', 400, 214),
    ('playroom', 'arcade', 150, 222), ('playroom', 'slide', 340, 266)
  ) as fixture (room, kind, x, y)
  where fixture.room = room_name;

  return room_name;
end;
$$;

create or replace function public.set_place(new_place text) returns public.nailong
language plpgsql security definer set search_path = public as $$
declare
  row_nailong public.nailong;
begin
  row_nailong := public.apply_decay();

  if row_nailong.status <> 'home' or row_nailong.current_home is distinct from auth.uid() then
    raise exception 'Nailong no está en tu casa';
  end if;

  if new_place not in ('room', 'patio') and not exists (
    select 1 from public.house_rooms where house_id = auth.uid() and room = new_place
  ) then
    raise exception 'Lugar desconocido';
  end if;

  if new_place not in ('room', 'bedroom') and public.is_sleeping() then
    raise exception 'Nailong está durmiendo';
  end if;

  update public.nailong set place = new_place where id returning * into row_nailong;
  return row_nailong;
end;
$$;

revoke all on function public.buy_room(text) from public, anon;
grant execute on function public.buy_room(text) to authenticated;
