---
name: release
description: Veröffentlicht eine neue Spotter-Version. Verwenden, wenn ein Update, Hotfix oder Release abgeschlossen werden soll oder der Nutzer „release“, „Version“, „veröffentlichen“ oder „live stellen“ sagt.
---

# Release-Ablauf für Spotter

Versionsschema: `MAJOR.MINOR.PATCH`. Hotfix (nur Fehler) → PATCH, neue Funktionen → MINOR. Im Zweifel den Nutzer fragen.

## Checkliste (alle Schritte, in dieser Reihenfolge)

1. **Tests grün:** Skill `test` ausführen. Kein Release mit Fehlern.
2. **Versionsnummer:** in `index.html` `const APP_VERSION = 'x.y.z';` erhöhen.
3. **Changelog in der App:** `const CHANGELOG = [...]` komplett durch die Neuerungen *dieser* Version ersetzen. Format `['Kurzer Titel', 'Ein bis zwei Sätze, was der Nutzer jetzt tun kann.']`. Aus Nutzersicht schreiben, Deutsch, Du-Form, keine Technikbegriffe. Bei reinen Hotfixes ein Eintrag „Fehlerbehebungen“ mit kurzer Aufzählung im Text. Der Dialog erscheint automatisch einmal, weil sich `APP_VERSION` ändert.
4. **Service-Worker-Cache:** in `sw.js` `const CACHE = 'spotter-vN';` um eins erhöhen. Ohne diesen Schritt sehen die iPhones die neue Version nicht zuverlässig.
5. **Bibliotheken geändert?** Nur dann: neue Version exakt pinnen (mindestens zwei Wochen alt), SRI-Hash (sha384) neu berechnen und in `index.html` **und** in `LIBS` in `sw.js` anpassen:
   `curl -sL <URL> | openssl dgst -sha384 -binary | openssl base64 -A`
6. **SQL nötig?** Wenn ja (Skill `datenbank`): `update-N.sql` vorhanden und `schema.sql` ergänzt. Im Release-Hinweis an den Nutzer **fett** vermerken, dass die SQL-Datei *vor* dem Push im Supabase SQL Editor ausgeführt werden muss.
7. **Anleitung und Changelog:** in `ANLEITUNG.md` einen Absatz „**Neu in x.y.z**:“ über dem vorherigen ergänzen. `CHANGELOG.md` hat einen Abschnitt `## x.y.z – TT.MM.JJJJ` mit allen Punkten (wird in jedem Commit mitgepflegt).
8. **Backlog:** erledigte Punkte in `BACKLOG.md` unter „Erledigt“ eintragen, „Aktuelle Version“ anpassen.
9. **Commit und Tag:** `git add -A && git commit -m "Spotter x.y.z: <Kurzbeschreibung>" && git tag vx.y.z`. **Nie selbst pushen.** Der Nutzer pusht über GitHub Desktop (Commit und Tag; Tags dort ggf. mit „Push tags“ bzw. beim nächsten Push mitnehmen).

## Niemals
- `config.js` ändern oder echte Schlüssel in andere Dateien kopieren.
- Den Service-Worker-Cache vergessen.
- Selbst pushen (`git push`), egal in welcher Situation.

## Abschlussnachricht an den Nutzer
Kurz: Was ist neu (in Nutzersprache), ob ein SQL-Schritt nötig ist, **wann der Nutzer über GitHub Desktop pushen soll** (bei SQL erst danach), was er danach konkret auf dem iPhone prüfen soll, Hinweis „App einmal online öffnen“. Bei Logo- oder Namensänderung: Verknüpfung auf dem Home-Bildschirm neu anlegen.
