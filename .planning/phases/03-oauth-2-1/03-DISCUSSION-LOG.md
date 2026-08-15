# Phase 3: OAuth 2.1 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-08-15
**Phase:** 03-oauth-2-1
**Areas discussed:** AS-Architektur, Token-Design, DCR-Policy und Allowlist, Login Flow v2 Fallback, Robustheit und Drosselung, Discovery-Haertung, Staging und E2E, Testtiefe
**Mode:** --auto (Claude waehlte je Frage die empfohlene Option; Leitplanke: Owner-Vorgabe hoechste Sicherheit und Zuverlaessigkeit, 15.08.2026)

---

## AS-Architektur

| Option | Description | Selected |
|--------|-------------|----------|
| Eigener minimaler AS in der ExApp, Login via NC Login Flow v2 | Volle OAuth-2.1-/DCR-/PKCE-Kontrolle, kein Fremdsystem, Passwoerter bleiben bei Nextcloud | X |
| Nextcloud-oauth2-App nutzen | Kein DCR, kein PKCE-Zwang, nicht OAuth-2.1-konform; scheidet aus | |
| Externes IdP (Keycloak o.ae.) | Zweites System fuer Selfhoster, gegen Zero-Config-Anspruch | |

[auto] Q: "Wo lebt der Authorization Server?" -> "Eigener minimaler AS in der ExApp" (empfohlen; MCP-SDK-Bausteine zuerst pruefen)

## Token-Design

| Option | Description | Selected |
|--------|-------------|----------|
| Opake Tokens, Rotation, Reuse-Detection, App-Passwort-Bindung verschluesselt | Sofortiger Widerruf, nichts clientseitig zu validieren, konservativ | X |
| JWTs mit lokaler Validierung | Schneller, aber Widerruf nicht sofort und Validierungsfehler moeglich | |

[auto] Q: "Opak oder JWT, wie binden?" -> "Opak + Rotation + verschluesselte App-Passwort-Bindung" (Sicherheitsvorgabe)

## DCR-Policy und Client-Allowlist (AUTH-07)

| Option | Description | Selected |
|--------|-------------|----------|
| DCR an, Registry mit allowed-Flag + globaler Aus-Schalter + Allowlist-Modus | Plug-and-play (SC 1/2) UND Enforcement-Punkt ab dem ersten Commit | X |
| DCR default aus | Erfuellt SC 1/2 nicht (kein plug-and-play) | |
| DCR an ohne Registry | Owner-Entscheid 14.08. verletzt | |

[auto] Q: "DCR-Default und Enforcement?" -> "An, mit Registry/Schalter/Allowlist" (einzige Option, die SC 1/2 UND AUTH-07 erfuellt)

## Login Flow v2 Fallback

| Option | Description | Selected |
|--------|-------------|----------|
| NC Login Flow v2 (poll), Ergebnis App-Passwort auf AUTH-01-Pfad | NC fuehrt Login samt 2FA, niemand sieht das echte Passwort | X |
| Eigener Passwort-Prompt | Verboten (AUTH-02-Wortlaut, Phishing-Muster) | |

[auto] Q: "Fallback-Onboarding?" -> "Login Flow v2" (Spec- und Requirements-Vorgabe)

## Robustheit und Drosselung (SC 5)

[auto] Q: "Validierungspfad?" -> "Eigener Store + Cache, keine NC-Retries, 401 mit resource_metadata-Pointer, 429 mit Retry-After, fail-closed" (empfohlen)

## Discovery-Haertung

[auto] Q: "AR-02-06 jetzt schliessen?" -> "Ja, ^/\.well-known/ eng fassen, AS-Routen einzeln deklarieren" (Uebergabe aus 02-SECURITY.md)

## Staging und E2E

[auto] Q: "Wie SC 1/2 beweisen?" -> "Eigener spaeter Plan mit Owner-Checkpoint; Staging-Instanz = OWNER-ACTION (Domain+TLS)" (blockiert den Rest nicht)

## Testtiefe

[auto] Q: "Akzeptanzkriterien?" -> "Missbrauchstests verpflichtend: Replay, Widerruf, redirect_uri, PKCE-Downgrade, Audience-Mismatch, DCR-aus, Allowlist-Block" (Owner-Vorgabe)

---

## Deferred Ideas

- Admin-UI fuer Allowlist/DCR-Schalter -> Phase 4
- Datenfluss-Disclosure -> Phase 6
- Findling-Synergie -> BACKLOG.md BL-01..03

## Claude's Discretion

Modulstruktur des AS, Token-Store-Schema, exakte Lebensdauern, Consent-Wortlaut,
Plan-Reihenfolge (Haertung frueh, E2E spaet).
