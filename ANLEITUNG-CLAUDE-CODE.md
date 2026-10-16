# Spotter mit Claude Code weiterentwickeln

Diese Datei kannst du nach der Einrichtung löschen.

## Erster Auftrag an Claude Code (kopieren und einfügen)

```
Im Projektordner liegt spotter-claude-code.zip. Bitte:
1. Entpacke es in den Projektordner (bestehende Dateien wie index.html und config.js dürfen nicht überschrieben werden) und lösche danach die ZIP-Datei.
2. Lies CLAUDE.md, BACKLOG.md und die Skills unter .claude/skills.
3. Richte die Testumgebung laut Skill test ein und führe die Tests aus. Erwartet sind genau drei Fehler, die zum Hotfix 1.5.2 gehören.
4. Committe die neuen Dateien mit der Nachricht "Projektwissen für Claude Code" und pushe.
Fasse mir danach kurz zusammen, was du über das Projekt weißt.
```

## Zweiter Auftrag: Hotfix 1.5.2

```
Setze den Hotfix 1.5.2 aus BACKLOG.md um. Teste mit dem Skill test, bis alles grün ist, und schließe mit dem Skill release ab. Frag mich vor dem Push.
```

## Später
- Neue Ideen sammeln und besprechen, bevor gebaut wird: Claude Code hält laut CLAUDE.md Rücksprache.
- Hilfreiche Befehle: `/release`, `/test`. Die Skills `design`, `datenbank` und `coach` lädt Claude Code automatisch, wenn sie passen.
- SQL-Dateien führst du selbst im Supabase SQL Editor aus, bevor gepusht wird.
