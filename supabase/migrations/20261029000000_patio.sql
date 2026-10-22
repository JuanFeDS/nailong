alter table public.house_items
  add column place text not null default 'room' check (place in ('room', 'patio'));

alter table public.nailong
  add column place text not null default 'room' check (place in ('room', 'patio'));

alter table public.house_items drop constraint house_items_kind_check;
alter table public.house_items add constraint house_items_kind_check check (kind in (
  'bed', 'bowl', 'ball', 'door', 'rug', 'plant',
  'bookshelf', 'clock', 'wallshelf', 'toybox', 'armchair', 'sidetable', 'pouf', 'frame',
  'lamp', 'fishtank', 'desk', 'guitar', 'cactus', 'wardrobe', 'poster', 'mirror',
  'backdoor', 'gate', 'swing', 'goal', 'soccerball', 'plot_empty', 'plot_sprout', 'plot_ripe'
));

insert into public.house_items (house_id, kind, x, y, place)
select id, 'backdoor', 60, 156, 'room' from public.profiles;

insert into public.house_items (house_id, kind, x, y, place)
select id, 'gate', 320, 180, 'patio' from public.profiles;

create function public.set_place(new_place text) returns public.nailong
language plpgsql security definer set search_path = public as $$
declare
  row_nailong public.nailong;
begin
  if new_place not in ('room', 'patio') then
    raise exception 'Lugar desconocido';
  end if;

  row_nailong := public.apply_decay();

  if row_nailong.status <> 'home' or row_nailong.current_home is distinct from auth.uid() then
    raise exception 'Nailong no está en tu casa';
  end if;

  if new_place = 'patio' and public.is_sleeping() then
    raise exception 'Nailong está durmiendo';
  end if;

  update public.nailong set place = new_place where id returning * into row_nailong;
  return row_nailong;
end;
$$;

revoke all on function public.set_place(text) from public, anon;
grant execute on function public.set_place(text) to authenticated;

create or replace function public.send_nailong() returns public.nailong
language plpgsql security definer set search_path = public as $$
declare
  row_nailong public.nailong;
  other_user uuid;
begin
  row_nailong := public.apply_decay();

  if row_nailong.status <> 'home' or row_nailong.current_home is distinct from auth.uid() then
    raise exception 'Nailong no está en tu casa';
  end if;

  if public.is_sleeping() then
    raise exception 'Nailong está durmiendo';
  end if;

  select id into other_user from public.profiles where id <> auth.uid();
  if other_user is null then
    raise exception 'Falta el segundo usuario';
  end if;

  update public.nailong set
    current_home = other_user,
    status = 'traveling',
    place = 'room',
    arrives_at = now() + interval '5 minutes' + random() * interval '5 minutes',
    last_sent_at = now(),
    trip_times = array_append(
      array(select trip_time from unnest(trip_times) as trip_time where trip_time > now() - interval '24 hours'),
      now()
    )
  where id
  returning * into row_nailong;

  return row_nailong;
end;
$$;

create or replace function public.run_escape_check() returns jsonb
language plpgsql security definer set search_path = public as $$
declare
  row_nailong public.nailong;
  current_happiness numeric;
  house_coins integer;
  stolen integer;
  refund integer;
  result jsonb := jsonb_build_object('escaped', false, 'returned', false);
begin
  select * into row_nailong from public.nailong;

  if row_nailong.status = 'home' and row_nailong.place = 'patio' and public.is_sleeping() then
    update public.nailong set place = 'room' where id;
  end if;

  if row_nailong.status = 'lost' then
    if now() >= row_nailong.arrives_at then
      perform public.apply_decay();
      refund := row_nailong.stolen_coins / 2;
      update public.profiles set coins = coins + refund where id = row_nailong.current_home;
      update public.nailong set
        status = 'home',
        place = 'room',
        arrives_at = null,
        happiness = 40,
        happiness_alert = 0,
        last_entered_at = now(),
        stolen_coins = 0
      where id
      returning * into row_nailong;
      result := jsonb_build_object(
        'escaped', false, 'returned', true, 'home', row_nailong.current_home, 'refund', refund
      );
    end if;
  elsif row_nailong.status = 'home'
        and not public.is_sleeping()
        and coalesce(row_nailong.last_entered_at, row_nailong.last_updated_at) + interval '3 days' <= now() then
    select happiness into current_happiness from public.current_stats();
    if current_happiness < 30 and random() < 0.00139 then
      perform public.apply_decay();
      select coins into house_coins from public.profiles where id = row_nailong.current_home;
      stolen := least(house_coins, least(60, greatest(10, floor(house_coins * 0.2)::integer)));
      update public.profiles set coins = coins - stolen where id = row_nailong.current_home;
      update public.nailong set
        status = 'lost',
        arrives_at = now() + interval '2 hours' + random() * interval '2 hours',
        stolen_coins = stolen
      where id
      returning * into row_nailong;
      result := jsonb_build_object(
        'escaped', true, 'returned', false, 'home', row_nailong.current_home, 'stolen', stolen
      );
    end if;
  end if;

  return result;
end;
$$;
