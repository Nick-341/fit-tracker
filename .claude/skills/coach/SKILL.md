---
name: coach
description: Fachliche Grundlagen für Spotter (Kalorienrechner, Makros, Level/XP, Trainingsprogression, Wochenrückblick, Coach-Hinweise). Verwenden bei Änderungen an Berechnungen, Zielen, XP-Regeln, Abzeichen, Steigerungshinweisen oder Texten mit Ernährungs- und Trainingsbezug.
---

# Coach-Logik in Spotter

## Kalorienrechner (`calc` in index.html)
- Grundumsatz: Mifflin-St Jeor; mit Körperfettanteil Katch-McArdle (`370 + 21,6 × fettfreie Masse`).
- Alltag: Grundumsatz × 1,2 + 0,0005 kcal × kg je Schritt über 3.000.
- Training: Netto-Mehrverbrauch `(MET − 1) × kg × Stunden`. MET: Kraft 3,5, Kraft intensiv 5, gemischt 5,5, Ausdauer 7, Ausdauer intensiv 10.
- Ziel: Defizit aus Tempo in % Körpergewicht pro Woche (7.700 kcal ≈ 1 kg), **maximal 25 % des Verbrauchs**. Aufbau: Überschuss aus % pro Monat. Rekomposition: −5 %.
- Makros: Protein und Fett in g/kg, Kohlenhydrate füllen den Rest. Warnung bei < 50 g KH oder > 2,5 g Protein/kg.
- Optional Trainings-/Ruhetage: Trainingstage bekommen den Trainingsverbrauch zusätzlich.
- Adaptive Messung: ≥ 6 Gewichte über ≥ 13 Tage und ≥ 10 geloggte Tage (> 600 kcal) innerhalb von 28 Tagen. Verbrauch = Ø Aufnahme − Gewichtstrend (lineare Regression, kg/Tag) × 7.700.

## Level-System (`computeGame`)
Grundsatz: **Beständigkeit belohnen, nie Extreme.** Niemals XP für größeres Defizit, weniger Essen oder schnelleren Gewichtsverlust.
- Essen geloggt (≥ 50 % Ziel) +10 · im Ziel (±10 %) +20 · Protein ≥ 90 % +15 · Training +30 (max. 2 pro Tag) · Bestwert +15 (max. 3 pro Einheit; geschätztes 1RM = kg × (1 + Wdh/30)) · Gewicht +5 · Maße +10 (1× pro Woche)
- Bedarf für Level L → L+1 = 100 + 50 × (L − 1). Titel: Einsteiger, Stammgast (3), Eisenfreund (6), Routinier (10), Athlet (15), Maschine (20), Legende (30).
- Serie: aufeinanderfolgende Tage mit geloggtem Essen. Der Partner sieht nur den Snapshot in `profiles.data.game`.
- Aufwärmsätze (ab 1.6) zählen nicht für Volumen, Bestwerte und XP.

## Trainingsprogression (ab 1.6)
Doppelte Progression: Erreicht der schwerste Arbeitssatz das obere Ende des Wiederholungsziels, beim nächsten Mal mehr Gewicht vorschlagen (Oberkörper +2,5 kg, Unterkörper +5 kg, Kurzhanteln kleinste sinnvolle Stufe). Sonst gleiches Gewicht und mehr Wiederholungen anstreben. Immer als Vorschlag formulieren, nie als Pflicht.

## Formulierungen
- Ermutigend, sachlich, konkret, ohne Schuld oder Druck („Logge an mehr Tagen vollständig, dann werden die Werte aussagekräftig“).
- Nie zu weniger Essen als das Ziel auffordern. Deutlich unter Ziel ist ein Warnsignal, kein Erfolg.
- Keine medizinischen Diagnosen. Bei auffälligen Mustern (über längere Zeit sehr wenig Essen) zurückhaltend auf Ausgewogenheit hinweisen.
- Gewicht immer über den 7-Tage-Durchschnitt bewerten, nie über Einzeltage.
