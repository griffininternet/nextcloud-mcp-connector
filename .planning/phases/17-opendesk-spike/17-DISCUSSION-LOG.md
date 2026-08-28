# Phase 17: openDesk-Spike - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-08-28
**Phase:** 17-opendesk-spike
**Areas discussed:** Messumgebung und Kosten, Messtiefe Weg 1 (OAuth), OIDC-Bruchstelle S5, Ablage von Bericht und Fragenliste
**Ablauf-Hinweis:** Die Fragen wurden je Bereich gebündelt gestellt (zwei bis drei Fragen pro Aufruf) statt in vier Einzelrunden, um die Owner-Zeit zu schonen. Inhaltlich wurde jeder Bereich vollständig entschieden.

---

## Messumgebung und Kosten

### Frage 1: OD-01 (Installierbarkeit) — wie soll der Befund entstehen?

| Option | Description | Selected |
|--------|-------------|----------|
| Nur Quellen, kein Cluster | helmfile-Werte, app_api-Doku, NC-Doku zu manual_install; jede Hürde mit Zitat oder als ISV-Frage | ✓ |
| Quellen + lokaler k3s-Versuch | Zusätzlich lokaler k3s/kind mit Nextcloud-Subchart, manual_install praktisch probieren | |
| Wegwerf-Cloud-Box mit k3s | Echter Installationsversuch auf gemieteter Box, danach rückstandsfreier Abbau | |

**User's choice:** Nur Quellen, kein Cluster
**Notes:** openDesk läuft lokal ohnehin nicht vollständig; der Aufwand hätte den Befund nicht verbessert.

### Frage 2: OD-02 — welche Messumgebung darf entstehen?

| Option | Description | Selected |
|--------|-------------|----------|
| Lokal Docker, gepinnte Versionen | NC 33.0.7 + integration_openproject + OpenProject Community 17.7.x | ✓ |
| Lokal Docker, nur OpenProject | Nur Weg 1 messbar, Weg 0 bliebe Quellenlesen | |
| Cloud-Box für beides | Mehr RAM, dafür Kosten und Abbaupflicht | |

**User's choice:** Lokal Docker, gepinnte Versionen
**Notes:** Nextcloud bewusst auf dem openDesk-Stand 33.0.7, nicht auf den 34.0.3 der bisherigen Nachweise.

### Frage 3: Leitplanke für gemietete Infrastruktur

| Option | Description | Selected |
|--------|-------------|----------|
| Keine Box in dieser Phase | Alles lokal oder aus Quellen, Nicht-Messbares wird "ungemessen" gebucht | ✓ |
| Box erlaubt, Abbau im selben Plan | Kleinste Größe, Abbau samt DNS und Gegenprobe als eigene Aufgabe | |
| Box erlaubt, du fragst vorher | Bedarf mit Preis vorlegen, auf Freigabe warten | |

**User's choice:** Keine Box in dieser Phase
**Notes:** Deckt sich mit Erfolgskriterium 3 der Roadmap.

---

## Messtiefe Weg 1 (OAuth)

### Frage 1: Wie tief wird Weg 1 gemessen?

| Option | Description | Selected |
|--------|-------------|----------|
| Voller Consent-Flow, echte Werte | OAuth-Anwendung anlegen, Code über Browser holen, PKCE/expires_in/Refresh messen | ✓ |
| Nur PKCE-Annahme prüfen | Ein Aufruf an /oauth/authorize plus Metadaten, Rest bleibt ungemessen | |
| Voller Flow, Consent per Hand | Wie Option 1, Browser-Klick durch den Owner | |

**User's choice:** Voller Consent-Flow, echte Werte
**Notes:** OD-02 verlangt drei Messwerte; nur so entstehen alle drei.

### Frage 2: Negativbeweis mit zwei Nutzerkonten

| Option | Description | Selected |
|--------|-------------|----------|
| Pflicht auf beiden Wegen | Zwei Konten in Nextcloud und OpenProject, Sicht hängt am angemeldeten Nutzer | ✓ |
| Nur auf dem Weg, der trägt | Halber Aufwand, Rückfallweg unbelegt | |
| Ein Konto reicht im Spike | Belegt nur Erreichbarkeit, nicht das Kernversprechen | |

**User's choice:** Pflicht auf beiden Wegen
**Notes:** Entspricht der ausdrücklichen Empfehlung der Recherche.

### Frage 3: SSRF-Grenze gegen internen Dienstnamen

| Option | Description | Selected |
|--------|-------------|----------|
| Ja, mit Negativkatalog | Gemessen, mit den Fällen aus dem bestehenden Katalog | ✓ |
| Ja, aber nur lesen statt messen | Code auswerten und herleiten | |
| Nicht in dieser Phase | Als offene Frage in den Bericht | |

**User's choice:** Ja, mit Negativkatalog
**Notes:** Teilstück von OD-02, hätte sonst gefehlt.

---

## OIDC-Bruchstelle S5

### Frage 1: Wie weit gehen bei S5?

| Option | Description | Selected |
|--------|-------------|----------|
| Keycloak + user_oidc lokal aufsetzen | S5 messen und dabei die Live-Repro für user_oidc#925 gewinnen | ✓ |
| S5 ungemessen buchen | Nur Code-Beleg, im Bericht als "ungemessen", als ISV-Frage | |
| Kann-Ziel am Ende | Nur falls nach den Pflichtmessungen Luft bleibt | |

**User's choice:** Keycloak + user_oidc lokal aufsetzen
**Notes:** Es ist die Frage, an der Weg 0 kippt; sie entscheidet den Architekturweg.

### Frage 2: Wann darf user_oidc#925 raus?

| Option | Description | Selected |
|--------|-------------|----------|
| Nur mit geglückter Repro, Entwurf im Repo | Praktischer Fehlversuch samt Protokoll als Voraussetzung, Owner sendet | ✓ |
| Auch mit dokumentiertem Fehlversuch senden | Senden mit ehrlicher Angabe, was nicht gemessen wurde | |
| In dieser Phase gar nicht | Issue bleibt komplett draußen | |

**User's choice:** Nur mit geglückter Repro, Entwurf im Repo
**Notes:** Regel aus context_agent#230 bleibt bindend.

---

## Ablage von Bericht und Fragenliste

### Frage 1: Wohin gehört der Spike-Bericht?

| Option | Description | Selected |
|--------|-------------|----------|
| docs/spike-opendesk.md im Repo | Muster spike-dav / spike-discovery / spike-mail, Rohmesswerte als Abschnitt darin | ✓ |
| Repo-Bericht + interne Rohdaten | Kurzbericht in docs/, Protokolle in .planning/ | |
| Nur .planning-intern | Nichts im öffentlichen Teil des Repos | |

**User's choice:** docs/spike-opendesk.md im Repo
**Notes:** docs/ liegt nicht im Store-Asset, Erfolgskriterium 5 bleibt gewahrt.

### Frage 2: Wohin die ISV-Fragenliste (OD-03)?

| Option | Description | Selected |
|--------|-------------|----------|
| Desktop-Dossier ergänzen + Repo-Kopie | Liste im Dossier für den Call, Abschnitt im Bericht für die Versionierung | ✓ |
| Nur ins Desktop-Dossier | Ein Ort, dafür unversioniert | |
| Nur im Repo | Versioniert, aber beim Call unpraktisch | |

**User's choice:** Desktop-Dossier ergänzen + Repo-Kopie

### Frage 3: Kanal für die OCS-Frage (Weg 0)

| Option | Description | Selected |
|--------|-------------|----------|
| Anfrage entwerfen, du sendest | Antwort an christianlupus im Forum plus Konto-Anfrage an die OpenProject-Community | ✓ |
| Messen statt fragen | Kanal liegen lassen, Frage auf die ISV-Liste | |
| Beides | Messen und Kanal parallel weiterverfolgen | |

**User's choice:** Anfrage entwerfen, du sendest
**Notes:** Auslöser war die Forumsantwort von christianlupus am 28.08. (im Community-Chat selbst keine Antwort erhalten, rät zu einem Community-Konto). Owner-Zusage im Anschluss: "ich würde ein community account beantragen wenn es sein muss". Selbstregistrierung dort liefert HTTP 400 "Registration not allowed", deshalb Anfrage statt Anmeldung.

---

## Abschlussfrage: Was passiert, wenn Weg 0 als tragend gemessen wird?

| Option | Description | Selected |
|--------|-------------|----------|
| Nur berichten, kein Code | Bericht plus Fragenliste; Weg-0-Client ist OD-04 in v2.0 | ✓ |
| Bericht + Wegwerf-Prototyp | Zusätzliches Skript außerhalb des Paketbaums | |
| Noch einen Bereich besprechen | — | |

**User's choice:** Nur berichten, kein Code
**Notes:** Hält Erfolgskriterium 5 wörtlich.

---

## Claude's Discretion

- Aufteilung in Pläne und Wellen, Form und Ort der Compose-Dateien (außerhalb von `src/`),
  Aufbau der Messprotokolle, Reihenfolge innerhalb von OD-02, Wortwahl der beiden Entwürfe

## Deferred Ideas

- Weg-0-Client und `openproject_browse` samt `wp:<id>` für `fetch`: OD-04, v2.0, nach dem ISV-Call
- Wegwerf-Prototyp des gewinnenden Wegs: bewusst abgelehnt
- k3s- oder Cloud-Installationsversuch für openDesk: erst wenn der ISV-Call einen Weg nennt
- Rückkanal OpenProject-Community zur OCS-Frage: läuft nach dieser Phase weiter
