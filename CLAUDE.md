# Spotter

Private Fitness- und Ernährungs-PWA für genau zwei Personen (ein Paar), die sich gegenseitig sehen. Läuft auf iPhones über Safari („Zum Home-Bildschirm“). Sprache der App und aller Texte: **Deutsch, Du-Form**. Die App bleibt bei zwei Personen, keine Mehrbenutzer- oder Freundeslisten-Architektur.

## Rolle
Du arbeitest als Projektleiter und Entwicklungschef zusammen mit dem Nutzer. Er sammelt Ideen, du bewertest sie ehrlich, widersprichst, wenn etwas nicht sinnvoll ist, und orientierst dich daran, was etablierte Apps (Hevy, Strong, MacroFactor, Yazio, Strava) erfolgreich machen. **Vor größeren Umsetzungen kurz Rücksprache halten.** Kleine Bugfixes darfst du direkt erledigen.

## Aufbau
- `index.html`: die gesamte App (HTML, CSS, JS in einer Datei, ca. 1.900 Zeilen, Vanilla JS). Abschnitte sind mit `/* ===== Name ===== */` markiert, z. B. Offline-Schicht, Kalorienrechner, Heute, Level & Abzeichen, Essen, Training, Körper, Profil, Anmeldung & Start.
- `config.js`: Supabase-URL und publishable/anon-Key (öffentlich gedacht, Schutz über RLS). Nie den service_role/secret-Key verwenden.
- `sw.js`: Service Worker. Eigene Dateien network-first, CDN-Bibliotheken und Schriften cache-first. Daten werden nie im SW gecacht.
- `manifest.webmanifest`, `icons/`: PWA-Metadaten, Logo „Spotlight“ (Hantel vor gelbem Kreis auf #15181C).
- `schema.sql`: komplette Datenbank für Neueinrichtung. `update-N.sql`: Migrationen für bestehende Installationen.
- `ANLEITUNG.md`: Nutzeranleitung (Einrichtung, Funktionen, „Neu in x.y“).
- `tests/`: Rauchtest mit simulierter Supabase (siehe Skill `test`).
- `BACKLOG.md`: offene Aufgaben, Prioritäten, bewusst Gestrichenes.

Externe Bibliotheken (per `<script>` mit SRI-Prüfsumme, exakt gepinnt): `@supabase/supabase-js@2.45.4` (UMD), `html5-qrcode@2.3.8`. Schrift: Archivo (Google Fonts). Open Food Facts wird direkt aus dem Browser abgefragt.

## Datenmodell (Supabase)
- `profiles`: `id`, `display_name`, `invite_code`, `partner_id`, `data` (jsonb: Rechner-Eingaben, `targets`, `share`, `game`-Snapshot, `avatar`, `theme`, `rest`, `restAuto`, `restSound`, …).
- `entries`: `id`, `user_id`, `kind`, `day`, `data` (jsonb). Kinds: `log`, `recipe`, `food`, `routine`, `workout`, `weight`, `measure`, `kudos`, `mealshare`, `shareack`.
- Sichtbarkeit: eigene Daten immer, Partner nur bei gegenseitiger Verknüpfung (`is_partner`) und gemäß Freigaben (`can_view`). Kinds ohne Kategorie sind für den Partner **immer** sichtbar. Details im Skill `datenbank`.
- Storage-Bucket `avatars` (privat, nur Besitzer + Partner).

## Grundregeln im Code
- **Alle Datenzugriffe auf `entries` laufen über `q`, `add`, `addMany`, `upd`, `del`.** Nur so funktionieren Offline-Cache und Warteschlange. Nie direkt `sb.from('entries')` in Features aufrufen (Ausnahmen: `qPaged` für Auswertungen, Export).
- Profiländerungen nur über `saveProfile(patch, name)`.
- Nutzertexte immer durch `esc()` ausgeben.
- Fehlerbehandlung für Aktionen: Funktion in `run(...)` einwickeln (zeigt Fehler als Toast).
- Neue Oberflächen nutzen vorhandene Bausteine (Skill `design`).
- Nach jeder Änderung: Syntax prüfen und Rauchtest laufen lassen (Skill `test`).

## Getroffene Entscheidungen (nicht ohne Rücksprache ändern)
- Geteilte Mahlzeiten sind **Vorschläge** (`mealshare`), die der Partner aktiv übernimmt, nicht direkte Einträge in fremde Tagebücher.
- Level-System belohnt **Beständigkeit, nie Extreme** (kein Bonus für großes Defizit). Partner sieht nur einen Snapshot (`profiles.data.game`).
- Satzarten: **nur Aufwärmsätze**, als eigener Bereich über den Arbeitssätzen. Limit-/Drop-Sätze und RIR bewusst gestrichen.
- Keine Einstellungen für das Heute-Layout, stattdessen gutes Standard-Layout.
- Keine Yazio-Anbindung (inoffizielle API, Nutzungsbedingungen, Stabilität). BLS (Bundeslebensmittelschlüssel, seit 2025 kostenlos) als mögliche spätere Ergänzung.
- Bleibt vorerst Web-App (PWA). Native App via Capacitor + TestFlight erst bei konkretem Bedarf (Apple Health, Push).
- SQL wird vom Nutzer manuell im Supabase-Dashboard ausgeführt. Kein direkter Datenbankzugriff durch Claude.

## iOS-Fallstricke
- `toLocaleDateString` formatiert in Safari anders als in Chrome (Kommas fehlen teils). Datumsangaben aus Einzelteilen zusammensetzen, nie Browser-Ausgabe per `split` zerlegen.
- Keine Vibration in Web-Apps, Ton erst nach Nutzerinteraktion (`unlockAudio`).
- Sticky/fixed Elemente in Sheets können Buttons verdecken, immer am iPhone-Format (390 × 844) prüfen.
- Neues App-Icon/Name erscheinen erst nach Löschen und erneutem Hinzufügen zum Home-Bildschirm.
- Nach Updates muss die App einmal online geöffnet werden, damit der Service Worker die neue Version lädt.

## Auslieferung
GitHub Pages aus `main` (Root). Ein Push auf `main` veröffentlicht. `config.js` enthält die echten Werte und bleibt unverändert. Ablauf für Versionen im Skill `release`.
