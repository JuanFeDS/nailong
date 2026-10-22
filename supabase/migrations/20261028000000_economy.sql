alter table public.profiles
  add column coins integer not null default 0 check (coins >= 0),
  add column earned_today integer not null default 0,
  add column earned_day date;

alter table public.nailong add column stolen_coins integer not null default 0;

create table public.daily_progress (
  user_id uuid not null references public.profiles(id) on delete cascade,
  day date not null,
  feeds integer not null default 0,
  plays integer not null default 0,
  claimed text[] not null default '{}',
  primary key (user_id, day)
);

alter table public.daily_progress enable row level security;

create table public.shop_items (
  kind text primary key,
  price integer not null check (price > 0)
);

alter table public.shop_items enable row level security;

create policy "ver la tienda" on public.shop_items
  for select to authenticated using (true);

insert into public.shop_items (kind, price) values
  ('lamp', 60),
  ('desk', 110),
  ('fishtank', 120),
  ('wardrobe', 150);

alter table public.house_items drop constraint house_items_kind_check;
alter table public.house_items add constraint house_items_kind_check check (kind in (
  'bed', 'bowl', 'ball', 'door', 'rug', 'plant',
  'bookshelf', 'clock', 'wallshelf', 'toybox', 'armchair', 'sidetable', 'pouf', 'frame',
  'lamp', 'fishtank', 'desk', 'guitar', 'cactus', 'wardrobe', 'poster', 'mirror'
));

create function public.bogota_today() returns date
language sql stable set search_path = public as $$
  select (now() at time zone 'America/Bogota')::date
$$;

create function public.grant_coins(target uuid, amount integer) returns integer
language plpgsql security definer set search_path = public as $$
declare
  today date := public.bogota_today();
  granted integer;
begin
  update public.profiles set
    earned_today = case when earned_day is not distinct from today then earned_today else 0 end,
    earned_day = today
  where id = target;

  select least(amount, greatest(0, 40 - earned_today)) into granted
  from public.profiles where id = target;

  update public.profiles set
    coins = coins + granted,
    earned_today = earned_today + granted
  where id = target;

  return granted;
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

  perform public.grant_coins(auth.uid(), 5);

  if action in ('feed', 'play') then
    insert into public.daily_progress (user_id, day, feeds, plays)
    values (auth.uid(), public.bogota_today(), (action = 'feed')::integer, (action = 'play')::integer)
    on conflict (user_id, day) do update set
      feeds = public.daily_progress.feeds + excluded.feeds,
      plays = public.daily_progress.plays + excluded.plays;
  end if;

  select * into row_nailong from public.nailong;
  return row_nailong;
end;
$$;

create function public.wallet_status() returns jsonb
language plpgsql security definer set search_path = public as $$
declare
  today date := public.bogota_today();
  wallet public.profiles;
  progress public.daily_progress;
begin
  select * into wallet from public.profiles where id = auth.uid();
  select * into progress from public.daily_progress where user_id = auth.uid() and day = today;

  return jsonb_build_object(
    'coins', wallet.coins,
    'earned_today', case when wallet.earned_day = today then wallet.earned_today else 0 end,
    'feeds', coalesce(progress.feeds, 0),
    'plays', coalesce(progress.plays, 0),
    'claimed', to_jsonb(coalesce(progress.claimed, '{}'::text[]))
  );
end;
$$;

create function public.claim_mission(mission text) returns jsonb
language plpgsql security definer set search_path = public as $$
declare
  today date := public.bogota_today();
  progress public.daily_progress;
  row_nailong public.nailong;
  reward integer := 15;
begin
  if mission not in ('feed', 'play', 'care') then
    raise exception 'Misión desconocida';
  end if;

  insert into public.daily_progress (user_id, day) values (auth.uid(), today)
  on conflict (user_id, day) do nothing;

  select * into progress from public.daily_progress
  where user_id = auth.uid() and day = today for update;

  if mission = any (progress.claimed) then
    raise exception 'Esa misión ya está reclamada';
  end if;

  if mission = 'feed' and progress.feeds < 2 then
    raise exception 'Aún no has completado esa misión';
  elsif mission = 'play' and progress.plays < 1 then
    raise exception 'Aún no has completado esa misión';
  elsif mission = 'care' then
    row_nailong := public.apply_decay();
    if least(row_nailong.satiety, row_nailong.happiness, row_nailong.energy) <= 50 then
      raise exception 'Aún no has completado esa misión';
    end if;
  end if;

  if cardinality(progress.claimed) + 1 = 3 then
    reward := reward + 20;
  end if;

  update public.daily_progress set claimed = array_append(claimed, mission)
  where user_id = auth.uid() and day = today;

  update public.profiles set coins = coins + reward where id = auth.uid();

  return public.wallet_status();
end;
$$;

create function public.buy_item(item_kind text) returns public.house_items
language plpgsql security definer set search_path = public as $$
declare
  item_price integer;
  bought public.house_items;
begin
  select price into item_price from public.shop_items where kind = item_kind;
  if item_price is null then
    raise exception 'Ese objeto no está en la tienda';
  end if;

  update public.profiles set coins = coins - item_price
  where id = auth.uid() and coins >= item_price;
  if not found then
    raise exception 'No tienes suficientes monedas';
  end if;

  insert into public.house_items (house_id, kind, x, y)
  values (auth.uid(), item_kind, 320, 250)
  returning * into bought;

  return bought;
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

  if row_nailong.status = 'lost' then
    if now() >= row_nailong.arrives_at then
      perform public.apply_decay();
      refund := row_nailong.stolen_coins / 2;
      update public.profiles set coins = coins + refund where id = row_nailong.current_home;
      update public.nailong set
        status = 'home',
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

revoke all on function public.bogota_today() from public, anon, authenticated;
revoke all on function public.grant_coins(uuid, integer) from public, anon, authenticated;
revoke all on function public.wallet_status() from public, anon;
revoke all on function public.claim_mission(text) from public, anon;
revoke all on function public.buy_item(text) from public, anon;
grant execute on function public.wallet_status() to authenticated;
grant execute on function public.claim_mission(text) to authenticated;
grant execute on function public.buy_item(text) to authenticated;
