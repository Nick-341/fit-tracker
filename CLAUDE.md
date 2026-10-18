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
- `ANLEITUNG.md`: Nutzeranleitung mit „Neu in x.y.z“ (seit 1.6.0).
- `CHANGELOG.md`: Änderungen je Version, in jedem Commit pflegen. In der App zeigt „Was ist neu“ nur die aktuelle Version.
- `docs/design/<version>/`: Entwürfe (je Screen hell/dunkel). Bei Widerspruch zwischen Bild und Auftrag gilt der Auftrag.
- `tests/`: Rauchtest mit simulierter Supabase (siehe Skill `test`).
- `BACKLOG.md`: offene Aufgaben, Prioritäten, bewusst Gestrichenes.

Externe Bibliotheken (per `<script>` mit SRI-Prüfsumme, exakt gepinnt): `@supabase/supabase-js@2.45.4` (UMD), `html5-qrcode@2.3.8`. Schrift: Archivo (Google Fonts). Open Food Facts wird direkt aus dem Browser abgefragt.

## Datenmodell (Supabase)
- `profiles`: `id`, `display_name`, `invite_code`, `partner_id`, `data` (jsonb: Rechner-Eingaben, `targets`, `share`, `game`-Snapshot, `avatar`, `theme`, `rest`, `restAuto`, `restSound`, …).
- `entries`: `id`, `user_id`, `kind`, `day`, `data` (jsonb). Kinds: `log`, `recipe`, `food`, `routine`, `workout`, `weight`, `measure`, `kudos`, `mealshare`, `shareack`.
- `workout.data.exercises[].sets[]`: `{ kg, reps, warm? }`. `warm: true` = Aufwärmsatz (zählt nicht für Volumen, Bestwerte, XP, Übungsfortschritt; immer über `isWork` filtern). `routine.data.exercises[].reps` = Wiederholungsbereich „6-8“ oder leer (kein Ziel).
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
- „Im Ziel“ (±10 % vom Kalorienziel, mind. halbes Ziel geloggt) gibt es nur einmal: `inTarget()`. Level-System, Wochenleiste und Wochenrückblick nutzen dieselbe Funktion.
- Training „Als Nächstes“: der Trainingstag, der am längsten nicht trainiert wurde (`nextRoutine`). Feste Wochentage für Trainingstage gibt es noch nicht.
- Einheit: Gespeichert werden abgehakte und von Hand geänderte Sätze; nur vorausgefüllte ohne Haken fallen weg (Hinweis mit Rückgängig). Steigerung +2,5 kg für alle Übungen, Wdh. aufs untere Ziel.
- Löschen ohne Nachfrage mit Rückgängig (`softDel`/`undoBar`) für Einträge, Sätze, Übungen, Einheiten, Gewicht, Maße. Trainingstage, Vorlagen, Abmelden, Verknüpfung lösen behalten die Nachfrage.
- Zahleneingaben über das eigene Zahlenfeld (`npOpen`), nicht über `<input>`. Ausnahmen: Suche, Texte, Kalorienrechner, Nährwerte eigener Lebensmittel, Trainingstag-Editor.
- Kalender lädt pro Monat über `q` (gecacht). `qPaged` hat bewusst keinen Cache.
- Pausenleiste in der Einheit: „+30 s“ und „×“ direkt, −15/+15 nach Tipp auf die Restzeit. Timer-Knöpfe nie im 250-ms-Takt neu bauen (Taps gehen sonst verloren).
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
GitHub Pages aus `main` (Root). Ein Push auf `main` veröffentlicht.
**Claude pusht nie selbst** (kein `git push`, auch nicht nach Zustimmung). Der Nutzer pusht über GitHub Desktop. Claude committet und taggt lokal und sagt am Ende, wann gepusht werden soll (bei SQL-Updates erst nach Ausführung des SQL) und was danach auf dem iPhone zu prüfen ist. `config.js` enthält die echten Werte und bleibt unverändert. Ablauf für Versionen im Skill `release`.
