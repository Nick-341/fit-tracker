-- ============================================================
-- Fit-Tracker: Datenbank-Einrichtung für Supabase
-- Komplett in den SQL Editor kopieren und einmal ausführen.
-- Kann gefahrlos erneut ausgeführt werden.
-- ============================================================

create extension if not exists pgcrypto;

-- Profile: eins pro Person (Name, Rechner-Eingaben, Ziele, Partner)
create table if not exists public.profiles (
  id          uuid primary key references auth.users(id) on delete cascade,
  display_name text not null default '',
  invite_code text not null unique
              default upper(substr(md5(random()::text || clock_timestamp()::text), 1, 6)),
  partner_id  uuid references public.profiles(id) on delete set null,
  data        jsonb not null default '{}'::jsonb,
  updated_at  timestamptz not null default now()
);

-- Einträge: Essen, Vorlagen, Lebensmittel, Training, Gewicht, Maße
create table if not exists public.entries (
  id         uuid primary key default gen_random_uuid(),
  user_id    uuid not null default auth.uid() references auth.users(id) on delete cascade,
  kind       text not null,
  day        date,
  data       jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create index if not exists entries_user_kind_day on public.entries (user_id, kind, day);

-- Partner = beide Profile zeigen gegenseitig aufeinander
create or replace function public.is_partner(other uuid) returns boolean
language sql stable security definer set search_path = public as $$
  select exists (
    select 1 from profiles me
    join profiles them on them.id = me.partner_id
    where me.id = auth.uid() and them.id = other and them.partner_id = me.id
  );
$$;

-- Verknüpfen per Einladungscode
create or replace function public.link_partner(code text) returns uuid
language plpgsql security definer set search_path = public as $$
declare other uuid; other_partner uuid;
begin
  select id, partner_id into other, other_partner
    from profiles where invite_code = upper(trim(code));
  if other is null then raise exception 'Code nicht gefunden'; end if;
  if other = auth.uid() then raise exception 'Das ist dein eigener Code'; end if;
  if other_partner is not null and other_partner <> auth.uid() then
    raise exception 'Diese Person ist bereits mit jemand anderem verknüpft';
  end if;
  update profiles set partner_id = null where partner_id = auth.uid() and id <> other;
  update profiles set partner_id = auth.uid(), updated_at = now() where id = other;
  update profiles set partner_id = other,      updated_at = now() where id = auth.uid();
  return other;
end; $$;

create or replace function public.unlink_partner() returns void
language plpgsql security definer set search_path = public as $$
begin
  update profiles set partner_id = null where partner_id = auth.uid();
  update profiles set partner_id = null where id = auth.uid();
end; $$;

revoke all on function public.link_partner(text) from public, anon;
revoke all on function public.unlink_partner() from public, anon;
grant execute on function public.is_partner(uuid)   to authenticated;
grant execute on function public.link_partner(text) to authenticated;
grant execute on function public.unlink_partner()   to authenticated;

-- Zugriffsregeln: lesen = ich + verknüpfter Partner, schreiben = nur ich
alter table public.profiles enable row level security;
alter table public.entries  enable row level security;

drop policy if exists "profil lesen"    on public.profiles;
drop policy if exists "profil anlegen"  on public.profiles;
drop policy if exists "profil aendern"  on public.profiles;
create policy "profil lesen"   on public.profiles for select using (id = auth.uid() or public.is_partner(id));
create policy "profil anlegen" on public.profiles for insert with check (id = auth.uid());
create policy "profil aendern" on public.profiles for update using (id = auth.uid()) with check (id = auth.uid());

drop policy if exists "eintraege lesen"   on public.entries;
drop policy if exists "eintraege anlegen" on public.entries;
drop policy if exists "eintraege aendern" on public.entries;
drop policy if exists "eintraege loeschen" on public.entries;
create policy "eintraege lesen"    on public.entries for select using (user_id = auth.uid() or public.is_partner(user_id));
create policy "eintraege anlegen"  on public.entries for insert with check (user_id = auth.uid());
create policy "eintraege aendern"  on public.entries for update using (user_id = auth.uid()) with check (user_id = auth.uid());
create policy "eintraege loeschen" on public.entries for delete using (user_id = auth.uid());
