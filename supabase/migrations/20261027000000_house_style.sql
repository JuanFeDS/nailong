alter table public.profiles
  add column wall text not null default 'blue' check (wall in ('blue', 'green', 'rose', 'cream', 'gray')),
  add column floor text not null default 'wood' check (floor in ('wood', 'dark', 'light', 'gray'));

create function public.set_house_style(new_wall text, new_floor text) returns public.profiles
language plpgsql security definer set search_path = public as $$
declare
  styled public.profiles;
begin
  update public.profiles set wall = new_wall, floor = new_floor
  where id = auth.uid()
  returning * into styled;

  return styled;
end;
$$;

revoke all on function public.set_house_style(text, text) from public, anon;
grant execute on function public.set_house_style(text, text) to authenticated;

alter table public.house_items drop constraint house_items_kind_check;
alter table public.house_items add constraint house_items_kind_check check (kind in (
  'bed', 'bowl', 'ball', 'door', 'rug', 'plant',
  'bookshelf', 'clock', 'wallshelf', 'toybox', 'armchair', 'sidetable', 'pouf', 'frame'
));

insert into public.house_items (house_id, kind, x, y)
select id, 'frame', 290, 84 from public.profiles;
