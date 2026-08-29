<!--
Entwurf einer Antwort an christianlupus im Nextcloud-Forum.

Status: Entwurf, nicht gesendet. Versand ausschliesslich durch den Owner.

Kanal:      https://help.nextcloud.com/t/integration-openproject-are-the-ocs-routes-a-public-api-for-other-apps/248660
            (Kategorie Development, Konto street1983nk besteht bereits)
Anlass:     christianlupus hat am 2026-08-28 auf den Ausgangsbeitrag geantwortet. Er hat
            dieselbe Frage im Community-Chat selbst gestellt und keine Antwort bekommen
            und raet zu einem Konto in der OpenProject-Community.
Entstanden: Phase 17, Plan 17-08 (D-11), 2026-08-29
Belege:     Jede technische Aussage unten steht mit Fassung und Messwert in
            docs/spike-opendesk.md: die Routenzaehlung in Abschnitt 2.1, die Messwerte
            S1 bis S4 ebenda, der OIDC-Befund in S5a bis S5c, die drei Luecken und
            file-links in Abschnitt 3.3.

Kein Agent hat diesen Text gesendet, gepostet oder eingereicht. Kein Browserversand,
kein Playwright-Lauf, kein Forums-Aufruf.

Der Text unterhalb dieses Kommentars ist die Antwort, wie sie im Forum erscheinen wuerde.
Er ist englisch, weil der Kanal englisch ist.
-->

Thanks, that is useful in itself: if the question did not get an answer in the community chat
either, then it is not just me failing to find the documented answer. I will follow your advice
and ask for an account in the OpenProject community.

Meanwhile I stopped guessing and measured, so I can narrow the question down. On a pinned local
setup (Nextcloud 33.0.7, `integration_openproject` 3.1.1, OpenProject 17.7.2) the OCS surface does
answer for an ExApp that acts as the signed-in user through AppAPI impersonation, with no cookie
and no app password in the request: `GET /api/v1/url` returns the OCS envelope with the instance
URL, and `GET /api/v1/configuration` returns 200 with real data for a connected account and 401
with an empty message for an account that never connected OpenProject, which is
`validatePreRequestConditions()` doing exactly what it should. Permissions are the user's own, not
the app's: searching for a work package that lives in a private project returns one hit for the
member and zero hits for the other account, same call, same headers. In the `oauth2` setup the
server also refreshes the expired user token by itself, so the call keeps working without a
browser session; in the `oidc` setup the same call drops to 401 once the cached token expires,
because the token exchange in `user_oidc` reads the login token from the session and an
impersonated request does not have one. Counted from `appinfo/routes.php` at tag `v3.1.1` there are
17 OCS routes, and the three gaps I mentioned in my first post are still there at that tag: no
route to read one work package by id, none for comments, and none for "work assigned to me". The
one route that takes a work package id at all is
`GET /api/v1/work-packages/{id}/file-links`, which is the Nextcloud-facing part I care about most.

So the technical part works, and the only thing I still cannot answer is the one I opened with: are
these OCS routes meant as an interface that other apps may call, or are they internal plumbing for
your own front end that may change without notice? I am not asking for new routes here and not
asking for a promise about the three gaps. I am asking whether building on the existing 17 would be
building on something that is expected to stay, so that I know whether to design around it or not.

If anyone reading this knows where such a statement would live for a Nextcloud integration app in
general, that would help too. I could not find a written rule for OCS routes of an app that is not
the server itself.
