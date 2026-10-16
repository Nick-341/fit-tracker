---
name: datenbank
description: Regeln für Supabase-Schema, Zugriffsregeln (RLS), Freigaben und neue Eintragsarten in Spotter. Verwenden bei jeder SQL-Änderung, jeder neuen `kind` in entries, neuen Profilfeldern mit Partnerbezug oder Storage-Änderungen.
---

# Datenbank-Regeln für Spotter

## Grundsätze
- Der Nutzer führt SQL **selbst** im Supabase SQL Editor aus. Du schreibst die Datei und erklärst, wann sie auszuführen ist. Kein direkter Datenbankzugriff.
- Jede Migration ist **wiederholbar** (`create or replace`, `if not exists`, `drop policy if exists` vor `create policy`, `on conflict do nothing`).
- Neue Migration als `update-N.sql` (fortlaufend, zuletzt `update-2.sql`) **und** denselben Inhalt am Ende von `schema.sql` anhängen, damit Neueinrichtungen vollständig sind.
- Jede Tabelle hat RLS aktiviert. Lesen: eigene Zeilen oder Partner gemäß `can_view`. Schreiben, Ändern, Löschen: nur eigene Zeilen.
- Sicherheitsrelevante Funktionen `security definer` mit `set search_path = public`.
- Nie den service_role/secret-Key im Client. Der publishable/anon-Key ist öffentlich und darf es sein.

## Freigaben (`can_view`)
Der Partner sieht ein `kind` nur, wenn die Kategorie in `profiles.data.share` nicht auf `false` steht:
- `log`, `recipe`, `food` → `nutrition`
- `workout`, `routine` → `training`
- `weight` → `weight`
- `measure` → `measure`
- alles andere → **immer sichtbar** (bewusst für `kudos`, `mealshare`, `shareack`)

**Achtung: Eine neue Eintragsart ohne Zuordnung ist für den Partner automatisch sichtbar.** Bei jeder neuen Art aktiv entscheiden und die Entscheidung in CLAUDE.md festhalten.

## Checkliste für eine neue Eintragsart (`kind`)
1. **Sichtbarkeit:** Welche Freigabe-Kategorie? Bestehende → `can_view` per Migration erweitern. Neue → Migration und Eintrag in `SHARE` (Profil-Schalter) in `index.html`.
2. **Datenzugriff:** ausschließlich über `q`/`add`/`addMany`/`upd`/`del`, damit Offline-Cache und Warteschlange greifen.
3. **Partneransicht:** Was zeigt die App, wenn der Partner die Kategorie nicht teilt? (`privNote(...)`)
4. **Export:** Der Export enthält automatisch alle eigenen `entries`. Prüfen, ob das passt.
5. **Level-System:** Soll die Art XP geben? Dann `computeGame` und die XP-Liste in `openGame` anpassen (Skill `coach`).
6. **Test-Simulation:** `tests/mock-supabase.js` mit Beispieldaten erweitern.
7. **CLAUDE.md:** Liste der Kinds aktualisieren.

## Storage
Bucket `avatars`: privat, Pfad `<user_id>/avatar.jpg`, Lesen für Besitzer und Partner, Schreiben nur Besitzer. Neue Buckets nach demselben Muster. Bilder vor dem Hochladen im Browser verkleinern.

## Profilfelder
`profiles.data` ist für den Partner immer lesbar. Werte, die der Partner nicht sehen soll, gehören **nicht** in `profiles.data`, sondern in eine eigene Eintragsart mit Freigabe-Kategorie.
