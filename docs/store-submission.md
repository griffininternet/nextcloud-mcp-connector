<!--
  - SPDX-FileCopyrightText: 2026 street1983nk
  - SPDX-License-Identifier: AGPL-3.0-or-later
-->

# App Store submission runbook

**Scope:** the steps that publish this ExApp to the Nextcloud App Store, and the steps
that publish every release after the first one. Written so that a follow up release is
an afternoon, not a research project. Every claim here carries the command or the URL it
was checked with, and the store side facts are verified against the store source, see
`.planning/phases/05-store-research.md`.

## Where this stands

The one time setup is done. The certificate is in place, the app is registered, and the
current release is live: `mcp_connector` has been listed in the App Store since
2026-08-19, first as 0.1.0 and since the same day as 0.1.1, and it is offered to ExApp
installations. The CSR pull request is history, not a blocker, and a signature is only
accepted against the certificate that pull request produced, so the live listing below is
the proof that both exist.

0.1.1 is the version an administrator should get: 0.1.0 could be installed with one click
but could not start afterwards, because the address it needs had no place to be set. The
proof of the difference is the last row of the table below.

What remains is maintenance: raise the version, write the changelog, tag, sign the
release asset and hand its URL to the store. That is the runbook further down.

**Open, 2026-08-20: 0.1.2 is built, published and signed, and not yet submitted.** Steps
1 to 6 of the runbook are done and every one of them is a row in the table below: the tag
`v0.1.2` is pushed, the workflow is green, the asset answers 200 and its signature
verifies against the certificate. Only step 7 is outstanding, because it needs the store
account, see the note under step 7. The signature is reproduced by re running the two
commands of step 6 against the published asset, it does not have to be carried around.

## What the artifacts are

Two separate things, do not confuse them:

- **The Docker image** is the app. It is built multi arch and pushed to
  `ghcr.io/street1983nk/mcp_connector:<version>`. AppAPI pulls it at install time.
  It is referenced only from `<docker-install>` in `appinfo/info.xml`.
- **The store archive** is a small `tar.gz` with a single top level folder
  `mcp_connector/` containing `appinfo/info.xml` (plus changelog, license and readme).
  This is what gets signed and submitted. It does NOT contain the image.

## One time setup (per app id), done

1. Generate the key and CSR (done, key held locally in
   `~/.nextcloud/certificates/mcp_connector.key`):
   ```
   openssl req -nodes -newkey rsa:4096 \
     -keyout ~/.nextcloud/certificates/mcp_connector.key \
     -out mcp_connector.csr -subj "/CN=mcp_connector"
   ```
2. Submit the CSR as a pull request to `nextcloud/app-certificate-requests` (done, PR
   [#1160](https://github.com/nextcloud/app-certificate-requests/pull/1160)), and keep
   the returned `mcp_connector.crt` next to the key.
3. Register the app once at `https://apps.nextcloud.com/developer/apps/new` with the
   certificate content and a proof of ownership signature over the app id (done):
   ```
   echo -n "mcp_connector" \
     | openssl dgst -sha512 -sign ~/.nextcloud/certificates/mcp_connector.key \
     | openssl base64 -A
   ```

None of these three steps is repeated for a release. The same private key signs every
release asset from here on.

## Proof of the live state

Every line was measured, not assumed. No fact without its check.

| Date | Fact | Checked with |
|------|------|--------------|
| 2026-08-19 | `mcp_connector` is listed and visible to ExApp installations, one of 26 ExApps | `curl -sS https://apps.nextcloud.com/api/v1/appapi_apps.json` contains the id |
| 2026-08-19 | Release 0.1.0 with the platform span `>=32.0.0 <35.0.0` | same answer, field `releases[].platformVersionSpec` |
| 2026-08-19 | The download URL the store stores is our GitHub release asset | same answer, field `releases[].download`: `https://github.com/street1983nk/nextcloud-mcp-connector/releases/download/v0.1.0/mcp_connector-0.1.0.tar.gz` |
| 2026-08-19 | The image is pullable anonymously and a real multi arch index (`linux/amd64` and `linux/arm64`, plus two attestation entries) | anonymous token from `https://ghcr.io/token?scope=repository:street1983nk/mcp_connector:pull&service=ghcr.io`, then `https://ghcr.io/v2/street1983nk/mcp_connector/manifests/0.1.0` returns `application/vnd.oci.image.index.v1+json` |
| 2026-08-19 | Exactly one tag exists | `https://ghcr.io/v2/street1983nk/mcp_connector/tags/list` returns `["0.1.0"]` |
| 2026-08-19 | The screenshot URL answers 200 with 39532 bytes | `curl -I https://raw.githubusercontent.com/street1983nk/nextcloud-mcp-connector/main/docs/screenshots/connections.png` |
| 2026-08-19 20:45Z | Release 0.1.1 is listed, with the same platform span `>=32.0.0 <35.0.0`, and the store now serves 27 ExApps | `curl -sS https://apps.nextcloud.com/api/v1/appapi_apps.json`, releases of `mcp_connector`: `0.1.1` and `0.1.0` |
| 2026-08-19 20:45Z | The download of 0.1.1 answers 200 with 29491 bytes, the size that was signed | `curl -sSIL https://github.com/street1983nk/nextcloud-mcp-connector/releases/download/v0.1.1/mcp_connector-0.1.1.tar.gz` gives 302 then 200 |
| 2026-08-19 20:46Z | The image of 0.1.1 is pullable anonymously and a real multi arch index: `linux/amd64`, `linux/arm64`, plus the two attestation entries | anonymous token from `ghcr.io/token`, then `https://ghcr.io/v2/street1983nk/mcp_connector/manifests/0.1.1`, `application/vnd.oci.image.index.v1+json` |
| 2026-08-19 20:46Z | Both tags exist, none was rewritten | `https://ghcr.io/v2/street1983nk/mcp_connector/tags/list` returns `["0.1.0","0.1.1"]` |
| 2026-08-19 20:53Z | The published 0.1.1 installs over the store path with no environment variable at all and stays up: `0 restarts`, state running, healthy, and it names its setup state in the log. This is the release: 0.1.0 answered the same install with `Restarting (2)` and exit 2 | `occ app_api:app:register mcp_connector harp_proxy_docker --force-scopes --wait-finish`, then `docker inspect nc_app_mcp_connector --format '{{.RestartCount}} {{.State.Status}}'` and `docker logs nc_app_mcp_connector` |
| 2026-08-20 08:33Z | The release workflow of the tag `v0.1.2` is green in every step, run `32349279561` | `gh run watch 32349279561 --exit-status`, exit 0 |
| 2026-08-20 08:34Z | The download of 0.1.2 answers 200 with 31909 bytes, the size that was signed | `curl -sSIL https://github.com/street1983nk/nextcloud-mcp-connector/releases/download/v0.1.2/mcp_connector-0.1.2.tar.gz` gives 302 then 200 |
| 2026-08-20 08:34Z | The asset the release carries is not the locally built one: 31909 bytes against 32168, and a different sha256. This is the reason step 6 signs the download and not `dist/` | `sha256sum` of both files, `912b429d…` against `4ab1fde9…` |
| 2026-08-20 08:35Z | The signature of 0.1.2 verifies against the merged certificate, so the store will accept it | `openssl x509 -in mcp_connector.crt -pubkey -noout`, then `openssl dgst -sha512 -verify` over the downloaded asset: `Verified OK` |
| 2026-08-20 08:36Z | The image of 0.1.2 is pullable anonymously and a real multi arch index: `linux/amd64`, `linux/arm64`, plus the two attestation entries | anonymous token from `ghcr.io/token`, then `https://ghcr.io/v2/street1983nk/mcp_connector/manifests/0.1.2`, `application/vnd.oci.image.index.v1+json` |
| 2026-08-20 08:36Z | All three tags exist, none was rewritten | `https://ghcr.io/v2/street1983nk/mcp_connector/tags/list` returns `["0.1.0","0.1.1","0.1.2"]` |
| 2026-08-20 08:28Z | Both screenshot URLs answer 200, the overview with 82580 bytes and the connections page with 41825 | `curl -sSI` on `docs/screenshots/connections.png` and `docs/screenshots/connections-page.png` |
| 2026-08-20 08:30Z | The manifest of 0.1.2 passes the validation the store runs, and both screenshots survive the pre pass | `pre-info.xslt` applied to `appinfo/info.xml`, then `info.xsd`, both fetched from the appstore repository: `assertValid` passes. Raw against `info.xsd` reports `routes` only, the documented false positive |

### The update keeps the connections

Measured on 2026-08-19 on the HaRP topology of `compose.exapp.yml`, on the published
artifacts and not on a local build.

| Time | Step | Result |
|------|------|--------|
| 20:49Z | `occ app_api:app:register mcp_connector harp_proxy_docker --info-xml https://raw.githubusercontent.com/street1983nk/nextcloud-mcp-connector/v0.1.0/appinfo/info.xml --env NC_MCP_PUBLIC_URL=... --force-scopes --wait-finish` | `0.1.0 [enabled]`, container healthy on `ghcr.io/street1983nk/mcp_connector:0.1.0` |
| 20:50Z | One real OAuth connection walked end to end (registration, sign in, consent, code exchange), then a tool listing with the token it produced | 16 tools for the account; rows in the volume: 1 client, 1 authorization, 1 access token, 1 refresh token |
| 20:51Z | `occ app_api:app:update --all --showonly`, 57 minutes after the last store fetch | empty, the instance still knew only 0.1.0. This is the cache of pitfall 8, not a failed release |
| 20:51Z | Cache discarded, then the same question again | `mcp_connector new version available: 0.1.1` |
| 20:52Z | `occ app_api:app:update mcp_connector --wait-finish`, 20 seconds | `0.1.1 [enabled]`, container healthy on the 0.1.1 image, and every row count unchanged |
| 20:52Z | The access token issued by 0.1.0, presented to 0.1.1 | 16 tools, and a real `files_list` call answered ok |

The last line is the point. A token from before the update can only work afterwards if the
volume, the rows in it and the data key that decrypts them all survived the redeploy, which
is what `deployExApp` with `removeData: false` promises. The same holds across a
`unregister` without `--rm-data` followed by a fresh install: the authorization and the
client were still there, and `occ mcp_connector:purge --force` then ended them with
`{"purged":true,"connections":1,"revoked":1,"revoke_failures":0,"tables_cleared":true,"key_deleted":true}`.

**Discard the cache by overwriting it, never by deleting it.** The cache lives in
`data/appdata_*/appstore/appapi_apps.json`. Removing the file leaves the entry in
Nextcloud's own file cache, and every following AppAPI command dies with
`OCP\Files\GenericFileException` and no explanation. Write an expired document into it
instead, and let Nextcloud read its own directory again:

```
docker exec -u www-data <nc> sh -c 'for d in /var/www/html/data/appdata_*/appstore; do \
  printf "%s" "{\"timestamp\":0,\"data\":[],\"ncversion\":\"0\"}" > "$d/appapi_apps.json"; done'
docker exec -u www-data <nc> php occ files:scan-app-data
```

## Release runbook for a follow up release

The order is not a preference. Steps 4 and 5 create artifacts that steps 6 and 7 depend
on, and step 4 is irreversible in public.

1. **Raise the version in all four places, to the same string.** `version` in
   `pyproject.toml`, `__version__` in `src/mcp_connector/__init__.py`, `<version>` and
   `<image-tag>` in `appinfo/info.xml`. Two gates hold this: the manifest gate in
   `tests/unit/test_exapp_env_setup.py` compares `<version>` with the package version
   and `<image-tag>` with `<version>`, and the release workflow refuses a tag push whose
   tag disagrees with `<version>`. The git tag `v<version>` is the third identical
   string, and it has to be, because AppAPI pulls exactly the tag the manifest names: a
   tag that does not exist means an install that cannot start, and a tag that points
   somewhere else means an install that runs code nobody released.
2. **Write the changelog.** A new version block in `CHANGELOG.md`, in the shape of the
   existing ones, with the user relevant changes only, plus the two link references at
   the bottom of the file. This file travels inside the store archive.
3. **Run every gate locally, all green.**
   ```
   uv run --no-sync pytest -q
   uv run --no-sync ruff check .
   uv run --no-sync ruff format --check .
   uv run --no-sync pyright
   uv run --no-sync vulture src scripts vulture_whitelist.py
   uv run --no-sync python scripts/check_tool_budget.py
   ```
   The manifest gates live in the first command: the route gate, the description gate
   (no backtick, no table, no image, no rule, no HTML, at least two paragraphs per
   language, `summary` under 128 characters, no forbidden vocabulary), the variable gate
   (no empty `<default>`, which the store answers with a 500) and the version equality
   above. Optional but cheap, build the archive without uploading it and look inside:
   ```
   scripts/build_store_release.sh
   tar -tzf dist/mcp_connector-<version>.tar.gz
   ```
4. **Tag and push, with exactly that version.** This is the irreversible step.
   ```
   git tag v<version>
   git push origin v<version>
   ```
5. **Wait for the workflow.** The `release` workflow builds the image for
   `linux/amd64` and `linux/arm64`, pushes it to
   `ghcr.io/street1983nk/mcp_connector:<version>`, builds the store archive and attaches
   it to the GitHub release. Do not continue while it is red.
   ```
   gh run list --workflow release.yml --limit 1
   ```
6. **Download the release asset and sign exactly that artifact.** Not a locally built
   one: `tar.gz` is not byte reproducible, and the store checks the signature against
   the bytes it downloads from the URL.
   ```
   curl -sSLO https://github.com/street1983nk/nextcloud-mcp-connector/releases/download/v<version>/mcp_connector-<version>.tar.gz
   openssl dgst -sha512 -sign ~/.nextcloud/certificates/mcp_connector.key \
     mcp_connector-<version>.tar.gz | openssl base64 -A
   ```
7. **Send the download URL and the signature to the store.** Either the form at
   `https://apps.nextcloud.com/developer/apps/releases/new`, or the API with the token
   from the account page (`https://apps.nextcloud.com/account/token`):
   ```
   curl -sS -i -X POST https://apps.nextcloud.com/api/v1/apps/releases \
     -H "Authorization: Token $NC_STORE_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"download":"https://github.com/street1983nk/nextcloud-mcp-connector/releases/download/v<version>/mcp_connector-<version>.tar.gz","signature":"<base64 signature>"}'
   ```
   The store downloads the archive, checks the signature against the certificate, checks
   the folder structure (exactly one top level folder, lowercase and underscores,
   contains `appinfo/info.xml`) and validates the metadata (after `pre-info.xslt`)
   against `info.xsd`. 201 means accepted.

   **This step needs a person, and that is not going to change.** The token belongs to
   the store account, it is not a repository secret and it is deliberately not stored in
   this working copy. Reading it out of a browser profile is not a way around that: the
   profile of a running browser holds its cookie database under an exclusive lock, and
   from Chrome 127 on those cookies are additionally bound to the installation that
   wrote them, so a copied profile does not open the session anyway. Whoever holds the
   account opens `https://apps.nextcloud.com/account/token`, and either pastes the
   download URL and the signature into the form at
   `https://apps.nextcloud.com/developer/apps/releases/new` or runs the `curl` above with
   the token in the environment. Everything before this step is automatable and is
   automated; this one is the hand off.

   Steps 1 to 6 leave nothing to redo: the signature is a pure function of the published
   asset and the key, so it is recomputed with the two commands of step 6 whenever it is
   needed, and it never has to be written down or passed along.
8. **Run the four proofs, and write each one into the table above with its date.**
   ```
   curl -sS https://apps.nextcloud.com/api/v1/appapi_apps.json           # release line <version>, same platform span
   curl -I  https://github.com/street1983nk/nextcloud-mcp-connector/releases/download/v<version>/mcp_connector-<version>.tar.gz
   TOKEN=$(curl -sS "https://ghcr.io/token?scope=repository:street1983nk/mcp_connector:pull&service=ghcr.io" | grep -o '"token":"[^"]*' | cut -d'"' -f4)
   curl -sS -H "Authorization: Bearer $TOKEN" \
     -H "Accept: application/vnd.oci.image.index.v1+json" \
     https://ghcr.io/v2/street1983nk/mcp_connector/manifests/<version>   # OCI index, amd64 and arm64
   curl -sS -H "Authorization: Bearer $TOKEN" \
     https://ghcr.io/v2/street1983nk/mcp_connector/tags/list             # every released tag
   ```

### Two production dependencies, both permanent

- **Never delete a release asset, never rewrite a tag.** AppAPI does not install from
  the store, it installs from our URL: `ExAppArchiveFetcher::downloadInfoXml` takes the
  download field of the newest release the store lists and fetches that `tar.gz` at
  install time, checks its signature and reads `info.xml` out of it. The store keeps
  the URL, nothing else. A deleted asset is a 404 for every administrator who installs
  after us, and AppAPI reports it as "Failed to get app info for ... from the
  Appstore". The `curl -I` in step 8 is the check that catches it, and it is not
  optional.
- **A correction takes a new patch version.** Uploading the same version twice is not
  something we have tried, and the store may refuse it. Raising the patch version
  costs one commit and is the clean practice anyway. It also keeps the tag, the image
  tag and the store release one to one, which is what the whole first step is about.

### The cache is not a bug

A fresh release does not show up in an instance at once, and that is expected
behaviour, not a failed release. `AppAPIFetcher::INVALIDATE_AFTER_SECONDS` is 3600
seconds for the stable channel (900 for unstable), and after a failed fetch
`RETRY_AFTER_FAILURE_SECONDS` adds another 300 seconds before the next attempt. So an
instance can be up to an hour behind, or an hour and five minutes after a failed
attempt, before `occ app_api:app:update` or the update hint appears. The signal that
tells the two cases apart: if `appapi_apps.json` on apps.nextcloud.com shows the new
version and the instance does not, it is the cache. Wait, or discard the cache on the
test instance.

An update itself keeps the data. `occ app_api:app:update` disables the app, replaces
the routes from the new `info.xml`, updates the app info and then redeploys with
`removeData: false`, so the volume and with it every authorization survives, and the
app secret is carried over on purpose.

## Pre submission checklist

Blocking, do before submitting:

- [x] Certificate merged (`app-certificate-requests` PR #1160) and app registered.
- [x] Image pushed to `ghcr.io/street1983nk/mcp_connector:<version>`, tag equals
      `<version>`, multi arch (amd64 alone would be accepted by the store, we ship both).
      Done for 0.1.2, see the table above.
- [x] Store archive built from the release asset and signed, download URL answers 200.
      Done for 0.1.2, and the signature was verified against the certificate before the
      hand off, see the table above.

info.xml, already in place:

- [x] `<external-app>` is `docker-install > routes > environment-variables`. This is
      correct. The store strips `routes` via `pre-info.xslt` before validating, so a
      local raw XSD check will always complain about `routes`, a false positive.
- [x] Required fields: id, name, summary, description (English), version,
      licence=agpl, author with mail, bugs, repository, dependencies/nextcloud
      min 32 max 34.
- [x] `category` is `integration` (valid).
- [x] Data flow described in the `<description>` as prose. The store has no
      data sharing field and no ethical AI tag, prose is the only channel. Full note
      in `docs/privacy.md`.
- [x] Two `<screenshot>` elements with HTTPS URLs, both reachable (see the proof table
      above). The order is the order the store shows, so the overview leads and the
      connections page follows.
- [x] German and French `<summary>` and `<description>` for the local listings.
- [x] No variable carries an empty `<default>`. An empty XML element parses as `None`,
      and the store field is `CharField(blank=True)` without `null=True`, so the upload
      dies with a 500 and no useful message.

## Not needed, common misunderstandings

- No separate ExApp XSD exists. The store uses one `info.xsd` plus the
  `pre-info.xslt` pre pass.
- No `<data-sharing>` element, no `<ethical-ai-rating>` element in the store schema.
- arm64 is optional for the store. We ship it because ARM selfhosters are a target
  group, `llm2` is amd64 only and is listed all the same.
- The store does not host the archive and does not mirror the image. It stores the URL
  and the metadata it validated once, which is why the two production dependencies
  above are permanent.
