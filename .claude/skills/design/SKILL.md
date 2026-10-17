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
| `--board` | #15181C | #0B0D10 | Anzeigetafel (`.board`), auch im Hellmodus dunkel |
| `--board-soft` | #2E343B | #262B32 | Balken-Hintergrund, Trennlinien, Segment auf der Tafel |
| `--board-ink` | #F2F3F0 | #F2F3F0 | Text auf der Tafel |
| `--board-muted` | #A2AAB2 | #A2AAB2 | Nebentext und `.lbl` auf der Tafel |
| `--partner-bg` | #E3F1FA | #1C2E3A | Flächen mit Partnerbezug (z. B. Mahlzeitvorschlag) |
| `--hint` | #FFF1CC | #3A311C | Hinweisleiste (`.hintbar`) |
| `--pad` | #FFFFFF | #1B1F24 | Eingabefelder und Zahlenfeld |

Neue Farben nur mit Werten für beide Modi. Nie Text in `--accent` auf hellem Grund (Kontrast), stattdessen `--mine`. Weißer Text auf blauen Flächen nur auf #076A9F.

## Schrift
Archivo (variabel). Überschriften: `font-weight:900; font-stretch:112%`. Fließtext 15–16 px, Nebentext 13 px.
- `.num`: 900, `font-stretch:90%`, `tabular-nums`. Größen-Klassen `.n108 .n96 .n54 .n44 .n40` (line-height .8), `.n36 .n28 .n24 .n20`. Einheit dahinter als `<span class="unit">kg</span>`.
- Tafel-Hauptzahl 88–108 px · Kachelzahl 40–44 px · Inline-Zahl 20–28 px.
- `.lbl`: 11 px, 800, `letter-spacing:.12em`, Versalien, `--muted` (auf `.board` automatisch `--board-muted`).
- **Alle Zahlen mit `tabular-nums`** (ist auf `body` gesetzt, nicht überschreiben).

## Maße
- Radien (Variablen): `--r-board` 24 · `--r-card` 20 (Karten, Listen) · `--r-btn` 14 (Buttons, Felder) · `--r-sm` 10 (klein).
- Abstände nur 4 / 8 / 12 / 16 / 24 px.

## Bausteine (vorhandene Klassen wiederverwenden)
- Anzeigetafel: `.board` (Radius 24, Padding 20, Hintergrund `--board`). Darin `.track` automatisch auf `--board-soft` mit gelber Füllung, `.track.over` rot, `<hr>` als Trennlinie. Balken: `.track.t10` (Hauptbalken), `.track.t4` (Makros).
- Hinweise: `.hintbar` (gebündelte Hinweise, Hintergrund `--hint`)
- Container: `.card`, `.list` mit `.row` (`.grow`, `.t`, `.s`, `.k`), `.note`, `.sec` + `.sec-h`
- Heute: `.hero` (Ring + Makrobalken), `.tiles`/`.tile` (`.done` = erledigt, gelb), `.prow` (Partnerzeile), `.sharein`, `.kudosin`
- Buttons: `.btn` (primär), `.btn.accent` (Hauptaktion, höchstens eine pro Ansicht), `.btn.ghost`, `.btn.line`, `.btn.danger`, `.btn.sm`, `.iconbtn`, `.plus`, `.dashed`
- Eingaben: `.f` (Label über Feld), `.grid2`, `.grid4`, `.chips`/`.chip`, `.seg`, `.switch`, `.stepper`
- Sheets: `openSheet(html)` / `closeSheet()`, Kopf `.sh-head` mit Titel und „Schließen“ bzw. „Zurück“
- Feste Leisten am Sheet-Ende: `.wbar` (Training: Pausentimer `#restbar` + Auto-Timer + „Einheit speichern“), `.bbar` (Korb), beide sticky bottom. Inhalte darunter dürfen nie verdeckt werden; Hauptaktionen gehören in die Leiste selbst.
- Rückmeldung: `toast('…')`

## Regeln
- **Große Zahl = Restwert oder Trend, nie Rohwert** (kcal übrig statt gegessen, Ø 7 Tage statt Tageswiegung).
- **Gelb nur für Fortschritt, Erledigtes und die eine Hauptaktion.** Keine gelben Deko-Flächen.
- **Hinweise bündeln statt Karten stapeln** (eine `.hintbar` statt mehrerer Karten).
- Pro Ansicht höchstens eine `.board`, immer oben.
- **Wörter nie mitten im Wort trennen:** kein `word-break: break-all`, kein `overflow-wrap: anywhere` (Ausnahme nur für lange URLs o. Ä., dann im Code begründen). Zahl und Einheit mit `&nbsp;` verbinden („ca.&nbsp;55&nbsp;min“).
- **Einzeilige Titel** in Kacheln, Listenzeilen, Tafeln und Buttons: `white-space:nowrap; overflow:hidden; text-overflow:ellipsis`. Mehrzeilig nur bei Fließtext und Hinweisen.
- **In Flex- und Grid-Kindern mit Text immer `min-width:0`**, Rasterspalten als `minmax(0,1fr)` statt `1fr` (sonst wächst die Spalte mit langem Text).
- Prüfen in 390 × 844 **und** 375 × 667, hell und dunkel, mit langen Namen (z. B. „Rumänisches Kreuzheben“, „Hähnchen-Reis-Bowl mit Gemüse“). Der Rauchtest `flow_umbruch` meldet getrennte Wörter und Text über den Karten- oder Bildschirmrand.
- Tippflächen mindestens 44 px hoch (`.btn.sm` mit 36 px nur für Nebenaktionen).
- iPhone-Safe-Area berücksichtigen (`env(safe-area-inset-*)`), die Tab-Leiste schwebt unten.
- Pro Ansicht genau eine Hauptaktion in Akzentfarbe.
- Keine Emojis in der Oberfläche, Icons als kleine Inline-SVGs.
- Texte: Deutsch, Du-Form, kurz, aktiv. Buttons als Verb („Speichern“, „Übernehmen“). Keine Technikbegriffe gegenüber dem Nutzer.
- Leere Zustände erklären in einem Satz, was zu tun ist.
- Lieber weniger Elemente als mehr: Neue Hinweise bündeln statt zusätzliche Karten stapeln.
- Animationen kurz und mit `prefers-reduced-motion` abschaltbar.
