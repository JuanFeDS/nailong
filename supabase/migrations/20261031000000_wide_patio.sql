create or replace function public.move_item(item_id uuid, new_x integer, new_y integer) returns public.house_items
language plpgsql security definer set search_path = public as $$
declare
  moved public.house_items;
begin
  if new_x not between 0 and 1000 or new_y not between 0 and 360 then
    raise exception 'Posición fuera del lugar';
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

update public.house_items set x = 476 where kind = 'gate' and place = 'patio' and x = 320;
