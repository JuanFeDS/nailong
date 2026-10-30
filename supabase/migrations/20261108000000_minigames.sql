alter table public.daily_progress add column minigame_coins integer not null default 0;

create function public.finish_minigame(game text, level integer, score integer) returns integer
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

  -- Tope propio de 20 al día; grant_coins aplica además el de 40 de toda la economía.
  wanted := least(10, ceil(least(greatest(score, 0), max_score) * level / divisor::numeric)::integer, greatest(0, 20 - already));
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

revoke all on function public.finish_minigame(text, integer, integer) from public, anon;
grant execute on function public.finish_minigame(text, integer, integer) to authenticated;
