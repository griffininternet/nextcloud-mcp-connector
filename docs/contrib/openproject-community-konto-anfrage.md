<!--
Entwurf einer Konto-Anfrage an die OpenProject-Community.

Status: Entwurf, nicht gesendet. Versand ausschliesslich durch den Owner.

Kanal:      offen und vom Owner zu waehlen. community.openproject.org ist das Forum, auf
            das das Repository nextcloud/integration_openproject verweist (die Issues dort
            sind abgeschaltet). Die Selbstregistrierung ist dort zu, deshalb geht diese
            Anfrage ueber den veroeffentlichten Kontaktweg von OpenProject und nicht ueber
            das Forum selbst. Dieser Entwurf nennt bewusst keine Adresse, weil in dieser
            Phase keine geprueft wurde.
Anlass:     christianlupus hat am 2026-08-28 im Nextcloud-Forum zu einem Konto in der
            OpenProject-Community geraten. Owner-Zusage vom selben Tag: "ich wuerde ein
            community account beantragen wenn es sein muss" (D-11).
Messwert:   Der Registrierungs-Einstieg von community.openproject.org antwortete am
            2026-08-28 mit HTTP 400 und dem Text "Registration not allowed".
Entstanden: Phase 17, Plan 17-08 (D-11), 2026-08-29

Kein Agent hat diesen Text gesendet, gepostet oder eingereicht. Kein Mailversand, kein
Browserversand, kein Playwright-Lauf, kein Registrierungsversuch ueber diesen Entwurf hinaus.

Der Text unterhalb dieses Kommentars ist die Anfrage, wie sie hinausgehen wuerde. Er ist
englisch, weil der Kanal englisch ist.
-->

Subject: Requesting an account for community.openproject.org

Hello,

I would like to ask a technical question in the OpenProject community forum, but I cannot create
an account: on 2026-08-28 the registration entry point of community.openproject.org answered with
HTTP 400 and the message "Registration not allowed". If self-registration is closed on purpose, I
would be grateful if you could tell me the intended way to get an account, or point me to the right
place for the question below.

Who is asking: I maintain an open source MCP connector for Nextcloud (AGPL-3.0, published in the
Nextcloud App Store). It lets an AI assistant read data from a Nextcloud strictly on behalf of the
signed-in user. I am currently looking at what it would take to do the same for OpenProject work
packages in an openDesk-style deployment, where both products sit in the same suite.

The question I want to ask: the Nextcloud app `integration_openproject` exposes OCS routes that run
under the signed-in user's own OpenProject connection. Going through that app instead of opening a
second OAuth client of my own would mean no additional secret in my container, no second consent
screen for the user, and no new outbound host, so it is clearly the better design if it is allowed.
What I cannot find out is whether those routes are meant as an interface that other apps may call,
or whether they are internal to that app's own front end and may change without notice. I asked in
the Nextcloud forum first, since the app's repository has issues disabled and points to
community.openproject.org, and the answer there was that the same question went unanswered in the
community chat as well, with the advice to ask here.

I am happy to ask this in public in the forum rather than by mail, which is why I am asking for an
account rather than for an answer. If the forum is the wrong place for a question about a Nextcloud
side app, please say so and I will take it wherever it belongs.

Thank you,
Khaled Cherif
