# Zurückgestellte Befunde aus Phase 11

Was hier steht, ist während der Ausführung aufgefallen und liegt ausserhalb des Scope des
Plans, in dem es gefunden wurde. Keiner dieser Punkte wurde repariert.

## DF-11-01: `truncated` hat in Talk dieselbe Doppelbedeutung wie in Mail vor IN-01

- **Gefunden in:** Plan 11-08, Task 2 (beim Schliessen von IN-01)
- **Ort:** `src/mcp_connector/tools/talk.py`, `_message` (Eintragsebene, `entry["truncated"]`)
  gegen `_history` (Antwortebene, `answer["truncated"]` mit `next` daneben)
- **Befund:** Genau die Konstellation, die der Review als IN-01 für `tools/mail.py` benannt
  hat: derselbe Schlüssel bedeutet auf Antwortebene "die Seite wurde geschnitten, es gibt ein
  `next`" und auf Eintragsebene "die Nachricht wurde bei der Byte-Decke geschnitten". Eine
  gekappte Seite mit einer gekappten Nachricht darin setzt beide gleichzeitig.
- **Warum nicht hier gefixt:** IN-01 nennt `tools/mail.py` namentlich, `11-08-PLAN.md` führt
  `talk.py` nicht in `files_modified`, und die Umbenennung ist eine sichtbare
  Vertragsänderung, die in den Changelog von 0.1.8 gehört (Plan 11-09 schreibt ihn).
- **Vorschlag:** Eintragsfeld auf `message_truncated` umbenennen, analog zu
  `preview_truncated`, plus ein Test für den Fall, in dem beide Schlüssel gleichzeitig
  gesetzt sind.
