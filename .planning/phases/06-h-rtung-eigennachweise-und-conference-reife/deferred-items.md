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

- **`scripts/acceptance_all_tools.py` erwartet 15 Werkzeuge, der Server hat 16** (aufgefallen
  in 06-10). `EXPECTED_TOOLS = 15` stammt aus Phase 1, das sechzehnte Werkzeug
  (`prepare_context`) kam spaeter, und die Namensliste des Skripts kennt es nicht. Alle
  fuenfzehn aufgerufenen Werkzeuge antworten `OK`, aber die Zeile
  `FAIL tools/list expected 15 tools, got 16` faerbt den Lauf rot und der Rueckgabewert ist
  `1`. Nicht in 06-10 behoben, weil dieser Plan `docs/` und die Messdatei aendert und ein
  Abnahmeskript aus Phase 1 keinen Nebenbei-Eingriff verdient. Erledigen: die Erwartung an
  `scripts/check_tool_budget.py` binden oder auf 16 setzen und `prepare_context` in die
  Namensliste aufnehmen, mit einem eigenen Lauf als Beleg. Bis dahin sagt
  `docs/conference-demo.md` in Schritt 5 woertlich, was die Zeile bedeutet.
