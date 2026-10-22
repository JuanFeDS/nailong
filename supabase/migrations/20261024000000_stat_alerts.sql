alter table public.nailong
  add column satiety_alert smallint not null default 0,
  add column happiness_alert smallint not null default 0,
  add column energy_alert smallint not null default 0;

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
      public.night_hours(n.last_updated_at, now()) as asleep_hours
    from public.nailong n
  )
  select
    least(100, greatest(0, e.satiety - 4 * (e.total_hours - e.asleep_hours) - 1.5 * e.asleep_hours)),
    least(100, greatest(0, e.happiness - 4 * (e.total_hours - e.asleep_hours) - 1.5 * e.asleep_hours)),
    least(100, greatest(0, e.energy - 3 * (e.total_hours - e.asleep_hours) + 7 * e.asleep_hours)),
    public.is_sleeping(),
    e.status,
    e.current_home,
    e.satiety_alert,
    e.happiness_alert,
    e.energy_alert
  from elapsed e
$$;

revoke all on function public.current_stats() from public, anon, authenticated;
grant execute on function public.current_stats() to service_role;
