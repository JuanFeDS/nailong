create or replace function public.is_sleeping() returns boolean
language sql stable set search_path = public as $$
  select (now() at time zone 'America/Bogota')::time >= time '22:30'
      or (now() at time zone 'America/Bogota')::time < time '08:00'
$$;

create or replace function public.night_hours(from_ts timestamptz, to_ts timestamptz) returns numeric
language sql stable set search_path = public as $$
  select coalesce(sum(extract(epoch from (least(to_ts, window_end) - greatest(from_ts, window_start))) / 3600), 0)
  from (
    select
      (day::timestamp + time '22:30') at time zone 'America/Bogota' as window_start,
      ((day::timestamp + interval '1 day') + time '08:00') at time zone 'America/Bogota' as window_end
    from generate_series(
      (from_ts at time zone 'America/Bogota')::date - 1,
      (to_ts at time zone 'America/Bogota')::date,
      interval '1 day'
    ) as day
  ) windows
  where least(to_ts, window_end) > greatest(from_ts, window_start)
$$;

create or replace function public.apply_decay() returns public.nailong
language plpgsql security definer set search_path = public as $$
declare
  row_nailong public.nailong;
  total_hours numeric;
  asleep_hours numeric;
  awake_hours numeric;
begin
  select * into row_nailong from public.nailong for update;
  total_hours := extract(epoch from (now() - row_nailong.last_updated_at)) / 3600;
  asleep_hours := public.night_hours(row_nailong.last_updated_at, now());
  awake_hours := total_hours - asleep_hours;

  update public.nailong set
    satiety = least(100, greatest(0, satiety - 4 * awake_hours - 1.5 * asleep_hours)),
    happiness = least(100, greatest(0, happiness - 4 * awake_hours - 1.5 * asleep_hours)),
    energy = least(100, greatest(0, energy - 3 * awake_hours + 7 * asleep_hours)),
    last_updated_at = now()
  where id
  returning * into row_nailong;

  return row_nailong;
end;
$$;

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

  if action = 'feed' then
    update public.nailong set satiety = least(100, satiety + 30) where id;
  elsif action = 'play' then
    update public.nailong set
      happiness = least(100, happiness + 25),
      energy = greatest(0, energy - 10),
      satiety = greatest(0, satiety - 5)
    where id;
  elsif action = 'sleep' then
    update public.nailong set energy = least(100, energy + 40) where id;
  else
    raise exception 'Acción desconocida: %', action;
  end if;

  select * into row_nailong from public.nailong;
  return row_nailong;
end;
$$;

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

  if row_nailong.last_entered_at is not null
     and row_nailong.last_entered_at + interval '3 days' > now() then
    raise exception 'Aún no puedes enviarlo: cooldown de 3 días';
  end if;

  select id into other_user from public.profiles where id <> auth.uid();
  if other_user is null then
    raise exception 'Falta el segundo usuario';
  end if;

  update public.nailong set
    current_home = other_user,
    status = 'traveling',
    arrives_at = now() + interval '5 minutes' + random() * interval '5 minutes',
    last_sent_at = now()
  where id
  returning * into row_nailong;

  return row_nailong;
end;
$$;

revoke all on function public.is_sleeping() from public, anon, authenticated;
revoke all on function public.night_hours(timestamptz, timestamptz) from public, anon, authenticated;
