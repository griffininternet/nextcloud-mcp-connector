# Deferred items, phase 18

Out of scope discoveries, logged and deliberately not fixed.

## 2026-08-29, plan 18-07

- `tests/unit/test_oauth_consent.py::test_a_flood_of_accepted_authorization_requests_ends_in_429`
  wurde in einem von drei Läufen der vollen Suite rot und war einzeln sowie in zwei weiteren
  vollen Läufen grün. Der Fall zählt 23 Anfragen gegen ein Fenster von 60 Sekunden und ist
  damit zeitabhängig. Keine Berührung mit Plan 18-07: er baut seine eigene `Throttle` und
  kennt weder `entry_exapp` noch das Audit-Modul.
- Die drei Variablen `NC_MCP_AUDIT_LOG`, `NC_MCP_AUDIT_RETENTION_DAYS` und
  `NC_MCP_AUDIT_MAX_BYTES` haben keinen `<environment-variables>`-Eintrag in
  `appinfo/info.xml`. Plan 18-07 verlangt `appinfo/` ausdrücklich unberührt; der Weg eines
  Administrators zum Schalter ist das Admin-Formular, also genau der Weg, den BL-06 fordert.
  Ein Eintrag wäre die zusätzliche Bequemlichkeit für eine von Hand aufgesetzte
  Docker-Installation.
