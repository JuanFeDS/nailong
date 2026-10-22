alter table public.nailong
  drop constraint nailong_status_check,
  add constraint nailong_status_check check (status in ('home', 'traveling', 'lost')),
  add column trip_times timestamptz[] not null default '{}';

update public.nailong set
  trip_times = case
    when last_sent_at is not null and last_sent_at > now() - interval '24 hours' then array[last_sent_at]
    else '{}'
  end
where id;

create or replace function public.travel_factor(trips timestamptz[]) returns numeric
language sql stable set search_path = public as $$
  select case
    when count(*) >= 5 then 2
    when count(*) >= 3 then 1.5
    else 1
  end
  from unnest(trips) as trip_time
  where trip_time > now() - interval '24 hours'
$$;

create or replace function public.apply_decay() returns public.nailong
language plpgsql security definer set search_path = public as $$
declare
  row_nailong public.nailong;
  total_hours numeric;
  asleep_hours numeric;
  awake_hours numeric;
  tiredness numeric;
begin
  select * into row_nailong from public.nailong for update;
  total_hours := extract(epoch from (now() - row_nailong.last_updated_at)) / 3600;
  asleep_hours := public.night_hours(row_nailong.last_updated_at, now());
  awake_hours := total_hours - asleep_hours;
  tiredness := public.travel_factor(row_nailong.trip_times);

  update public.nailong set
    satiety = least(100, greatest(0, satiety - 4 * tiredness * awake_hours - 1.5 * asleep_hours)),
    happiness = least(100, greatest(0, happiness - 4 * tiredness * awake_hours - 1.5 * asleep_hours)),
    energy = least(100, greatest(0, energy - 3 * tiredness * awake_hours + 7 * asleep_hours)),
    last_updated_at = now()
  where id
  returning * into row_nailong;

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

  select id into other_user from public.profiles where id <> auth.uid();
  if other_user is null then
    raise exception 'Falta el segundo usuario';
  end if;

  update public.nailong set
    current_home = other_user,
    status = 'traveling',
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

create or replace function public.current_stats()
returns table (
  satiety numeric,
  happiness numeric,
  energy numeric,
  sleeping boolean,
  status text,
  current_home uuid,
  satiety_alert smallint,
  happiness_alert smallint,
  energy_alert smallint
)
language sql stable security definer set search_path = public as $$
  with elapsed as (
    select
      n.*,
      extract(epoch from (now() - n.last_updated_at)) / 3600 as total_hours,
      public.night_hours(n.last_updated_at, now()) as asleep_hours,
      public.travel_factor(n.trip_times) as tiredness
    from public.nailong n
  )
  select
    least(100, greatest(0, e.satiety - 4 * e.tiredness * (e.total_hours - e.asleep_hours) - 1.5 * e.asleep_hours)),
    least(100, greatest(0, e.happiness - 4 * e.tiredness * (e.total_hours - e.asleep_hours) - 1.5 * e.asleep_hours)),
    least(100, greatest(0, e.energy - 3 * e.tiredness * (e.total_hours - e.asleep_hours) + 7 * e.asleep_hours)),
    public.is_sleeping(),
    e.status,
    e.current_home,
    e.satiety_alert,
    e.happiness_alert,
    e.energy_alert
  from elapsed e
$$;

create or replace function public.run_escape_check() returns jsonb
language plpgsql security definer set search_path = public as $$
declare
  row_nailong public.nailong;
  current_happiness numeric;
  result jsonb := jsonb_build_object('escaped', false, 'returned', false);
begin
  select * into row_nailong from public.nailong;

  if row_nailong.status = 'lost' then
    if now() >= row_nailong.arrives_at then
      perform public.apply_decay();
      update public.nailong set
        status = 'home',
        arrives_at = null,
        happiness = 40,
        happiness_alert = 0,
        last_entered_at = now()
      where id
      returning * into row_nailong;
      result := jsonb_build_object('escaped', false, 'returned', true, 'home', row_nailong.current_home);
    end if;
  elsif row_nailong.status = 'home'
        and not public.is_sleeping()
        and coalesce(row_nailong.last_entered_at, row_nailong.last_updated_at) + interval '3 days' <= now() then
    select happiness into current_happiness from public.current_stats();
    if current_happiness < 30 and random() < 0.00139 then
      perform public.apply_decay();
      update public.nailong set
        status = 'lost',
        arrives_at = now() + interval '2 hours' + random() * interval '2 hours'
      where id
      returning * into row_nailong;
      result := jsonb_build_object('escaped', true, 'returned', false, 'home', row_nailong.current_home);
    end if;
  end if;

  return result;
end;
$$;

revoke all on function public.travel_factor(timestamptz[]) from public, anon, authenticated;
revoke all on function public.run_escape_check() from public, anon, authenticated;
grant execute on function public.run_escape_check() to service_role;
