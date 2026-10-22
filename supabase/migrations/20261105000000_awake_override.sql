alter table public.nailong add column awake_until timestamptz;

create or replace function public.is_sleeping() returns boolean
language sql stable set search_path = public as $$
  select ((now() at time zone 'America/Bogota')::time >= time '22:30'
          or (now() at time zone 'America/Bogota')::time < time '08:00')
     and not coalesce((select awake_until > now() from public.nailong), false)
$$;
