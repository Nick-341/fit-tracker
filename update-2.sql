-- ============================================================
-- Spotter Update: Freigabe-Einstellungen und Profilfotos
-- Einmal komplett im Supabase SQL Editor ausführen.
-- Kann gefahrlos erneut ausgeführt werden. Bestehende Daten bleiben erhalten.
-- ============================================================

-- Darf der aktuelle Nutzer Einträge dieser Art von "owner" sehen?
-- Eigene immer; vom Partner nur, wenn er den Bereich nicht ausgeblendet hat.
create or replace function public.can_view(owner uuid, k text) returns boolean
language sql stable security definer set search_path = public as $$
  select owner = auth.uid() or (
    public.is_partner(owner) and coalesce((
      select (p.data -> 'share' ->> (case
        when k in ('log', 'recipe', 'food') then 'nutrition'
        when k in ('workout', 'routine')    then 'training'
        when k = 'weight'                   then 'weight'
        when k = 'measure'                  then 'measure'
        else 'immer' end))::boolean
      from profiles p where p.id = owner), true)
  );
$$;
grant execute on function public.can_view(uuid, text) to authenticated;

drop policy if exists "eintraege lesen" on public.entries;
create policy "eintraege lesen" on public.entries for select
  using (public.can_view(user_id, kind));

-- Speicher für Profilfotos (privat: nur du und dein Partner)
insert into storage.buckets (id, name, public)
values ('avatars', 'avatars', false)
on conflict (id) do nothing;

drop policy if exists "avatar lesen"    on storage.objects;
drop policy if exists "avatar anlegen"  on storage.objects;
drop policy if exists "avatar aendern"  on storage.objects;
drop policy if exists "avatar loeschen" on storage.objects;

create policy "avatar lesen" on storage.objects for select to authenticated
  using (bucket_id = 'avatars' and (
    (storage.foldername(name))[1] = auth.uid()::text
    or public.is_partner(((storage.foldername(name))[1])::uuid)));
create policy "avatar anlegen" on storage.objects for insert to authenticated
  with check (bucket_id = 'avatars' and (storage.foldername(name))[1] = auth.uid()::text);
create policy "avatar aendern" on storage.objects for update to authenticated
  using (bucket_id = 'avatars' and (storage.foldername(name))[1] = auth.uid()::text)
  with check (bucket_id = 'avatars' and (storage.foldername(name))[1] = auth.uid()::text);
create policy "avatar loeschen" on storage.objects for delete to authenticated
  using (bucket_id = 'avatars' and (storage.foldername(name))[1] = auth.uid()::text);
