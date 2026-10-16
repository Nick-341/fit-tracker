---
name: design
description: Design-System von Spotter (Variante „Kraft“). Verwenden bei jeder Änderung an Oberfläche, Layout, Farben, Texten oder neuen Ansichten in index.html.
---

# Spotter Design-System

## Charakter
Sportlich, kontrastreich, klar. Breite, kräftige Schrift für Überschriften und Zahlen, ein Signalgelb als Akzent, ruhige Flächen. Zahlen sind die Helden.

## Farben
CSS-Variablen in `:root`. Dunkelmodus über `prefers-color-scheme` und `:root[data-theme="dark"]` (Nutzerwahl Automatisch/Hell/Dunkel).

| Token | Hell | Dunkel | Verwendung |
|---|---|---|---|
| `--bg` | #F2F3F0 | #15181C | Seitenhintergrund |
| `--surface` | #FFFFFF | #21252B | Karten, Listen |
| `--soft` | #E6E8E4 | #30363E | Balken-Hintergrund, Ghost-Buttons |
| `--line` | #DCDFDA | #30363E | Trennlinien, Rahmen |
| `--ink` | #15181C | #F2F3F0 | Text, primäre Buttons |
| `--muted` | #58606A | #A2AAB2 | Nebentext |
| `--accent` | #FFB81C | #FFB81C | Akzent, aktive Tabs, Hauptaktion |
| `--on-accent` | #15181C | #15181C | Text auf Akzent |
| `--mine` | #C98200 | #FFB81C | eigene Daten (Linien, Text auf hellem Grund) |
| `--partner` | #0A84C6 | #5CC8FF | Daten des Partners |
| `--warn` | #C0341D | #FF8A7A | Überschreitung, Löschen |

Neue Farben nur mit Werten für beide Modi. Nie Text in `--accent` auf hellem Grund (Kontrast), stattdessen `--mine`. Weißer Text auf blauen Flächen nur auf #076A9F.

## Schrift
Archivo (variabel). Überschriften: `font-weight:900; font-stretch:112%`. Große Zahlen: Klasse `num` (900, 90 %). Fließtext 15–16 px, Nebentext 13 px.

## Bausteine (vorhandene Klassen wiederverwenden)
- Container: `.card`, `.list` mit `.row` (`.grow`, `.t`, `.s`, `.k`), `.note`, `.sec` + `.sec-h`
- Heute: `.hero` (Ring + Makrobalken), `.tiles`/`.tile` (`.done` = erledigt, gelb), `.prow` (Partnerzeile), `.sharein`, `.kudosin`
- Buttons: `.btn` (primär), `.btn.accent` (Hauptaktion, höchstens eine pro Ansicht), `.btn.ghost`, `.btn.line`, `.btn.danger`, `.btn.sm`, `.iconbtn`, `.plus`, `.dashed`
- Eingaben: `.f` (Label über Feld), `.grid2`, `.grid4`, `.chips`/`.chip`, `.seg`, `.switch`, `.stepper`
- Sheets: `openSheet(html)` / `closeSheet()`, Kopf `.sh-head` mit Titel und „Schließen“ bzw. „Zurück“
- Feste Leisten am Sheet-Ende: `.restbar`, `.bbar` (sticky bottom). Inhalte darunter dürfen nie verdeckt werden; Hauptaktionen gehören in die Leiste selbst.
- Rückmeldung: `toast('…')`

## Regeln
- Tippflächen mindestens 44 px hoch (`.btn.sm` mit 36 px nur für Nebenaktionen).
- iPhone-Safe-Area berücksichtigen (`env(safe-area-inset-*)`), die Tab-Leiste schwebt unten.
- Pro Ansicht genau eine Hauptaktion in Akzentfarbe.
- Keine Emojis in der Oberfläche, Icons als kleine Inline-SVGs.
- Texte: Deutsch, Du-Form, kurz, aktiv. Buttons als Verb („Speichern“, „Übernehmen“). Keine Technikbegriffe gegenüber dem Nutzer.
- Leere Zustände erklären in einem Satz, was zu tun ist.
- Lieber weniger Elemente als mehr: Neue Hinweise bündeln statt zusätzliche Karten stapeln.
- Animationen kurz und mit `prefers-reduced-motion` abschaltbar.
