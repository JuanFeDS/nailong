insert into public.house_items (house_id, kind, x, y, place)
select id, 'swing', 170, 285, 'patio' from public.profiles;

create or replace function public.do_action(action text) returns public.nailong
language plpgsql security definer set search_path = public as $$
declare
  row_nailong public.nailong;
begin
  row_nailong := public.apply_decay();

  if row_nailong.status <> 'home' or row_nailong.current_home is distinct from auth.uid() then
    raise exception 'Nailong no está en tu casa';
  end if;

  if public.is_sleeping() then
    raise exception 'Nailong está durmiendo';
  end if;

  if action = 'play' then
    update public.nailong set
      happiness = least(100, happiness + 25),
      energy = greatest(0, energy - 10),
      satiety = greatest(0, satiety - 5)
    where id;
  elsif action = 'swing' then
    if row_nailong.place <> 'patio' then
      raise exception 'El columpio está en el patio';
    end if;
    update public.nailong set
      happiness = least(100, happiness + 20),
      energy = greatest(0, energy - 5)
    where id;
  elsif action = 'sleep' then
    update public.nailong set energy = least(100, energy + 40) where id;
  else
    raise exception 'Acción desconocida: %', action;
  end if;

  perform public.grant_coins(auth.uid(), 5);

  if action in ('play', 'swing') then
    insert into public.daily_progress (user_id, day, plays)
    values (auth.uid(), public.bogota_today(), 1)
    on conflict (user_id, day) do update set plays = public.daily_progress.plays + 1;
  end if;

  select * into row_nailong from public.nailong;
  return row_nailong;
end;
$$;
