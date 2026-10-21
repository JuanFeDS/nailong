alter table public.nailong
  add column arrival_notified boolean not null default true;

create table public.push_subscriptions (
  endpoint text primary key,
  user_id uuid not null references public.profiles (id) on delete cascade,
  p256dh text not null,
  auth text not null,
  created_at timestamptz not null default now()
);

alter table public.push_subscriptions enable row level security;

create policy "push_select_own" on public.push_subscriptions
  for select to authenticated using (user_id = auth.uid());

create policy "push_insert_own" on public.push_subscriptions
  for insert to authenticated with check (user_id = auth.uid());

create policy "push_update_own" on public.push_subscriptions
  for update to authenticated using (user_id = auth.uid()) with check (user_id = auth.uid());

create policy "push_delete_own" on public.push_subscriptions
  for delete to authenticated using (user_id = auth.uid());

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
    arrival_notified = false,
    last_sent_at = now()
  where id
  returning * into row_nailong;

  return row_nailong;
end;
$$;

create extension if not exists pg_cron;
create extension if not exists pg_net;

-- Sustituye REEMPLAZA_CON_CRON_SECRET por el valor de CRON_SECRET (mismo que en los secretos de la función).
select cron.schedule(
  'notify-arrivals',
  '* * * * *',
  $$
  select net.http_post(
    url := 'https://fvsldnxmwukmrtuzukpa.supabase.co/functions/v1/notify-arrivals',
    headers := jsonb_build_object('Content-Type', 'application/json', 'x-cron-secret', 'REEMPLAZA_CON_CRON_SECRET'),
    body := '{}'::jsonb
  )
  $$
);
