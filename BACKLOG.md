# Backlog Spotter

Aktuelle Version: **1.5.1**

## Hotfix 1.5.2 (als Nächstes)
Der Rauchtest bildet beide Fehler bereits nach und schlägt aktuell mit genau diesen Meldungen fehl: „Datum Gestern ohne undefined (Safari-Format)“, „Speichern-Knopf nicht vom Timer verdeckt“ und der daraus folgende Abbruch im Trainingsablauf. Nach dem Hotfix müssen alle Tests grün sein.

- [ ] **Bug: „Gestern, undefined“** in der Kopfzeile. Ursache: `longDay()` zerlegt die Ausgabe von `toLocaleDateString` per `split(', ')`, Safari liefert kein Komma. Lösung: Wochentag, Tag und Monat einzeln formatieren und selbst zusammensetzen.
- [ ] **Bug: Pausentimer verdeckt „Einheit speichern“** im Trainings-Sheet. Lösung: Timer und Speichern-Knopf in eine gemeinsame feste Leiste am unteren Rand des Sheets, Speichern immer erreichbar.

## Version 1.6 (nach Rücksprache umsetzen)
- [ ] **Satz abhaken:** Sätze mit Werten vom letzten Mal vorausgefüllt, ✓ bestätigt (startet Timer bei Auto-Timer), abgehakte Sätze markiert, erledigte Übungen klappen zu, Sprung zur nächsten offenen Übung.
- [ ] **Aufwärmsätze:** eigener Bereich „+ Aufwärmsatz“ über den Arbeitssätzen, grau beschriftet. Zählen nicht für Volumen, Bestwerte, XP.
- [ ] **Steigerungshinweis:** Wurde beim schwersten Satz das obere Wiederholungsziel erreicht, beim nächsten Mal mehr Gewicht vorschlagen (doppelte Progression, z. B. +2,5 kg).
- [ ] **Heute aufräumen** (ohne Einstellungen): Kudos und Mahlzeitvorschläge als kompakte Hinweisleiste, erledigter Plan als eine Zeile.
- [ ] **Essen kompakter:** leere Mahlzeiten als schmale Zeile mit „+“, im Mahlzeitenkopf kcal und Protein.
- [ ] **Rückgängig statt Nachfragen:** nach Löschen einige Sekunden „Gelöscht, Rückgängig“ (Einträge, Sätze, Übungen, Einheiten).
- [ ] **Zuletzt verwendet nach Mahlzeit sortiert:** in der Lebensmittelsuche zuerst, was in dieser Mahlzeit am häufigsten gegessen wird.
- [ ] **Kalender:** Tipp auf das Datum öffnet Monatsansicht mit Markierungen (Essen geloggt, Training, im Ziel) zum schnellen Springen und Nachpflegen.

## Ideen für später
- Notizen pro Übung (z. B. Sitzeinstellung)
- Bildschirm bleibt während des Trainings an (Wake Lock, auf iOS testen)
- Scheibenrechner für die Langhantel
- Gemeinsames Training mit Live-Ansicht der Sätze des Partners
- Fortschrittsfotos (privat, Vorher-nachher)
- Offline-Modus Stufe B (komplette Ernährung inkl. Suche)
- BLS als Lebensmitteldatenbank für Grundnahrungsmittel
- Native App (Capacitor, TestFlight) bei Bedarf an Apple Health oder Push
- `index.html` in mehrere Dateien aufteilen, sobald die Größe stört

## Bewusst gestrichen
- Limit- und Drop-Sätze, RIR (bringen keine Entscheidung, die die Daten nicht schon tragen)
- Einstellungen für das Heute-Layout
- Favoriten nach Uhrzeit (ersetzt durch Sortierung nach Mahlzeit)
- Yazio-Anbindung
- Automatisches Abmelden als Standard (nur optional vorhanden)

## Erledigt
1.0 Grundversion · 1.1 Design B, Hell/Dunkel, Level-System · 1.2 Name Spotter, Logo, Trainingstag-Editor mit Bibliothek · 1.4 Pausentimer, Kopieren, Kudos, Profilfoto, Freigaben, Sicherheit, Übungsfortschritt, Wochenrückblick, Changelog · 1.5 Offline-Modus, Trainingsentwurf, Sammelkorb, Dauer-Scan, Kopieren mit Ziel, Einträge bearbeiten, Export, SRI · 1.5.1 Mahlzeiten an Partner schicken, Auto-Timer abschaltbar
