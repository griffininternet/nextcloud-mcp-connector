<!--
Entwurf eines Kommentars zu gitlab.opencode.de bmi/opendesk/deployment/opendesk#381
("Governance & contribution process for Univention Intercom Service (ICS)").

Status: Entwurf, nicht gesendet. Versand ausschließlich durch den Owner
(openCode-Konto erforderlich; Konto-Frage klärt der Owner).

Anlass:   Das Issue ist ausdrücklich ein Discussion-Starter zur Governance-Lücke
          zwischen openDesk (GitLab, opencode.de) und Univention (GitHub) am
          Beispiel des seit Juli in Triage hängenden PR
          univention/intercom-service#4. Es stellt offene Fragen zu CLA-Angleichung,
          Review-SLAs und Maintainerschaft. Stand geprüft am 2026-08-31.
Warum wir: ICS ist der sichtbare Weg, wie Dritt-Anwendungen in openDesk kommen
          (openDesk Edu nutzt ihn für OpenCloud, SOGo, ILIAS). Als externer
          App-Entwickler, der die openDesk-Integrierbarkeit gemessen hat, sind wir
          genau die Zielgruppe der gesuchten Governance. Erst Beitragender werden,
          dann Lösungen anbieten.
Belege:   Alle Messwerte stehen versioniert in docs/spike-opendesk.md
          (github.com/street1983nk/nextcloud-mcp-connector).

Kein Agent hat diesen Text gesendet, gepostet oder eingereicht.

Der Text unterhalb dieses Kommentars ist der Kommentar, wie er im Issue erscheinen
würde. Englisch, weil der bestehende Thread englisch geführt ist.
-->

Outside data point, if it helps the discussion: we develop a Nextcloud ExApp (an MCP
connector, in the public app store) and spent the last weeks measuring what it would take
to run a third-party component inside openDesk, from source rather than from assumptions.
Three observations that bear on the governance question raised here:

1. For a component author looking at openDesk v1.18.0 today, ICS is the only visible,
   working path for third-party integration. The Nextcloud app store is disabled in the
   image, and AppAPI appears nowhere in this deployment project, so the app-level
   extension route that upstream Nextcloud offers does not exist here in practice. That
   makes the governance of ICS contributions more consequential than the issue text
   already states: it is not one integration path among several, it is currently the
   only one that has shipped anywhere (Edu).

2. The friction described here is visible from outside and it filters who contributes.
   Across the openDesk projects on opencode.de there are, as of late August, zero issue
   titles mentioning MCP, audit, search or federation from external component authors.
   We do not read that as absence of interest, we read it as the funnel this issue
   describes: two platforms, two CLA regimes, no documented review SLA, and a stalled
   reference PR as the visible precedent of what happens to an outside contribution.

3. As a concrete data point for the CLA question: we are willing to sign a CLA to
   contribute, and we still hesitated, because it is two of them, on two platforms,
   with unclear effect on each other. One documented statement, "contributions to
   ICS follow process X, CLA Y, expected first response within Z days", would have
   removed that hesitation entirely. The SLA does not need to be short, it needs to
   exist.

On the question whether ICS should move into the openDesk base with shared
maintainership: from the outside, what matters more than where the repository lives is
that exactly one contribution process is authoritative and written down. A mirror with
divergent forks (as described for Edu) is the expensive alternative to that one sentence.

We plan further measured contributions around identity across components (there is a
gap where an ExApp without PHP code cannot obtain an audience-correct token for a
sister component without a browser session; we have it measured and will file it
through the appropriate upstream channel). If a defined path for third-party component
authors comes out of this discussion, we would be glad to be one of its first users,
CLA included. Measurements behind the statements above are versioned here:
https://github.com/street1983nk/nextcloud-mcp-connector/blob/main/docs/spike-opendesk.md
