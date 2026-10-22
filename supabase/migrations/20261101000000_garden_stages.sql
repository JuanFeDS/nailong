alter table public.garden_plots drop constraint garden_plots_stage_check;
alter table public.garden_plots add constraint garden_plots_stage_check
  check (stage in ('empty', 'sprout', 'growing', 'ripe', 'wilted'));

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

create or replace function public.water_plot(plot_slot integer) returns jsonb
language plpgsql security definer set search_path = public as $$
declare
  plot public.garden_plots;
begin
  perform public.garden_status();

  select * into plot from public.garden_plots
  where house_id = auth.uid() and slot = plot_slot for update;

  if plot.stage not in ('sprout', 'growing') then
    raise exception 'Ahí no hay nada que regar';
  end if;
  if plot.last_watered_at is not null and now() < plot.last_watered_at + interval '2 hours' then
    raise exception 'Todavía está húmedo';
  end if;

  update public.garden_plots set
    waterings = waterings + 1,
    last_watered_at = now(),
    stage = case
      when waterings + 1 >= 3 then 'ripe'
      when waterings + 1 >= 2 then 'growing'
      else 'sprout'
    end
  where house_id = auth.uid() and slot = plot_slot;

  return public.garden_status();
end;
$$;

create function public.clear_plot(plot_slot integer) returns jsonb
language plpgsql security definer set search_path = public as $$
begin
  perform public.garden_status();

  update public.garden_plots set stage = 'empty'
  where house_id = auth.uid() and slot = plot_slot and stage = 'wilted';
  if not found then
    raise exception 'Ese bancal no está marchito';
  end if;

  return public.garden_status();
end;
$$;

revoke all on function public.clear_plot(integer) from public, anon;
grant execute on function public.clear_plot(integer) to authenticated;
