alter table public.profiles add column last_ration_at timestamptz;

create table public.food_catalog (
  kind text primary key,
  price integer check (price > 0),
  satiety integer not null check (satiety > 0),
  sell_price integer check (sell_price > 0)
);

alter table public.food_catalog enable row level security;

create policy "ver el catálogo de comida" on public.food_catalog
  for select to authenticated using (true);

insert into public.food_catalog (kind, price, satiety, sell_price) values
  ('bread', 6, 15, null),
  ('meal', 14, 30, null),
  ('tomato', null, 40, 25);

create table public.pantry (
  house_id uuid not null references public.profiles(id) on delete cascade,
  kind text not null references public.food_catalog(kind),
  qty integer not null default 0 check (qty >= 0),
  primary key (house_id, kind)
);

alter table public.pantry enable row level security;

create policy "ver mi despensa" on public.pantry
  for select to authenticated using (house_id = (select auth.uid()));

create table public.garden_plots (
  house_id uuid not null references public.profiles(id) on delete cascade,
  slot smallint not null check (slot between 0 and 2),
  stage text not null default 'empty' check (stage in ('empty', 'sprout', 'ripe')),
  waterings smallint not null default 0,
  planted_at timestamptz,
  last_watered_at timestamptz,
  primary key (house_id, slot)
);

alter table public.garden_plots enable row level security;

insert into public.garden_plots (house_id, slot)
select profile.id, slot from public.profiles profile, generate_series(0, 2) as slot;

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

  if action = 'play' then
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

  if action = 'play' then
    insert into public.daily_progress (user_id, day, plays)
    values (auth.uid(), public.bogota_today(), 1)
    on conflict (user_id, day) do update set plays = public.daily_progress.plays + 1;
  end if;

  select * into row_nailong from public.nailong;
  return row_nailong;
end;
$$;

create function public.pantry_status() returns jsonb
language plpgsql security definer set search_path = public as $$
declare
  total integer;
  last_ration timestamptz;
begin
  select coalesce(sum(qty), 0) into total from public.pantry where house_id = auth.uid();
  select last_ration_at into last_ration from public.profiles where id = auth.uid();

  return jsonb_build_object(
    'items', coalesce((select jsonb_object_agg(kind, qty) from public.pantry where house_id = auth.uid() and qty > 0), '{}'::jsonb),
    'ration_ready', total = 0 and (last_ration is null or now() >= last_ration + interval '8 hours'),
    'ration_at', case when total = 0 and last_ration is not null and now() < last_ration + interval '8 hours'
                      then last_ration + interval '8 hours' end
  );
end;
$$;

create function public.buy_food(food text) returns jsonb
language plpgsql security definer set search_path = public as $$
declare
  food_price integer;
begin
  select price into food_price from public.food_catalog where kind = food;
  if food_price is null then
    raise exception 'Esa comida no está en la tienda';
  end if;

  update public.profiles set coins = coins - food_price
  where id = auth.uid() and coins >= food_price;
  if not found then
    raise exception 'No tienes suficientes monedas';
  end if;

  insert into public.pantry (house_id, kind, qty) values (auth.uid(), food, 1)
  on conflict (house_id, kind) do update set qty = public.pantry.qty + 1;

  return public.pantry_status();
end;
$$;

create function public.feed_nailong(food text) returns public.nailong
language plpgsql security definer set search_path = public as $$
declare
  row_nailong public.nailong;
  food_satiety integer;
  total integer;
  last_ration timestamptz;
begin
  row_nailong := public.apply_decay();

  if row_nailong.status <> 'home' or row_nailong.current_home is distinct from auth.uid() then
    raise exception 'Nailong no está en tu casa';
  end if;

  if public.is_sleeping() then
    raise exception 'Nailong está durmiendo';
  end if;

  if food = 'ration' then
    select coalesce(sum(qty), 0) into total from public.pantry where house_id = auth.uid();
    select last_ration_at into last_ration from public.profiles where id = auth.uid();
    if total > 0 or (last_ration is not null and now() < last_ration + interval '8 hours') then
      raise exception 'La ración de emergencia no está disponible';
    end if;
    update public.profiles set last_ration_at = now() where id = auth.uid();
    food_satiety := 10;
  else
    select satiety into food_satiety from public.food_catalog where kind = food;
    if food_satiety is null then
      raise exception 'Comida desconocida';
    end if;
    update public.pantry set qty = qty - 1 where house_id = auth.uid() and kind = food and qty > 0;
    if not found then
      raise exception 'No te queda de eso en la despensa';
    end if;
  end if;

  update public.nailong set satiety = least(100, satiety + food_satiety) where id;

  perform public.grant_coins(auth.uid(), 5);

  insert into public.daily_progress (user_id, day, feeds)
  values (auth.uid(), public.bogota_today(), 1)
  on conflict (user_id, day) do update set feeds = public.daily_progress.feeds + 1;

  select * into row_nailong from public.nailong;
  return row_nailong;
end;
$$;

create function public.garden_status() returns jsonb
language plpgsql security definer set search_path = public as $$
begin
  update public.garden_plots set
    stage = 'empty', waterings = 0, planted_at = null, last_watered_at = null
  where house_id = auth.uid()
    and stage = 'sprout'
    and coalesce(last_watered_at, planted_at) < now() - interval '36 hours';

  return coalesce((
    select jsonb_agg(
      jsonb_build_object(
        'slot', slot,
        'stage', stage,
        'waterings', waterings,
        'next_water_at', case when stage = 'sprout' and last_watered_at is not null
                              then last_watered_at + interval '2 hours' end,
        'withers_at', case when stage = 'sprout'
                           then coalesce(last_watered_at, planted_at) + interval '36 hours' end
      ) order by slot
    )
    from public.garden_plots where house_id = auth.uid()
  ), '[]'::jsonb);
end;
$$;

create function public.plant_seed(plot_slot integer) returns jsonb
language plpgsql security definer set search_path = public as $$
begin
  perform public.garden_status();

  update public.garden_plots set
    stage = 'sprout', waterings = 0, planted_at = now(), last_watered_at = null
  where house_id = auth.uid() and slot = plot_slot and stage = 'empty';
  if not found then
    raise exception 'Ese bancal no está libre';
  end if;

  update public.profiles set coins = coins - 5 where id = auth.uid() and coins >= 5;
  if not found then
    raise exception 'No tienes suficientes monedas';
  end if;

  return public.garden_status();
end;
$$;

create function public.water_plot(plot_slot integer) returns jsonb
language plpgsql security definer set search_path = public as $$
declare
  plot public.garden_plots;
begin
  perform public.garden_status();

  select * into plot from public.garden_plots
  where house_id = auth.uid() and slot = plot_slot for update;

  if plot.stage <> 'sprout' then
    raise exception 'Ahí no hay nada que regar';
  end if;
  if plot.last_watered_at is not null and now() < plot.last_watered_at + interval '2 hours' then
    raise exception 'Todavía está húmedo';
  end if;

  update public.garden_plots set
    waterings = waterings + 1,
    last_watered_at = now(),
    stage = case when waterings + 1 >= 3 then 'ripe' else 'sprout' end
  where house_id = auth.uid() and slot = plot_slot;

  return public.garden_status();
end;
$$;

create function public.harvest_plot(plot_slot integer) returns jsonb
language plpgsql security definer set search_path = public as $$
begin
  update public.garden_plots set
    stage = 'empty', waterings = 0, planted_at = null, last_watered_at = null
  where house_id = auth.uid() and slot = plot_slot and stage = 'ripe';
  if not found then
    raise exception 'Todavía no hay nada que cosechar';
  end if;

  insert into public.pantry (house_id, kind, qty) values (auth.uid(), 'tomato', 2)
  on conflict (house_id, kind) do update set qty = public.pantry.qty + 2;

  return public.garden_status();
end;
$$;

create function public.sell_fruit(quantity integer) returns jsonb
language plpgsql security definer set search_path = public as $$
declare
  unit_price integer;
begin
  if quantity < 1 then
    raise exception 'Cantidad no válida';
  end if;

  select sell_price into unit_price from public.food_catalog where kind = 'tomato';

  update public.pantry set qty = qty - quantity
  where house_id = auth.uid() and kind = 'tomato' and qty >= quantity;
  if not found then
    raise exception 'No tienes tantos tomates';
  end if;

  update public.profiles set coins = coins + unit_price * quantity where id = auth.uid();

  return public.pantry_status();
end;
$$;

revoke all on function public.pantry_status() from public, anon;
revoke all on function public.buy_food(text) from public, anon;
revoke all on function public.feed_nailong(text) from public, anon;
revoke all on function public.garden_status() from public, anon;
revoke all on function public.plant_seed(integer) from public, anon;
revoke all on function public.water_plot(integer) from public, anon;
revoke all on function public.harvest_plot(integer) from public, anon;
revoke all on function public.sell_fruit(integer) from public, anon;
grant execute on function public.pantry_status() to authenticated;
grant execute on function public.buy_food(text) to authenticated;
grant execute on function public.feed_nailong(text) to authenticated;
grant execute on function public.garden_status() to authenticated;
grant execute on function public.plant_seed(integer) to authenticated;
grant execute on function public.water_plot(integer) to authenticated;
grant execute on function public.harvest_plot(integer) to authenticated;
grant execute on function public.sell_fruit(integer) to authenticated;
