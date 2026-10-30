-- Ajuste de la economía: unas 60-80 monedas al día en vez de 100-300.
update public.food_catalog set sell_price = 8 where kind = 'tomato';

update public.shop_items set price = new_prices.price
from (values
  ('cushions', 80),
  ('hangingplant', 100),
  ('painting', 120),
  ('lamp', 140),
  ('bigplant', 160),
  ('coffeetable', 180),
  ('desk', 250),
  ('fishtank', 280),
  ('tv', 320),
  ('wardrobe', 350),
  ('sofa', 400),
  ('flowerpots', 90),
  ('birdbath', 170),
  ('lamppost', 200),
  ('bench', 230)
) as new_prices (kind, price)
where public.shop_items.kind = new_prices.kind;

create or replace function public.grant_coins(target uuid, amount integer) returns integer
language plpgsql security definer set search_path = public as $$
declare
  today date := public.bogota_today();
  granted integer;
begin
  update public.profiles set
    earned_today = case when earned_day is not distinct from today then earned_today else 0 end,
    earned_day = today
  where id = target;

  select least(amount, greatest(0, 30 - earned_today)) into granted
  from public.profiles where id = target;

  update public.profiles set
    coins = coins + granted,
    earned_today = earned_today + granted
  where id = target;

  return granted;
end;
$$;

create or replace function public.claim_mission(mission text) returns jsonb
language plpgsql security definer set search_path = public as $$
declare
  today date := public.bogota_today();
  progress public.daily_progress;
  row_nailong public.nailong;
  reward integer := 10;
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
    reward := reward + 10;
  end if;

  update public.daily_progress set claimed = array_append(claimed, mission)
  where user_id = auth.uid() and day = today;

  update public.profiles set coins = coins + reward where id = auth.uid();

  return public.wallet_status();
end;
$$;

create or replace function public.finish_minigame(game text, level integer, score integer) returns integer
language plpgsql security definer set search_path = public as $$
declare
  today date := public.bogota_today();
  divisor integer;
  max_score integer;
  already integer;
  wanted integer;
  granted integer;
  row_nailong public.nailong;
begin
  if game = 'ghosts' then
    divisor := 5; max_score := 300;
  elsif game = 'catch' then
    divisor := 6; max_score := 400;
  elsif game = 'memory' then
    divisor := 2; max_score := 80;
  else
    raise exception 'Minijuego desconocido: %', game;
  end if;

  if level is null or level not between 1 and 3 then
    raise exception 'Nivel inválido: %', level;
  end if;

  insert into public.daily_progress (user_id, day) values (auth.uid(), today)
  on conflict (user_id, day) do nothing;

  select minigame_coins into already from public.daily_progress
  where user_id = auth.uid() and day = today;

  -- Tope propio de 15 al día; grant_coins aplica además el de 30 de toda la economía.
  wanted := least(10, ceil(least(greatest(score, 0), max_score) * level / divisor::numeric)::integer, greatest(0, 15 - already));
  granted := case when wanted > 0 then public.grant_coins(auth.uid(), wanted) else 0 end;

  update public.daily_progress set minigame_coins = minigame_coins + granted
  where user_id = auth.uid() and day = today;

  -- Sin raise: si Nailong no está en casa o duerme, las monedas se dan igual.
  row_nailong := public.apply_decay();
  if score > 0 and row_nailong.status = 'home' and row_nailong.current_home = auth.uid() and not public.is_sleeping() then
    update public.nailong set happiness = least(100, happiness + 10) where id;
  end if;

  return granted;
end;
$$;
