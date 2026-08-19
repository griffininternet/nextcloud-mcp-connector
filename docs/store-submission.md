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
first release is live: `mcp_connector` 0.1.0 has been listed in the App Store since
2026-08-19 and is offered to ExApp installations. The CSR pull request is history, not a
blocker, and a signature is only accepted against the certificate that pull request
produced, so the live listing below is the proof that both exist.

What remains is maintenance: raise the version, write the changelog, tag, sign the
release asset and hand its URL to the store. That is the runbook further down.

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
- [ ] Image pushed to `ghcr.io/street1983nk/mcp_connector:<version>`, tag equals
      `<version>`, multi arch (amd64 alone would be accepted by the store, we ship both).
- [ ] Store archive built from the release asset and signed, download URL answers 200.

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
- [x] One `<screenshot>` with an HTTPS URL, reachable (see the proof table above).
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
