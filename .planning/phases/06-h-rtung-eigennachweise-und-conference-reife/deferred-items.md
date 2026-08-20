# Phase 6: aufgeschobene Punkte

Was in dieser Phase auffiel, aber nicht zum Auftrag des jeweiligen Plans gehoerte. Jede
Zeile nennt den Fund, den Plan, in dem er auffiel, und was mit ihm passieren soll.

## Offen

- **`uv.lock` traegt die eigene Projektversion 0.1.0, das Repo steht auf 0.1.2** (aufgefallen
  in 06-01). Der erste `uv run` einer Sitzung synchronisiert und schreibt dabei
  `version = "0.1.2"` in den `nextcloud-mcp-connector`-Block der Lockdatei, was als
  ungefragte Aenderung im Arbeitsbaum erscheint. Keine Abhaengigkeit ist betroffen, nur die
  Selbstangabe des eigenen Pakets: der Versionssprung auf 0.1.2 wurde ohne erneutes Locken
  gemacht. In 06-01 bewusst zurueckgesetzt (`git checkout -- uv.lock`), weil dieser Plan
  laut Verifikation `pyproject.toml` und `uv.lock` unberuehrt lassen sollte. Erledigen:
  einmal `uv lock` in einem Plan, der ohnehin an der Paketmetadaten-Ecke arbeitet, oder im
  Zuge eines 0.1.3-Release.
