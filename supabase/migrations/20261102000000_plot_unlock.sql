alter table public.garden_plots add column unlocked boolean not null default false;

update public.garden_plots set unlocked = true where slot = 0 or stage <> 'empty';

create or replace function public.garden_status() returns jsonb
language plpgsql security definer set search_path = public as $$
begin
  update public.garden_plots set
    stage = 'wilted', waterings = 0, planted_at = null, last_watered_at = null
  where house_id = auth.uid()
    and stage in ('sprout', 'growing')
    and coalesce(last_watered_at, planted_at) < now() - interval '36 hours';

  return coalesce((
    select jsonb_agg(
      jsonb_build_object(
        'slot', slot,
        'unlocked', unlocked,
        'unlock_price', case slot when 1 then 60 else 120 end,
        'stage', stage,
        'waterings', waterings,
        'next_water_at', case when stage in ('sprout', 'growing') and last_watered_at is not null
                              then last_watered_at + interval '2 hours' end,
        'withers_at', case when stage in ('sprout', 'growing')
                           then coalesce(last_watered_at, planted_at) + interval '36 hours' end
      ) order by slot
    )
    from public.garden_plots where house_id = auth.uid()
  ), '[]'::jsonb);
end;
$$;

create or replace function public.plant_seed(plot_slot integer) returns jsonb
language plpgsql security definer set search_path = public as $$
begin
  perform public.garden_status();

  update public.garden_plots set
    stage = 'sprout', waterings = 0, planted_at = now(), last_watered_at = null
  where house_id = auth.uid() and slot = plot_slot and stage = 'empty' and unlocked;
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

create function public.buy_plot() returns jsonb
language plpgsql security definer set search_path = public as $$
declare
  next_slot smallint;
  price integer;
begin
  select slot into next_slot from public.garden_plots
  where house_id = auth.uid() and not unlocked
  order by slot limit 1;
  if next_slot is null then
    raise exception 'Ya tienes todos los bancales';
  end if;

  price := case next_slot when 1 then 60 else 120 end;

  update public.profiles set coins = coins - price where id = auth.uid() and coins >= price;
  if not found then
    raise exception 'No tienes suficientes monedas';
  end if;

  update public.garden_plots set unlocked = true where house_id = auth.uid() and slot = next_slot;

  return public.garden_status();
end;
$$;

revoke all on function public.buy_plot() from public, anon;
grant execute on function public.buy_plot() to authenticated;
