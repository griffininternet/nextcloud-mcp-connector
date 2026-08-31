<!--
Entwurf eines Kommentars zu gitlab.opencode.de bmi/opendesk/deployment/opendesk#381
("Governance & contribution process for Univention Intercom Service (ICS)").

Status: Entwurf, nicht gesendet. Versand ausschließlich durch den Owner.

Anlass:   Das Issue ist ein Discussion-Starter zur Governance-Lücke zwischen openDesk
          (GitLab, opencode.de) und Univention (GitHub). WICHTIGE ENTWICKLUNG, im Issue
          selbst nachgelesen am 2026-08-31 (eingeloggt): der Referenz-PR
          univention/intercom-service#4 wurde am 14. Juli GEMERGT (Release 2.24.0), die
          CLA-Frage wurde "resolved or waived", und der Issue-Autor schreibt am 18.07.
          ausdrücklich "informal channels worked well here. Still worth discussing formal
          processes for future contributions." Am 28.07. folgte ein Vendor-Independence-
          Umbau (nubus-common/bitnami raus, Mirror-Forks). Eine erste Entwurfsfassung
          dieses Kommentars nannte den PR noch "stalled"; das war der Stand der Recherche
          vom 29.08. und ist ueberholt. Diese Fassung dockt am Zitat des Autors an.
Warum wir: ICS ist der sichtbare Weg, wie Dritt-Anwendungen in openDesk kommen. Als
          externer App-Entwickler, der die openDesk-Integrierbarkeit gemessen hat, sind
          wir die Zielgruppe der gesuchten Governance.
Belege:   Messwerte versioniert in docs/spike-opendesk.md
          (github.com/street1983nk/nextcloud-mcp-connector).

Kein Agent hat diesen Text gesendet, gepostet oder eingereicht; das Einfuegen in die
Kommentarbox geschah auf ausdrueckliche Owner-Anweisung, der Owner klickt selbst.

Der Text unterhalb dieses Kommentars ist der Kommentar, wie er im Issue erscheinen
wuerde. Englisch, weil der Thread englisch gefuehrt ist.
-->

Outside data point for the "formal processes for future contributions" part, since the
happy ending above was reached through informal channels: we develop a Nextcloud ExApp
(an MCP connector, in the public app store) and spent the last weeks measuring, from
source, what it would take to run a third-party component inside openDesk. Three
observations:

1. For a component author looking at openDesk v1.18.0 today, ICS is the only
   third-party integration path that has shipped anywhere (Edu, with OpenCloud, SOGo
   and ILIAS). The Nextcloud app store is disabled in the image, and AppAPI appears
   nowhere in this deployment project, so the app-level extension route that upstream
   Nextcloud offers does not exist here in practice. That makes ICS contribution
   governance more consequential than one chart parameter: it is the front door.

2. The friction this issue describes filters who even shows up. Across the openDesk
   projects on opencode.de there are, as of late August, zero issue titles from
   external component authors mentioning MCP, audit, search or federation. We do not
   read that as absence of interest. We read it as the funnel: two platforms, two CLA
   regimes, and no written expectation of what happens to an outside contribution.
   That the upstream PR (intercom-service PR 4) got merged is genuinely good news,
   but from the outside that outcome was invisible until one logs in and reads this
   thread; the documented state was still "in triage". (Im GitLab-Kommentar bewusst
   ohne Raute vor der 4, weil GitLab "#4" auf das lokale Work-Item 4 verlinken wuerde.)

3. A concrete data point for the CLA and SLA questions: we are willing to sign a CLA
   to contribute, and we still hesitated, because it is two of them, on two platforms,
   with unclear effect on each other. One documented sentence, "contributions to ICS
   follow process X, CLA Y, expected first response within Z days", would have removed
   that hesitation entirely. The SLA does not need to be short. It needs to exist and
   to be findable without reading a closed thread.

We plan further measured contributions around identity across components (there is a
gap where an ExApp without PHP code cannot obtain an audience-correct token for a
sister component without a browser session; we have it measured and will file it
through the appropriate upstream channel). If a defined path for third-party component
authors comes out of this discussion, we would be glad to be one of its first users,
CLA included. The measurements behind the statements above are versioned here:
https://github.com/street1983nk/nextcloud-mcp-connector/blob/main/docs/spike-opendesk.md
