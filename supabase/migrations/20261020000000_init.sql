create table public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  display_name text not null
);

create table public.nailong (
  id boolean primary key default true check (id),
  satiety numeric not null default 80 check (satiety between 0 and 100),
  happiness numeric not null default 80 check (happiness between 0 and 100),
  energy numeric not null default 80 check (energy between 0 and 100),
  last_updated_at timestamptz not null default now(),
  current_home uuid references public.profiles (id),
  last_sent_at timestamptz
);

insert into public.nailong default values;

alter table public.profiles enable row level security;
alter table public.nailong enable row level security;

create policy "profiles_select" on public.profiles
  for select to authenticated using (true);

create policy "nailong_select" on public.nailong
  for select to authenticated using (true);

alter publication supabase_realtime add table public.nailong;

create function public.handle_new_user() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  if (select count(*) from public.profiles) >= 2 then
    raise exception 'Solo se permiten dos usuarios';
  end if;

  insert into public.profiles (id, display_name)
  values (new.id, coalesce(new.raw_user_meta_data ->> 'display_name', split_part(new.email, '@', 1)));

  update public.nailong set current_home = new.id where current_home is null;
  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

create function public.apply_decay() returns public.nailong
language plpgsql security definer set search_path = public as $$
declare
  row_nailong public.nailong;
  hours numeric;
begin
  select * into row_nailong from public.nailong for update;
  hours := extract(epoch from (now() - row_nailong.last_updated_at)) / 3600;

  update public.nailong set
    satiety = greatest(0, satiety - 4 * hours),
    happiness = greatest(0, happiness - 4 * hours),
    energy = greatest(0, energy - 3 * hours),
    last_updated_at = now()
  where id
  returning * into row_nailong;

  return row_nailong;
end;
$$;

create function public.do_action(action text) returns public.nailong
language plpgsql security definer set search_path = public as $$
declare
  row_nailong public.nailong;
begin
  row_nailong := public.apply_decay();

  if row_nailong.current_home is distinct from auth.uid() then
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

create function public.send_nailong() returns public.nailong
language plpgsql security definer set search_path = public as $$
declare
  row_nailong public.nailong;
  other_user uuid;
begin
  row_nailong := public.apply_decay();

  if row_nailong.current_home is distinct from auth.uid() then
    raise exception 'Nailong no está en tu casa';
  end if;

  if row_nailong.last_sent_at is not null
     and row_nailong.last_sent_at + interval '3 days' > now() then
    raise exception 'Aún no puedes enviarlo: cooldown de 3 días';
  end if;

  select id into other_user from public.profiles where id <> auth.uid();
  if other_user is null then
    raise exception 'Falta el segundo usuario';
  end if;

  update public.nailong set current_home = other_user, last_sent_at = now()
  where id
  returning * into row_nailong;

  return row_nailong;
end;
$$;

revoke all on function public.apply_decay() from public, anon, authenticated;
revoke all on function public.handle_new_user() from public, anon, authenticated;
revoke all on function public.do_action(text) from public, anon;
revoke all on function public.send_nailong() from public, anon;
grant execute on function public.do_action(text) to authenticated;
grant execute on function public.send_nailong() to authenticated;
