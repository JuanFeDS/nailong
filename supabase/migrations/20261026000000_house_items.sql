create table public.house_items (
  id uuid primary key default gen_random_uuid(),
  house_id uuid not null references public.profiles(id) on delete cascade,
  kind text not null check (kind in (
    'bed', 'bowl', 'ball', 'door', 'rug', 'plant',
    'bookshelf', 'clock', 'wallshelf', 'toybox', 'armchair', 'sidetable', 'pouf'
  )),
  x smallint not null,
  y smallint not null
);

create index house_items_house_id_idx on public.house_items (house_id);

alter table public.house_items enable row level security;

create policy "ver los objetos de mi casa" on public.house_items
  for select to authenticated
  using (house_id = (select auth.uid()));

insert into public.house_items (house_id, kind, x, y)
select profile.id, layout.kind, layout.x, layout.y
from public.profiles profile
cross join (values
  ('rug', 360, 300),
  ('clock', 200, 86),
  ('wallshelf', 385, 100),
  ('bookshelf', 480, 168),
  ('sidetable', 200, 190),
  ('pouf', 470, 270),
  ('armchair', 585, 305),
  ('toybox', 200, 336),
  ('plant', 44, 340),
  ('bed', 100, 236),
  ('bowl', 500, 330),
  ('ball', 300, 344),
  ('door', 582, 156)
) as layout (kind, x, y);

create function public.move_item(item_id uuid, new_x integer, new_y integer) returns public.house_items
language plpgsql security definer set search_path = public as $$
declare
  moved public.house_items;
begin
  if new_x not between 0 and 640 or new_y not between 0 and 360 then
    raise exception 'Posición fuera de la habitación';
  end if;

  update public.house_items set x = new_x, y = new_y
  where id = item_id and house_id = auth.uid()
  returning * into moved;

  if moved.id is null then
    raise exception 'Ese objeto no está en tu casa';
  end if;

  return moved;
end;
$$;

revoke all on function public.move_item(uuid, integer, integer) from public, anon;
grant execute on function public.move_item(uuid, integer, integer) to authenticated;
