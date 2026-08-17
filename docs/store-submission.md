<!--
  - SPDX-FileCopyrightText: 2026 street1983nk
  - SPDX-License-Identifier: AGPL-3.0-or-later
-->

# App Store submission runbook

**Scope:** the steps that publish this ExApp to the Nextcloud App Store. Written so
that once the certificate is in place, the submission itself is an afternoon, not a
research project. Every claim here is verified against the store source, see
`.planning/phases/05-store-research.md`.

## What the artifacts are

Two separate things, do not confuse them:

- **The Docker image** is the app. It is built multi arch and pushed to
  `ghcr.io/street1983nk/mcp_connector:<version>`. AppAPI pulls it at install time.
  It is referenced only from `<docker-install>` in `appinfo/info.xml`.
- **The store archive** is a small `tar.gz` with a single top level folder
  `mcp_connector/` containing `appinfo/info.xml` (plus changelog and license). This
  is what gets signed and submitted. It does NOT contain the image.

## One time setup (per app id)

1. Generate the key and CSR (already done, key held locally):
   ```
   openssl req -nodes -newkey rsa:4096 \
     -keyout ~/.nextcloud/certificates/mcp_connector.key \
     -out mcp_connector.csr -subj "/CN=mcp_connector"
   ```
2. Submit the CSR as a PR to `nextcloud/app-certificate-requests`.
   **Status: open, this is the current blocker.** PR
   [#1160](https://github.com/nextcloud/app-certificate-requests/pull/1160), DCO
   green, waiting for a maintainer to merge and hand back `mcp_connector.crt`.
3. Register the app once at
   `https://apps.nextcloud.com/developer/apps/new` with the certificate content and
   a proof of ownership signature over the app id:
   ```
   echo -n "mcp_connector" \
     | openssl dgst -sha512 -sign ~/.nextcloud/certificates/mcp_connector.key \
     | openssl base64 -A
   ```

## Per release

1. Set the version. `<version>` in `appinfo/info.xml` and the git tag `v<version>`
   and the pushed image tag must all be the same string. Add the release section to
   `CHANGELOG.md`.
2. Push the tag. The `release.yml` workflow builds and pushes the multi arch image
   to ghcr.io and attaches the store archive to the GitHub release.
   - If the signing key is stored as the `NC_SIGN_KEY_B64` secret, the workflow also
     prints the signature. If not, build and sign locally:
     ```
     scripts/build_store_release.sh
     ```
     It prints the base64 SHA-512 signature.
3. Make the archive reachable over HTTPS (the GitHub release asset URL works).
4. Submit at `https://apps.nextcloud.com/developer/apps/releases/new` with the
   download URL and the base64 signature. The store downloads the archive, checks
   the signature against the certificate, checks the folder structure, and validates
   the metadata (after `pre-info.xslt`) against `info.xsd`.

## Pre submission checklist

Blocking, do before submitting:

- [ ] Certificate merged (`app-certificate-requests` PR #1160) and app registered.
- [ ] Image pushed to `ghcr.io/street1983nk/mcp_connector:<version>`, tag equals
      `<version>`. Multi arch recommended, amd64 alone is accepted by the store.
- [ ] Store archive built and signed, download URL ready.

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

Still missing, needs a human:

- [ ] At least one `<screenshot>` with an HTTPS URL. Take it while doing the browser
      check of the settings signpost and the `/connections` page (AR-04-01), host it
      (a raw GitHub URL works), then add `<screenshot>https://...</screenshot>` to
      info.xml.
- [ ] Optional: a German `<description lang="de">` for a nicer local listing.

## Not needed, common misunderstandings

- No separate ExApp XSD exists. The store uses one `info.xsd` plus the
  `pre-info.xslt` pre pass.
- No `<data-sharing>` element, no `<ethical-ai-rating>` element in the store schema.
- arm64 is optional. `llm2` is amd64 only and is listed.
