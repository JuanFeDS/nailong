alter table public.nailong
  add column status text not null default 'home' check (status in ('home', 'traveling')),
  add column arrives_at timestamptz,
  add column last_entered_at timestamptz;

update public.nailong set last_entered_at = last_sent_at where id;

create or replace function public.do_action(action text) returns public.nailong
language plpgsql security definer set search_path = public as $$
declare
  row_nailong public.nailong;
begin
  row_nailong := public.apply_decay();

  if row_nailong.status <> 'home' or row_nailong.current_home is distinct from auth.uid() then
    raise exception 'Nailong no está en tu casa';
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

create function public.let_in() returns public.nailong
language plpgsql security definer set search_path = public as $$
declare
  row_nailong public.nailong;
begin
  row_nailong := public.apply_decay();

  if row_nailong.status <> 'traveling' or row_nailong.current_home is distinct from auth.uid() then
    raise exception 'Nailong no está esperando en tu puerta';
  end if;

  if now() < row_nailong.arrives_at then
    raise exception 'Nailong aún no ha llegado';
  end if;

  update public.nailong set status = 'home', arrives_at = null, last_entered_at = now()
  where id
  returning * into row_nailong;

  return row_nailong;
end;
$$;

revoke all on function public.let_in() from public, anon;
grant execute on function public.let_in() to authenticated;
