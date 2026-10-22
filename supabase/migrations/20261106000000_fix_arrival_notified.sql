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

  select id into other_user from public.profiles where id <> auth.uid();
  if other_user is null then
    raise exception 'Falta el segundo usuario';
  end if;

  update public.nailong set
    current_home = other_user,
    status = 'traveling',
    place = 'room',
    arrival_notified = false,
    arrives_at = now() + interval '5 minutes' + random() * interval '5 minutes',
    last_sent_at = now(),
    trip_times = array_append(
      array(select trip_time from unnest(trip_times) as trip_time where trip_time > now() - interval '24 hours'),
      now()
    )
  where id
  returning * into row_nailong;

  return row_nailong;
end;
$$;
