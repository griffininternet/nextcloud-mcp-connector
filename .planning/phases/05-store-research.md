# Phase 05: App-Store-Einreichung ExApp mcp_connector, Recherche

Stand: 2026-08-17. Ziel: belastbare Checkliste fuer die Store-Einreichung der ExApp
`mcp_connector` (ghcr.io-Docker-Image + `appinfo/info.xml`), unabhaengig vom noch
ausstehenden Zertifikat. Alle Aussagen sind an echten Dateien/Repos verifiziert.

Kurz-Kontext unserer App: `<external-app>` mit `<docker-install>` (ghcr.io),
`<routes>`, `<environment-variables>`; Ziel Nextcloud 32 bis 34; App-ID `mcp_connector`;
Lizenz AGPL-3.0.

---

## Frage 1: XSD-Schema-Problem und korrekte info.xml-Struktur (WICHTIGSTE FRAGE)

### Kernbefund: Unsere routes-Platzierung ist RICHTIG. Das oeffentliche XSD ist unvollstaendig, und der Store entfernt `<routes>` vor der Validierung.

**a) Kennt das oeffentliche info.xsd das `<routes>`-Element in `<external-app>`? NEIN.**

Das Schema unter `https://apps.nextcloud.com/schema/apps/info.xsd` (identisch mit der
Store-Quelle `nextcloudappstore/api/v1/release/info.xsd`, Zeilen 751 bis 758) definiert:

```xml
<xs:complexType name="external-app">
    <xs:sequence>
        <xs:element name="docker-install" type="docker-install" minOccurs="0" maxOccurs="1"/>
        <xs:element name="scopes" type="scopes" minOccurs="0" maxOccurs="1"/>
        <xs:element name="system" type="xs:boolean" minOccurs="0" maxOccurs="1"/>
        <xs:element name="environment-variables" type="environment-variables" minOccurs="0" maxOccurs="1"/>
    </xs:sequence>
</xs:complexType>
```

Es gibt im gesamten XSD KEIN `<routes>`- und KEIN `<k8s-service-roles>`-Element. Deshalb
schlaegt eine direkte Validierung unserer Roh-info.xml gegen dieses XSD fehl mit genau der
Meldung "Element 'routes': This element is not expected". Das ist erwartbar und kein Fehler
in unserer Datei.

**b) Warum der Store unsere Datei trotzdem akzeptiert (der entscheidende Mechanismus):**

Der Store validiert NICHT die Roh-info.xml. In `nextcloudappstore/api/v1/release/parser.py`
(`parse_app_metadata`) laeuft VOR der Schemapruefung ein XSLT-Vorlauf `pre-info.xslt`
(`schema.assertValid(pre_transformed_doc)`). Diese `pre-info.xslt` baut das `<info>`-Dokument
neu auf und kopiert fuer `external-app` NUR bekannte Kinder in fester Reihenfolge:

```xml
<xsl:template match="external-app">
    <external-app>
        <xsl:apply-templates select="docker-install"/>
        <xsl:copy-of select="scopes"/>
        <xsl:copy-of select="system"/>
        <xsl:apply-templates select="environment-variables"/>
    </external-app>
</xsl:template>
```

Kommentar im Stylesheet: "reformat info.xml to have everything in order and excluded unknown
elements". Das heisst konkret:
- `<routes>` und `<k8s-service-roles>` werden vor der Validierung STILL ENTFERNT. Der Validator
  sieht sie nie. Deshalb ist unsere Reihenfolge `docker-install > routes > environment-variables`
  vollkommen unkritisch: Der XSLT-Vorlauf greift die Elemente einzeln per Namen heraus und ordnet
  sie selbst; die Reihenfolge in unserer Roh-Datei spielt fuer den Store keine Rolle.
- Der Store liest `<routes>` also gar nicht aus. Ausgewertet werden `<routes>` und
  `<k8s-service-roles>` erst zur Installationszeit von AppAPI in der Nextcloud-Instanz, nicht vom
  App Store.

**Fazit Frage 1:** Weder ist unsere `routes`-Platzierung falsch, noch muss sie verschoben werden.
Das oeffentliche/Store-XSD ist fuer ExApp-Laufzeitelemente bewusst unvollstaendig; der Store
strippt die Unbekannten via `pre-info.xslt`. Der Validierungsfehler entsteht nur, weil wir lokal
direkt gegen `info.xsd` pruefen, was der Store so nie tut.

**c) Verifikation an echten, veroeffentlichten ExApps:**

Beispiel 1, `nextcloud/context_chat_backend` (`appinfo/info.xml`, live im Store): nutzt `<routes>`
GENAU in unserer Reihenfolge, plus ein weiteres store-unbekanntes Element `<k8s-service-roles>`:

```xml
<external-app>
    <docker-install>
        <registry>ghcr.io</registry>
        <image>nextcloud-releases/context_chat_backend</image>
        <image-tag>5.5.0-beta0</image-tag>
    </docker-install>
    <routes>
        <route>
            <url>downloadLogs</url>
            <verb>GET</verb>
            <access_level>ADMIN</access_level>
            <headers_to_exclude>[]</headers_to_exclude>
        </route>
    </routes>
    <environment-variables>
        <variable> ... </variable>
    </environment-variables>
    <k8s-service-roles> ... </k8s-service-roles>
</external-app>
```

Das belegt: `docker-install > routes > environment-variables` ist die praxiserprobte Anordnung,
und der Store publiziert diese App trotz `routes`/`k8s-service-roles` problemlos.

Beispiel 2, `nextcloud/llm2` (`appinfo/info.xml`, live im Store): fuehrt KEINE `routes`, nutzt
dafuer `<system>` und die schema-konforme Reihenfolge:

```xml
<external-app>
    <docker-install>
        <registry>ghcr.io</registry>
        <image>nextcloud/llm2</image>
        <image-tag>2.8.0</image-tag>
    </docker-install>
    <system>false</system>
    <environment-variables>
        <variable> ... </variable>
    </environment-variables>
</external-app>
```

Ergebnis: `routes` steht NICHT im Store-Schema, wird aber von realen ExApps in info.xml gefuehrt
und vom Store toleriert (weggestrippt). Apps ohne `routes` (llm2) sind ebenso gueltig.

**d) Gibt es ein separates/erweitertes XSD fuer ExApps, gegen das der Store validiert? NEIN.**

Der Store benutzt nur ein einziges Schema (`info.xsd`) plus den `pre-info.xslt`-Vorlauf. Ein
erweitertes ExApp-XSD, das `routes`/`k8s-service-roles` kennt, existiert im Store-Repo nicht. Die
verbindliche Struktur dieser Laufzeitelemente ergibt sich aus AppAPI selbst (dessen info.xml-Parser)
und aus den Referenz-ExApps, nicht aus einem oeffentlichen Store-XSD.

### Praktische Konsequenz fuer uns
- info.xml so lassen: `docker-install`, dann `routes`, dann `environment-variables` ist korrekt.
- Lokale Validierung gegen das rohe `info.xsd` wird immer bei `routes` meckern. Das ist ein
  falsch-positiver Fehler. Um so zu validieren wie der Store, muss man zuerst `pre-info.xslt`
  anwenden (Unbekannte entfernen) und danach gegen `info.xsd` pruefen. Alternativ: `routes` und
  `k8s-service-roles` fuer den reinen Schema-Selbsttest temporaer entfernen.
- Struktur eines `<route>` (verifiziert an context_chat_backend): `url`, `verb`,
  `access_level` (z. B. `ADMIN`, `USER`, `PUBLIC`), `headers_to_exclude` (z. B. `[]`).

Quellen:
- https://apps.nextcloud.com/schema/apps/info.xsd
- https://github.com/nextcloud/appstore/blob/master/nextcloudappstore/api/v1/release/info.xsd (Zeilen 751 bis 758)
- https://github.com/nextcloud/appstore/blob/master/nextcloudappstore/api/v1/release/pre-info.xslt (Template `external-app`)
- https://github.com/nextcloud/appstore/blob/master/nextcloudappstore/api/v1/release/parser.py (`parse_app_metadata`)
- https://github.com/nextcloud/context_chat_backend/blob/master/appinfo/info.xml
- https://github.com/nextcloud/llm2/blob/main/appinfo/info.xml

---

## Frage 2: Release- und Signaturprozess fuer ExApps

**Kernbefund: Der Prozess ist identisch zu klassischen PHP-Apps. Signiert wird ein tar.gz-Release-Archiv,
NICHT das Docker-Image. Das Docker-Image wird nur per `docker-install` referenziert und von AppAPI
zur Installationszeit aus ghcr.io gezogen.**

**a) Was wird signiert und wie?**
- Signiert wird das Release-Archiv (`app.tar.gz`), das eine einzelne oberste Ordnerebene mit
  `appinfo/info.xml` enthaelt. Bei einer ExApp ist das ein schlankes Metadaten-Tarball
  (Repo-Inhalt bzw. mindestens `appinfo/`), NICHT das Container-Image.
- Signatur (SHA-512 ueber die tar.gz-Datei, base64):
  `openssl dgst -sha512 -sign ~/.nextcloud/certificates/mcp_connector.key /pfad/mcp_connector.tar.gz | openssl base64`

**b) Upload/Einreichung:**
- Web: `https://apps.nextcloud.com/developer/apps/releases/new`, oder REST-API
  (`POST` an `https://apps.nextcloud.com/api/v1/apps/releases`).
- Uebergeben werden: Download-URL (HTTPS-Link auf das tar.gz, z. B. GitHub-Release-Asset) und die
  base64-Signatur; optional der Nightly/Pre-Release-Schalter.
- Der Store laedt das Archiv von der URL, prueft die Signatur gegen das hinterlegte Zertifikat,
  prueft die Struktur (genau ein Top-Level-Ordner, Kleinbuchstaben/Unterstriche, enthaelt
  `appinfo/info.xml`) und validiert die Metadaten (nach `pre-info.xslt`) gegen `info.xsd`.

**c) Rolle des CSR-Zertifikats (app-certificate-requests):**
- Einmalig pro App-ID: Key + CSR erzeugen
  `openssl req -nodes -newkey rsa:4096 -keyout mcp_connector.key -out mcp_connector.csr -subj "/CN=mcp_connector"`,
  Ablage in `~/.nextcloud/certificates/`.
- Den Inhalt von `mcp_connector.csr` als Pull Request in `nextcloud/app-certificate-requests`
  einreichen. Nach Merge/Signatur erhaelt man das oeffentliche Zertifikat `mcp_connector.crt`.
- App einmalig registrieren (Web `.../developer/apps/new` oder API) mit dem Zertifikatsinhalt plus
  einem Besitznachweis-Signature ueber die App-ID:
  `echo -n "mcp_connector" | openssl dgst -sha512 -sign ~/.nextcloud/certificates/mcp_connector.key | openssl base64`.
- Danach signiert derselbe private Key jedes Release-Archiv. Das Zertifikat ist also der Vertrauensanker;
  ohne gemergten CSR ist keine Einreichung moeglich (das ist genau unser offener Punkt).

Quellen:
- https://nextcloudappstore.readthedocs.io/en/latest/developer.html (Certificates, Register, Upload a release)
- https://github.com/nextcloud/app-certificate-requests
- https://docs.nextcloud.com/server/latest/developer_manual/exapp_development/development_overview/ExAppDevelopmentSteps.html

---

## Frage 3: Pflicht-Metadaten fuer die Store-Listung

Verifiziert an `docs.nextcloud.com/.../app_development/info.html` und am Store-XSLT/XSD.

**Pflichtfelder in info.xml** (sonst schlaegt Validierung/Listing fehl):
- `id`, `name`, `description`, `version`, `licence`, `author`, `bugs`,
  `dependencies/nextcloud` (mit `min-version`/`max-version`).
- `summary` ist optional (faellt sonst auf `description` zurueck), sollte aber gesetzt sein.
- `category`: gueltige Werte sind `customization, files, games, integration, monitoring, multimedia,
  office, organization, security, social, tools`. **"integration" ist gueltig** und passt fuer einen
  MCP-Connector. Nur genau diese Werte sind erlaubt.

**Screenshots:**
- `<screenshot>` erwartet eine HTTPS-URL auf ein Bild (optionales Attribut `small-thumbnail`).
- Nicht formal erzwungen, aber faktisch fuer eine gute Listung erwartet. Store-Empfehlung: PNG/JPG,
  quer, breit genug. Ohne Screenshot wirkt die Listung leer (siehe Memory-Erfahrung).

**Logo/Icon:**
- Kein eigenes Pflichtfeld in info.xml. Das App-Icon kommt aus dem App-Paket
  (`img/app.svg`/`app-dark.svg`) bzw. wird ueber `<screenshot>` bebildert. Fuer eine ExApp ohne
  klassisches PHP-Frontend genuegt ein Repository-Logo als `<screenshot>`.

**Mehrsprachige Beschreibung:**
- `name` und `description` unterstuetzen Uebersetzungen via `lang`-Attribut
  (`<description lang="de">...</description>`). Englisch MUSS vorhanden sein
  (`validate_english_present` im Parser erzwingt das). Deutsch optional zusaetzlich.

**Changelog-Format:**
- `CHANGELOG.md` im Projekt-Root, seit Nextcloud 29 auch sprachspezifisch `CHANGELOG.en.md` bzw.
  `CHANGELOG.<lang>.md`. Format nach "Keep a Changelog" mit Versionsueberschriften; der Store
  ordnet Eintraege per Version zu.

**Was uns wahrscheinlich noch fehlt (Luecken):**
- Mindestens ein `<screenshot>` (HTTPS) fehlt vermutlich.
- Englische `description` sicherstellen (Pflicht), deutsche optional.
- `CHANGELOG.md` im Keep-a-Changelog-Format.
- `<summary>` setzen (kurz, praegnant).
- `category` auf `integration` fixieren.
- `author` mit `mail`/`homepage`, `bugs`-URL, `repository`-URL, `website` sinnvoll fuellen.

Quellen:
- https://docs.nextcloud.com/server/latest/developer_manual/app_development/info.html
- https://github.com/nextcloud/appstore/blob/master/nextcloudappstore/api/v1/release/parser.py

---

## Frage 4: Datenweitergabe-/Privacy-Disclosure und Ethical-AI-Rating

**Kernbefund: Der App Store verlangt KEINE strukturierte Datenweitergabe-Erklaerung in info.xml.
Es gibt KEIN `<data-sharing>`- und KEIN `<ethical-ai-rating>`-Element im Store-Schema.**

- Weder `info.xsd` noch `pre-info.xslt` kennen ein Datenschutz-/Data-Sharing-Feld oder einen
  Ethical-AI-Tag. Alles Nicht-Aufgefuehrte wird ohnehin weggestrippt. Ein solcher Tag in info.xml
  waere also wirkungslos.
- Datenschutz wird im Store nur ueber die allgemeinen Store-Regeln adressiert ("Apps must respect
  user privacy", "clearly communicate their intended purpose and active features") und ueber die
  Freitext-`<description>`. Empfehlung: In der `description` transparent beschreiben, dass der
  MCP-Connector Nutzer-/Kontextdaten an vom Nutzer verbundene externe MCP-/LLM-Clients weiterreicht,
  inkl. Hinweis auf Scopes/Berechtigungen.
- Das "Ethical AI Rating" ist ein NEXTCLOUD-LAUFZEITKONZEPT, kein Store-Metadatum. Es wird von
  Anbieter-Apps gesetzt, die einen Task-Processing-Provider registrieren (Provider liefert seine
  Rating-Einstufung ueber die OCP-/Task-Processing-API zur Laufzeit). Fuer einen reinen
  MCP-Connector, der KEIN Task-Processing-Provider ist, ist das Rating im Store nicht relevant und
  nicht deklarierbar.
- Fazit: Kein Formularfeld, kein XML-Tag. Die "Disclosure" erfolgt praktisch nur als Prosa in der
  Beschreibung. Wenn spaeter ein Task-Processing-Provider dazukommt, koennte ein Ethical-AI-Rating
  zur Laufzeit relevant werden, aber nicht fuer die Store-Einreichung.

Quellen:
- https://github.com/nextcloud/appstore/blob/master/nextcloudappstore/api/v1/release/info.xsd
- https://github.com/nextcloud/appstore/blob/master/nextcloudappstore/api/v1/release/pre-info.xslt
- https://docs.nextcloud.com/server/latest/developer_manual/app_publishing_maintenance/publishing.html
- https://nextcloud.com/blog/nextcloud-ethical-ai-rating/

---

## Frage 5: Multi-Arch-Image und image-tag

**Kernbefund: Multi-Arch (linux/amd64 + linux/arm64) ist der empfohlene Best-Practice-Weg und wird
von Referenz-ExApps so gemacht, ist aber NICHT vom Store erzwungen. `<image-tag>` muss exakt zum
veroeffentlichten Image-Tag passen und folgt bei den Referenzapps der `<version>`.**

Verifiziert direkt an den ghcr.io-Manifests:
- `ghcr.io/nextcloud-releases/context_chat_backend:5.4.0` ist ein OCI-Image-Index mit
  `architecture: amd64` UND `architecture: arm64` (plus Attestation). Also echtes Multi-Arch.
- `ghcr.io/nextcloud/llm2:2.8.0` ist ein OCI-Index mit NUR `amd64` (plus Attestation), also
  Single-Arch, und ist trotzdem regulaer im Store. Das belegt: arm64 ist nicht Pflicht.

Empfehlung fuer uns: Multi-Arch amd64 + arm64 per `docker buildx build --platform
linux/amd64,linux/arm64 --push` nach ghcr.io. Damit laeuft die ExApp auch auf ARM-Hosts/Deploy-Daemons.
Mindestanforderung real: amd64 genuegt fuer die Store-Zulassung.

image-tag-Regel (verifiziert an beiden Apps):
- `<docker-install><image-tag>` muss ein tatsaechlich existierendes Tag im Registry sein, das AppAPI
  ziehen kann. Bei context_chat_backend ist `image-tag = 5.5.0-beta0` = `<version>`; bei llm2
  `image-tag = 2.8.0` = `<version>`. Konvention: image-tag == Release-Version, damit Store-Version und
  gezogenes Image deckungsgleich sind. Es ist technisch nicht zwingend byte-identisch mit `<version>`,
  aber es muss existieren und sollte aus Konsistenzgruenden gleich lauten.
- `<registry>ghcr.io</registry>`, `<image>owner/mcp_connector</image>` (z. B. eigener GH-Owner),
  `<image-tag>X.Y.Z</image-tag>` passend zu `<version>X.Y.Z</version>`.

Quellen (per Registry-API gegengeprueft):
- ghcr.io Manifest `nextcloud-releases/context_chat_backend:5.4.0` (amd64+arm64)
- ghcr.io Manifest `nextcloud/llm2:2.8.0` (nur amd64)
- https://github.com/nextcloud/context_chat_backend/blob/master/appinfo/info.xml
- https://github.com/nextcloud/llm2/blob/main/appinfo/info.xml

---

## Zusammenfassende Einreichungs-Checkliste

Blockierend / vor Einreichung erledigen:
- [ ] CSR-Zertifikat: `mcp_connector.csr` als PR in `nextcloud/app-certificate-requests` (offen, unser Blocker), danach `.crt` ablegen und App registrieren.
- [ ] Docker-Image nach `ghcr.io/<owner>/mcp_connector:<version>` pushen (empfohlen multi-arch amd64+arm64), `image-tag` == `<version>`.
- [ ] Release-tar.gz bauen (Top-Level-Ordner `mcp_connector/` mit `appinfo/info.xml`), mit Key signieren, Download-URL bereitstellen (z. B. GitHub-Release-Asset).

info.xml pruefen:
- [ ] `<external-app>` bleibt `docker-install > routes > environment-variables` (routes-Platzierung ist korrekt, Store strippt sie ohnehin).
- [ ] Pflichtfelder: id, name, summary, description (mind. Englisch), version, licence=agpl, author(+mail), bugs, repository, dependencies/nextcloud min=32 max=34 (35 waere ebenfalls erlaubt).
- [ ] `category` = `integration`.
- [ ] Mind. 1 `<screenshot>` mit HTTPS-URL.
- [ ] `CHANGELOG.md` (Keep-a-Changelog) im Root.
- [ ] Optional deutsche `description lang="de"`.

Nicht noetig / Missverstaendnisse:
- Kein separates ExApp-XSD, kein Data-Sharing-Feld, kein Ethical-AI-Tag in info.xml.
- Lokaler XSD-Fehler bei `routes` ist ein falsch-positiver; der Store validiert erst nach `pre-info.xslt`.
- arm64 ist optional (llm2 ist amd64-only und trotzdem gelistet).
