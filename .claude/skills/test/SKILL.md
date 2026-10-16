---
name: test
description: Rauchtest für Spotter mit simulierter Supabase im iPhone-Format. Nach jeder Code-Änderung an index.html oder sw.js verwenden, vor jedem Release, und wenn der Nutzer „testen“ oder „prüfen“ sagt.
---

# Spotter testen

Die App wird in Chromium (Playwright) im iPhone-Format 390 × 844 geöffnet. Supabase wird durch `tests/mock-supabase.js` ersetzt (In-Memory-Datenbank mit Beispieldaten für zwei Personen: Max = ich, Lena = Partnerin). Alle externen Anfragen werden abgefangen, es braucht kein Internet. SRI-Prüfsummen werden im Test entfernt, weil die Simulation die echte Bibliothek ersetzt.

## Einmalige Einrichtung
```bash
pip3 install playwright pillow
python3 -m playwright install chromium
```

## Ausführen
```bash
python3 tests/smoke.py            # alle Abläufe
python3 tests/smoke.py training   # nur Abläufe, deren Name "training" enthält
```
Erwartete Ausgabe am Ende: `ALLE TESTS OK`. Screenshots landen in `tests/screenshots/` (nicht einchecken).

## Vorgehen nach Änderungen
1. Syntax prüfen: `python3 tests/smoke.py` prüft das Haupt-Script vorab mit `node --check`, falls Node installiert ist.
2. Tests ausführen. Bei Fehlern zuerst die Ausgabe lesen (Seitenfehler und Toast-Texte werden mitgeloggt), Ursache beheben, erneut testen.
3. **Screenshots ansehen**, mindestens die betroffenen Ansichten. Prüfen: nichts verdeckt (besonders Buttons unter festen Leisten), kein Text abgeschnitten oder unschön umbrochen, Tippflächen groß genug, Hell- und Dunkelmodus.
4. **Neue Funktion = neuer Testablauf** in `tests/smoke.py` (Funktion `flow_<name>(pg)`, in `FLOWS` eintragen). Mit `check(bedingung, 'Beschreibung')` prüfen.
5. **Neue Datenart oder neue Supabase-Methode** → `tests/mock-supabase.js` erweitern (Abschnitte BEISPIELDATEN und QUERY-BUILDER).

## Grenzen
Die Simulation prüft Logik und Darstellung, nicht Supabase selbst (Zugriffsregeln, SQL) und nicht Safari. Safari-spezifisches Verhalten (Datumsformat, Audio, Kamera, Service Worker) dem Nutzer als konkrete Prüfbitte mitgeben: „Bitte am iPhone prüfen: …“.
