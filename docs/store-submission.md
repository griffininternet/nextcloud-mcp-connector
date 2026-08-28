<!--
  - SPDX-FileCopyrightText: 2026 street1983nk
  - SPDX-License-Identifier: AGPL-3.0-or-later
-->

# App Store submission runbook

**Scope:** the steps that publish this ExApp to the Nextcloud App Store, and the steps
that publish every release after the first one. Written so that a follow up release is
an afternoon, not a research project. Every claim here carries the command or the URL it
was checked with, and the store side facts are verified against the store source. The
research those facts came out of is kept in `.planning/phases/05-store-research.md`, an
internal note that may disappear: every row of the proof table below carries its own
command or its own URL, so no claim on this page leans on that note.

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

**Done, 2026-08-20: 0.1.2 is live in the store.** Steps 1 to 7 of the runbook are done and
every one of them is a row in the table below: the tag `v0.1.2` is pushed, the workflow is
green, the asset answers 200, its signature verifies against the certificate, and the
upload answered 201. The upload ran in the page context of the signed in store session
(see the note under step 7), the token never left the page.

**Done, 2026-08-21: 0.1.3 is live in the store.** Same path as 0.1.2, every step a row in
the table below: the store page named 0.1.3 as the current release one minute after the
upload, and `appapi_apps.json` carried the release line twelve minutes after it.

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
| 2026-08-20 08:28Z | Both screenshot URLs answer 200, the overview with 82580 bytes and the connections page with 41825 | `curl -sSI` on `docs/screenshots/connections.png` and `docs/screenshots/connections-page.png` |
| 2026-08-20 08:30Z | The manifest of 0.1.2 passes the validation the store runs, and both screenshots survive the pre pass | `pre-info.xslt` applied to `appinfo/info.xml`, then `info.xsd`, both fetched from the appstore repository: `assertValid` passes. Raw against `info.xsd` reports `routes` only, the documented false positive |
| 2026-08-20 08:33Z | The release workflow of the tag `v0.1.2` is green in every step, run `32349279561` | `gh run watch 32349279561 --exit-status`, exit 0 |
| 2026-08-20 08:34Z | The download of 0.1.2 answers 200 with 31909 bytes, the size that was signed | `curl -sSIL https://github.com/street1983nk/nextcloud-mcp-connector/releases/download/v0.1.2/mcp_connector-0.1.2.tar.gz` gives 302 then 200 |
| 2026-08-20 08:34Z | The asset the release carries is not the locally built one: 31909 bytes against 32168, and a different sha256. This is the reason step 6 signs the download and not `dist/` | `sha256sum` of both files, `912b429d…` against `4ab1fde9…` |
| 2026-08-20 08:35Z | The signature of 0.1.2 verifies against the merged certificate, so the store will accept it | `openssl x509 -in mcp_connector.crt -pubkey -noout`, then `openssl dgst -sha512 -verify` over the downloaded asset: `Verified OK` |
| 2026-08-20 08:36Z | The image of 0.1.2 is pullable anonymously and a real multi arch index: `linux/amd64`, `linux/arm64`, plus the two attestation entries | anonymous token from `ghcr.io/token`, then `https://ghcr.io/v2/street1983nk/mcp_connector/manifests/0.1.2`, `application/vnd.oci.image.index.v1+json` |
| 2026-08-20 08:36Z | All three tags exist, none was rewritten | `https://ghcr.io/v2/street1983nk/mcp_connector/tags/list` returns `["0.1.0","0.1.1","0.1.2"]` |
| 2026-08-20 08:42Z | The store accepted the 0.1.2 release | `POST /api/v1/apps/releases` from the page context of the signed in store session answered HTTP 201 |
| 2026-08-20 08:43Z | The store page serves 0.1.2 as the current release | `https://apps.nextcloud.com/apps/mcp_connector` answers 200 and names `0.1.2`; `api/v1/appapi_apps.json` carries the `0.1.2` release line with the platform span of the manifest |
| 2026-08-21 03:57Z | The release workflow of the tag `v0.1.3` is green in every step, run `32445358277` | `gh run watch 32445358277 --exit-status`, exit 0 |
| 2026-08-21 04:02Z | The download of 0.1.3 answers 200 with 35310 bytes, the size that was signed | `curl -sSIL https://github.com/street1983nk/nextcloud-mcp-connector/releases/download/v0.1.3/mcp_connector-0.1.3.tar.gz` gives 302 then 200 |
| 2026-08-21 04:02Z | The signature of 0.1.3 verifies against the merged certificate, so the store will accept it | `openssl x509 -in mcp_connector.crt -pubkey -noout`, then `openssl dgst -sha512 -verify` over the downloaded asset: `Verified OK` |
| 2026-08-21 04:03Z | The store accepted the 0.1.3 release | `POST /api/v1/apps/releases` from the page context of the signed in store session answered HTTP 201 |
| 2026-08-21 04:04Z | The image of 0.1.3 is pullable anonymously and a real multi arch index: `linux/amd64`, `linux/arm64`, plus the two attestation entries | anonymous token from `ghcr.io/token`, then `https://ghcr.io/v2/street1983nk/mcp_connector/manifests/0.1.3`, `application/vnd.oci.image.index.v1+json` |
| 2026-08-21 04:04Z | All four tags exist, none was rewritten | `https://ghcr.io/v2/street1983nk/mcp_connector/tags/list` returns `["0.1.0","0.1.1","0.1.2","0.1.3"]` |
| 2026-08-21 04:04Z | The store page serves 0.1.3 as the current release | `https://apps.nextcloud.com/apps/mcp_connector` answers 200 and names `0.1.3`. `api/v1/appapi_apps.json` still answered the 0.1.2 list at that minute: that endpoint is cached on the store side, the same cache the section below describes, so the check was repeated |
| 2026-08-21 04:16Z | Release 0.1.3 is listed with the platform span `>=32.0.0 <35.0.0`, next to all three earlier releases | `curl -sS https://apps.nextcloud.com/api/v1/appapi_apps.json`, releases of `mcp_connector`: `0.1.3`, `0.1.2`, `0.1.1` and `0.1.0`. Twelve minutes behind the upload, so the cache of that endpoint is measured in minutes, not the hour an instance waits |
| 2026-08-21 15:41Z | The release workflow of the tag `v0.1.4` is green, run `32498760814` | `gh run view 32498760814`: status completed, conclusion success, job publish success |
| 2026-08-21 15:42Z | The download of 0.1.4 answers 200 with 37325 bytes, the size that was signed | `curl -sSIL https://github.com/street1983nk/nextcloud-mcp-connector/releases/download/v0.1.4/mcp_connector-0.1.4.tar.gz` gives 302 then 200 |
| 2026-08-21 15:42Z | The signature of 0.1.4 verifies against the merged certificate, so the store will accept it | `openssl x509 -in mcp_connector.crt -pubkey -noout`, then `openssl dgst -sha512 -verify` over the downloaded asset: `Verified OK` |
| 2026-08-21 15:44Z | The store accepted the 0.1.4 release | `POST /api/v1/apps/releases` from the page context of the signed in store session answered HTTP 201 |
| 2026-08-21 15:46Z | The image of 0.1.4 is pullable anonymously and a real multi arch index: `linux/amd64`, `linux/arm64`, plus the two attestation entries | anonymous token from `ghcr.io/token`, then `https://ghcr.io/v2/street1983nk/mcp_connector/manifests/0.1.4`, `application/vnd.oci.image.index.v1+json` |
| 2026-08-21 15:46Z | All five tags exist, none was rewritten | `https://ghcr.io/v2/street1983nk/mcp_connector/tags/list` returns `["0.1.0","0.1.1","0.1.2","0.1.3","0.1.4"]` |
| 2026-08-21 15:46Z | Release 0.1.4 is listed with the platform span `>=32.0.0 <35.0.0`, next to all four earlier releases | `curl -sS https://apps.nextcloud.com/api/v1/appapi_apps.json`, releases of `mcp_connector`: `0.1.4`, `0.1.3`, `0.1.2`, `0.1.1` and `0.1.0`. Two minutes behind the upload this time |
| 2026-08-22 10:59Z | The release workflow of the tag `v0.1.5` is green, run `32569019469` | `gh run view 32569019469`: status completed, conclusion success |
| 2026-08-22 11:00Z | The download of 0.1.5 answers 200 with 38194 bytes, the size that was signed | `curl -sSIL .../v0.1.5/mcp_connector-0.1.5.tar.gz` gives 302 then 200 |
| 2026-08-22 11:00Z | The signature of 0.1.5 verifies against the merged certificate | `openssl dgst -sha512 -verify` over the downloaded asset: `Verified OK` |
| 2026-08-22 11:00Z | The store accepted the 0.1.5 release | `POST /api/v1/apps/releases` from the page context of the signed in store session answered HTTP 201 |
| 2026-08-22 11:00Z | The image of 0.1.5 is a real multi arch index: `linux/amd64`, `linux/arm64`, plus the two attestation entries | anonymous token from `ghcr.io/token`, then the manifest of `0.1.5` |
| 2026-08-22 11:00Z | All six tags exist, none was rewritten | tags list returns `["0.1.0","0.1.1","0.1.2","0.1.3","0.1.4","0.1.5"]` |
| 2026-08-22 11:00Z | The store page serves the new description, the homepage and documentation links and both donation buttons, and names 0.1.5 | `https://apps.nextcloud.com/apps/mcp_connector` read in the browser: the section "What an assistant can do" is present, the links `Homepage`, `User documentation`, `Admin documentation`, `Donate with PayPal` and `Donate with Stripe` are rendered. Metadata reaches the page at upload time, not on a release schedule, which is why a description change needs a release of its own |
| 2026-08-24 22:36Z | All six gates of step 3 are green locally for 0.1.8: 2766 tests passed with 163 deselected, no lint finding, 197 files already formatted, no type error, no dead code, and the tool surface measures 15657 bytes across 21 tools against a budget of 18000 | `uv run --no-sync` in front of each of `pytest -q`, `ruff check .`, `ruff format --check .`, `pyright`, `vulture src scripts vulture_whitelist.py` and `python scripts/check_tool_budget.py`, the last one exit 0 |
| 2026-08-24 22:39Z | The store archive of 0.1.8 has exactly one top level folder, `mcp_connector`, lowercase with an underscore, and it carries `appinfo/info.xml`, `CHANGELOG.md`, `LICENSE` and `README.md`. This is a structure check and nothing else: the locally built archive is not the artifact that gets signed, and the 31909 against 32168 bytes of the 2026-08-20 row above are the measurement that says so | `scripts/build_store_release.sh`, then `tar -tzf dist/mcp_connector-0.1.8.tar.gz` |
| 2026-08-25 02:54Z | The release workflow of the tag `v0.1.8` is green in every step, run `32803041518`: the multi arch image was built and pushed, the store archive was built and attached to the GitHub release. The 42 commits of this phase were pushed to `main` immediately before the tag, so the documentation and screenshot URLs the manifest points at serve the state this release belongs to | `git push origin main`, then `git tag v0.1.8` and `git push origin v0.1.8`, then `gh run watch 32803041518 --exit-status`, exit 0, job `publish` success in 1m29s |
| 2026-08-25 02:55Z | The download of 0.1.8 answers 200 with 45546 bytes, the size that was signed, and the signature over exactly those bytes verifies against the certificate. The published asset is again not the locally built one: 45546 bytes against 45710, `2769c587…` against `15fc8719…`, which is the same measurement as the 2026-08-20 row and the reason step 6 signs the download | `curl -sSIL https://github.com/street1983nk/nextcloud-mcp-connector/releases/download/v0.1.8/mcp_connector-0.1.8.tar.gz` gives 302 then 200; `openssl x509 -in mcp_connector.crt -pubkey -noout`, then `openssl dgst -sha512 -verify` over the downloaded asset: `Verified OK`; `sha256sum` of both files |
| 2026-08-25 02:58Z | The store accepted the 0.1.8 release | `POST /api/v1/apps/releases` from the page context of the signed in store session answered HTTP 201 with an empty body, with the download URL and the signature of the row above as the payload and `nightly` false |
| 2026-08-25 02:58Z | The asset of 0.1.8 exists and was not deleted, so an administrator installing after us gets it from our URL. This row is not optional: AppAPI installs from this URL and not from the store, and a deleted asset is a 404 for every later installation | `curl -I https://github.com/street1983nk/nextcloud-mcp-connector/releases/download/v0.1.8/mcp_connector-0.1.8.tar.gz` gives 302 to `release-assets.githubusercontent.com`, and following it gives 200 with 45546 bytes |
| 2026-08-25 02:58Z | The image of 0.1.8 is pullable anonymously and a real multi arch index: `linux/amd64`, `linux/arm64`, plus the two attestation entries | anonymous token from `ghcr.io/token`, then `https://ghcr.io/v2/street1983nk/mcp_connector/manifests/0.1.8` answers with the content type `application/vnd.oci.image.index.v1+json` and both platforms in its manifest list |
| 2026-08-25 02:58Z | All nine tags exist, none was rewritten and none was removed | `https://ghcr.io/v2/street1983nk/mcp_connector/tags/list` returns `["0.1.0","0.1.1","0.1.2","0.1.3","0.1.4","0.1.5","0.1.6","0.1.7","0.1.8"]` |
| 2026-08-25 02:59Z | The store page serves 0.1.8 as the current release and carries the corrected donation button, the paypal.me address `paypalme/KhaledCherifDev`, which is the reason this release exists, next to the Stripe one. The description text is not part of the initial HTML of that page, so this row says nothing about it: that is a property of the request, not of the release | `curl -sS https://apps.nextcloud.com/apps/mcp_connector` answers 200, names `0.1.8` and contains both donation addresses, measured once with the default user agent and once with a browser one |
| 2026-08-25 03:01Z | Release 0.1.8 is listed with the platform span `>=32.0.0 <35.0.0`, which is the span the manifest declares with min-version 32 and max-version 34, next to all eight earlier releases, and the download the store keeps is our GitHub asset | `curl -sS https://apps.nextcloud.com/api/v1/appapi_apps.json`, releases of `mcp_connector`: `0.1.8` down to `0.1.0`, every one with the same span, and the store serves 27 ExApps. That endpoint still answered the 0.1.7 list at 02:58Z and carried 0.1.8 about two minutes later, which is the cache the section below describes and not a failed upload |
| 2026-08-25 18:13Z | All six gates of step 3 are green locally for 0.1.9: 2812 tests passed with 163 deselected, no lint finding, 199 files already formatted, no type error and no warning, no dead code, and the tool surface measures 15711 bytes across 21 tools against a budget of 18000. That is the same number the phase 12 measurement recorded (plan 12-01, after the `mail_browse` docstring change raised it from 15657; the v1.2 baseline was 15612), because this phase touched no tool and no docstring, and the budget was not raised to make it fit. The store archive of 0.1.9 has exactly one top level folder, `mcp_connector`, and the `README.md` it carries names `Version 0.1.9.`, which is the line the 0.1.8 tarball got wrong and published as 0.1.7 forever, because a release asset is immutable. This run is a structure check and nothing else: the locally built archive is not the artifact that gets signed, and nothing from it is submitted | `uv run --no-sync` in front of each of `pytest -q`, `ruff check .`, `ruff format --check .`, `pyright`, `vulture src scripts vulture_whitelist.py` and `python scripts/check_tool_budget.py`, every one exit 0; then `bash scripts/build_store_release.sh`, `tar -tzf dist/mcp_connector-0.1.9.tar.gz` through `cut -d/ -f1` and `sort -u` gives the single line `mcp_connector`, and `tar -xzOf dist/mcp_connector-0.1.9.tar.gz mcp_connector/README.md` counted against `^Version 0\.1\.9\.` gives 1 |
| 2026-08-25 18:14Z | Step 1 is done for 0.1.9: the six version places carry the same string. `version` in `pyproject.toml`, `__version__` in `src/mcp_connector/__init__.py`, `<version>` and `<image-tag>` in `appinfo/info.xml`, the three `Version 0.1.9.` status lines of `README.md`, `README.de.md` and `README.fr.md` as the fifth, and the self entry of `uv.lock` as the sixth. The three status lines are the ones no gate holds and the signed tarball publishes, so they were raised by hand in this step; `uv.lock` was raised as a text edit, without a lock run, the way commit 8392680 did it for 0.1.8 | `grep -c '^version = "0.1.9"' pyproject.toml` gives 1, `grep -c '^__version__ = "0.1.9"' src/mcp_connector/__init__.py` gives 1, `grep -o '<version>[^<]*' appinfo/info.xml` and the same over `<image-tag>` give `0.1.9` once each, `grep -n '^Version 0\.1\.9\.' README.md README.de.md README.fr.md` gives three hits, one per file, `grep -n 'version = "0.1.9"' uv.lock` names line 472, and the manifest gate `uv run --no-sync pytest tests/unit/test_exapp_env_setup.py -q` exits 0 |
| 2026-08-25 18:14Z | Step 2 is done for 0.1.9: the block `## [0.1.9] - 2026-08-25` names `message_truncated` on the entry level of `talk_browse` as the one format change under `### Changed`, the corrected search provider name `talk-conversations` as a documentation fix under `### Fixed`, and the planned Enterprise add-on as the new store text under `### Added`. The two link references at the bottom of the file are in place, so the block is reachable from the version list | `grep -n '^## \[0\.1\.9\]' CHANGELOG.md` names line 12, `grep -c 'message_truncated' CHANGELOG.md` and `grep -c 'talk-conversations' CHANGELOG.md` give 1 each, `grep -n '^### Added' CHANGELOG.md` names line 19, above `### Changed` on 28 and `### Fixed` on 41, and `grep -n 'compare/v0.1.9' CHANGELOG.md` plus `grep -n 'compare/v0.1.8...v0.1.9' CHANGELOG.md` name lines 479 and 480 |
| 2026-08-25 18:21Z | The first half of step 4 is done for 0.1.9 and it stands alone on purpose: the eighteen commits of this phase are on the public `main`, and no tag exists. `origin/main` and `HEAD` are the same commit `22471c1`, the working tree is clean, and `v0.1.9` is absent locally and on the remote. The push comes before the tag because the store description links to `blob/main/...` and the screenshots load from `raw.githubusercontent.com/.../main/...`, so a tag on an unpushed state would publish a release whose linked pages show an older one, which is what the 0.1.8 release found with 42 unpushed commits. The tag itself waits for an explicit owner release, and the row that carries the tag and the workflow run of step 5 is written after that run is green, never before | `git push origin main` moved `dfee4f8..22471c1`, then `git log origin/main..HEAD --oneline` counted with `wc -l` gives 0, `git status --short` prints nothing, `git tag --list v0.1.9` and `git ls-remote --tags origin v0.1.9` are both empty, and `gh run list --workflow release.yml --limit 5` names no run for `v0.1.9`, its newest being `32803041518` for `v0.1.8` |
| 2026-08-25 18:30Z | The second half of step 4 and all of step 5 are done for 0.1.9. The tag `v0.1.9` exists locally and on the remote and points at `685295d`, one commit after the `22471c1` that the row above certifies at 18:21Z: `685295d` is that proof line itself, and it was published by the `git push origin main` of this step before the tag was created, so nothing was tagged that the public branch does not serve. The release workflow of that tag is green in every step, run `32883904698`, job `publish` success in 1m40s: the multi arch image was built and pushed to `ghcr.io/street1983nk/mcp_connector:0.1.9`, and the store archive was built and attached to the GitHub release as `mcp_connector-0.1.9.tar.gz` with 47264 bytes. The tag came into being only after an explicit owner release at 18:27Z, and every commit of this phase was on the public `main` before it existed. No tag was rewritten, no asset was deleted, and the 47264 bytes are the published size, not the 47546 of the local structure check | `git push origin main`, then `git tag v0.1.9` and `git push origin v0.1.9`, then `gh run watch 32883904698 --exit-status`, exit 0, and `gh run view 32883904698 --json conclusion` gives `success`. `git ls-remote --tags origin v0.1.9` names `685295d7d1e0ac227d6611d33fb3eb799351c800`, and `gh release view v0.1.9 --json assets` names `mcp_connector-0.1.9.tar.gz` |
| 2026-08-25 18:39Z | Step 6 is done for 0.1.9: the download answers 200 with 47264 bytes after a 302, and the signature over exactly those bytes verifies against the merged certificate: `Verified OK`. The published asset is again not the locally built one: 47264 bytes against the 47546 of the step 3 structure check, sha256 `a2b9bc33…` against `4f2a05fe…`, the same measurement as the 0.1.2 and 0.1.8 rows and the reason this step signs the download and never `dist/` | `curl -sSIL https://github.com/street1983nk/nextcloud-mcp-connector/releases/download/v0.1.9/mcp_connector-0.1.9.tar.gz` gives 302 then 200 with `Content-Length: 47264`; `curl -sSLO` on the same URL; `openssl dgst -sha512 -sign ~/.nextcloud/certificates/mcp_connector.key` over the downloaded file, then `openssl x509 -in mcp_connector.crt -pubkey -noout` and `openssl dgst -sha512 -verify` with that signature over the same file: `Verified OK`; `sha256sum` of the download and of `dist/mcp_connector-0.1.9.tar.gz` |
| 2026-08-25 18:40Z | The store accepted the 0.1.9 release | `POST /api/v1/apps/releases` from the page context of the signed in store session answered HTTP 201 with an empty body, with the download URL of the row above and the freshly computed signature as the payload and `nightly` false |
| 2026-08-25 18:41Z | The asset of 0.1.9 exists and was not deleted, so an administrator installing after us gets it from our URL. This row is not optional: AppAPI installs from this URL and not from the store, and a deleted asset is a 404 for every later installation | `curl -I https://github.com/street1983nk/nextcloud-mcp-connector/releases/download/v0.1.9/mcp_connector-0.1.9.tar.gz` gives 302 to `release-assets.githubusercontent.com`, and following it gives 200 with 47264 bytes |
| 2026-08-25 18:41Z | The image of 0.1.9 is pullable anonymously and a real multi arch index: `linux/amd64`, `linux/arm64`, plus the two attestation entries | anonymous token from `ghcr.io/token`, then `https://ghcr.io/v2/street1983nk/mcp_connector/manifests/0.1.9` answers with the content type `application/vnd.oci.image.index.v1+json` and both platforms in its manifest list |
| 2026-08-25 18:41Z | All ten tags exist, none was rewritten and none was removed | `https://ghcr.io/v2/street1983nk/mcp_connector/tags/list` returns `["0.1.0","0.1.1","0.1.2","0.1.3","0.1.4","0.1.5","0.1.6","0.1.7","0.1.8","0.1.9"]` |
| 2026-08-25 18:46Z | Release 0.1.9 is listed with the platform span `>=32.0.0 <35.0.0`, which is the span the manifest declares, next to all nine earlier releases, and the store serves 27 ExApps. That endpoint still answered the 0.1.8 list at 18:41Z and carried 0.1.9 six minutes after the upload, which is the cache the section below describes and not a failed upload; the app detail page already named 0.1.9 at 18:43Z | `curl -sS https://apps.nextcloud.com/api/v1/appapi_apps.json`, releases of `mcp_connector`: `0.1.9` down to `0.1.0` |
| 2026-08-27 23:20Z | Step 1 is done for 0.1.10: the six version places carry the same string. `version` in `pyproject.toml`, `__version__` in `src/mcp_connector/__init__.py`, `<version>` and `<image-tag>` in `appinfo/info.xml`, the three `Version 0.1.10.` status lines of `README.md`, `README.de.md` and `README.fr.md` as the fifth, and the self entry of `uv.lock` as the sixth. The three status lines are the ones no gate holds and the signed tarball publishes, so they were raised by hand; `uv.lock` was raised as a text edit, without a lock run, the way 0.1.8 and 0.1.9 did it. Four of the seven files are CRLF (`README.md`, `README.de.md`, `README.fr.md`, `appinfo/info.xml`) and were patched byte exact, so the change is one line per place and not a line ending rewrite of the whole file | `grep -c '^version = "0.1.10"' pyproject.toml` gives 1, `grep -c '^__version__ = "0.1.10"' src/mcp_connector/__init__.py` gives 1, `grep -o '<version>[^<]*' appinfo/info.xml` and the same over `<image-tag>` give `0.1.10` once each, `grep -n '^Version 0\.1\.10\.' README.md README.de.md README.fr.md` gives three hits, one per file, `grep -n 'version = "0.1.10"' uv.lock` names line 472, `git diff --numstat` names one added and one removed line per file and two against two for `appinfo/info.xml` with its two places, the CRLF counts before and after the patch are 536, 551, 570 and 540 either way, and the manifest gate `uv run --no-sync pytest tests/unit/test_exapp_env_setup.py -q` exits 0 |
| 2026-08-27 23:22Z | Step 2 is done for 0.1.10: the block `## [0.1.10] - 2026-08-28` names under `### Changed` the shortened Enterprise section of the store description and of all three READMEs, together with the contact change from `k.cherif@outlook.de` to `admin@infranode.dev`, and under `### Fixed` the wording corrections in `README.fr.md` and `README.de.md`. Those are the only two rubrics of the block, because 0.1.10 changes no line of code: text is the kind of change only a release carries to its readers, since the store reads the manifest at upload time. The link definition `[0.1.10]` stands at the bottom of the file and is paired with its section, and no `[Unreleased]` definition exists | `grep -n '^## \[0\.1\.10\]' CHANGELOG.md` names line 12, above the 0.1.9 block on line 39, `grep -n '^### ' CHANGELOG.md` names `### Changed` and `### Fixed` as the only two rubrics of that block, `grep -c 'admin@infranode.dev' CHANGELOG.md` gives 1 and the hit is above line 39, `grep -c 'compare/v0.1.9...v0.1.10' CHANGELOG.md` gives 1, the sorted set of version headings equals the sorted set of link definitions at 11 against 11, and `grep -c 'Unreleased' CHANGELOG.md` gives 0 |
| 2026-08-27 23:34Z | All six gates of step 3 are green locally for 0.1.10: 2813 tests passed with 163 deselected, no lint finding, 198 files already formatted, no type error and no warning, no dead code, and the tool surface measures 15712 bytes across 21 tools against a budget of 18000. That is one byte more than the 15711 of the 0.1.9 run, and the byte has a name rather than a rounding excuse: the `tools/list` envelope carries the `serverInfo` metadata, whose version string grew from `0.1.9` to `0.1.10` by exactly one character. The 21 tool schemas are byte identical to the phase 12 measurement, `mail_browse` at 1376 and `talk_browse` at 912, and no limit was raised to make anything fit: `BUDGET_BYTES` stays 18000, `MAX_TOOL_BYTES` stays 1400. The store archive of 0.1.10 has exactly one top level folder, `mcp_connector`, the `README.md` it carries names `Version 0.1.10.`, which is the line the 0.1.8 tarball got wrong and published as 0.1.7 forever because a release asset is immutable, and the `CHANGELOG.md` it carries holds the block `[0.1.10]` and with it, for the first time inside a published asset, the correction written into the 0.1.9 block after that tag existed. This run is a structure check and nothing else: the locally built archive of 47299 bytes is not the artifact that gets signed, and nothing from it, least of all the signature the script prints for diagnosis, is submitted | `uv run --no-sync` in front of each of `pytest -q`, `ruff check .`, `ruff format --check .`, `pyright`, `vulture src scripts vulture_whitelist.py` and `python scripts/check_tool_budget.py`, every one exit 0; the test count was read from a run without the extra `-q`, because `addopts` already carries one and two of them suppress the summary line; `git diff -- scripts/check_tool_budget.py tests/contract/test_tool_surface.py` is empty, and the same measurement with the version patched back to `0.1.9` gives 15711 bytes again, which is what names the byte; then `bash scripts/build_store_release.sh`, `tar -tzf dist/mcp_connector-0.1.10.tar.gz` through `cut -d/ -f1` and `sort -u` gives the single line `mcp_connector`, `tar -xzOf dist/mcp_connector-0.1.10.tar.gz mcp_connector/README.md` counted against `^Version 0\.1\.10\.` gives 1, the same over `mcp_connector/CHANGELOG.md` counted against `^## \[0\.1\.10\]` gives 1 and against `only at upload time` gives 2, and `git status --short dist` and `git tag --list v0.1.10` are both empty |
| 2026-08-27 23:42Z | The first half of step 4 is done for 0.1.10 and it stands alone on purpose: the eight commits of this phase are on the public `main`, and no tag exists. `origin/main` and `HEAD` are the same commit `d3cacfc`, the working tree is clean, and `v0.1.10` is absent locally and on the remote. The push comes before the tag because the store description links to `blob/main/...` and the screenshots load from `raw.githubusercontent.com/.../main/...`, so a tag on an unpushed state would publish a release whose linked pages show an older one, which is what the 0.1.8 release found with 42 unpushed commits. The date line of the 0.1.10 block was checked before the push and left untouched at `2026-08-28`: that is the calendar day of this check in Europe/Berlin, and in UTC the same moment was still the 2026-08-27 with eighteen minutes to go, so the tag, which waits for an explicit owner release, cannot come into being on a day earlier than the one the block names. Should that release arrive on a later calendar day, this one line is raised to the day of the tag before the tag exists, because a release notes date is immutable inside the signed asset. The row that carries the tag and the workflow run of step 5 is written after that run is green, never before | `git push origin main` moved `907582c..d3cacfc`, then `git log origin/main..HEAD --oneline` counted with `wc -l` gives 0, `git status --short` prints nothing, `git tag --list v0.1.10` and `git ls-remote --tags origin v0.1.10` are both empty, `gh run list --workflow release.yml --limit 5` names no run for `v0.1.10`, its newest being the `workflow_dispatch` dry run `32923698977` on `main`, and `grep -n '^## \[0\.1\.10\]' CHANGELOG.md` names line 12 with the date `2026-08-28` against `date` giving `2026-08-28` locally and `date -u` giving `2026-08-27 23:42:33Z` |
| 2026-08-28 04:53Z | The second half of step 4 and all of step 5 are done for 0.1.10. The tag `v0.1.10` exists locally and on the remote and points at `156280f`, one commit after the `d3cacfc` that the row above certifies at 23:42Z: `156280f` is that proof row itself, and it was published by a `git push origin main` before the tag was created, so nothing was tagged that the public branch does not serve. The release workflow of that tag is green in every step, run `33142956284`, job `publish` success in 1m44s from 04:50:10Z to 04:51:54Z: the multi arch image was built for `linux/amd64` and `linux/arm64` and pushed to `ghcr.io/street1983nk/mcp_connector:0.1.10`, and the store archive was built and attached to the GitHub release as `mcp_connector-0.1.10.tar.gz` with 46973 bytes. The tag came into being only after an explicit owner release at 04:49Z, and every commit of this phase was on the public `main` before it existed. The 46973 bytes are the published size, not the 47299 of the local structure check, the same measurement the 0.1.2, 0.1.8 and 0.1.9 rows recorded and the reason step 6 signs the download and never `dist/`. No tag was rewritten and no asset was deleted. One caution for whoever reads the release later: the `createdAt` it carries, `2026-08-27T23:43:54Z`, is the commit date of the tagged commit and not the moment of publication, which was 04:51:55Z | `git push origin main` moved `907582c..d3cacfc` and then `d3cacfc..156280f`, then `git tag v0.1.10` and `git push origin v0.1.10`, then `gh run watch 33142956284 --exit-status` exit 0, and `gh run view 33142956284 --json conclusion` gives `success`. `git ls-remote --tags origin v0.1.10` names `156280fea850c7df6360b10bacbe6a256f0300f7`, `git tag --list` counted with `wc -l` gives 15 against the 14 before, and `gh release view v0.1.10 --json assets` names `mcp_connector-0.1.10.tar.gz` at 46973 bytes with `isDraft` false |
| 2026-08-28 05:00Z | Step 6 is done for 0.1.10: the download answers 200 with 46973 bytes after a 302, and the signature over exactly those bytes verifies against the merged certificate: `Verified OK`. The published asset is again not the locally built one: 46973 bytes against the 47299 of the step 3 structure check, sha256 `4236d2e8…` against `4682e06d…`, the same measurement as the 0.1.2, 0.1.8 and 0.1.9 rows and the reason this step signs the download and never `dist/`. The published bytes carry the payload this release exists for: the `info.xml` inside the asset names `admin@infranode.dev` three times, and the `CHANGELOG.md` inside the asset holds the block `[0.1.10]`, so the shortened Enterprise text and the corrected changelog travel in the artifact that gets signed and not only in the local structure check | `curl -sSIL https://github.com/street1983nk/nextcloud-mcp-connector/releases/download/v0.1.10/mcp_connector-0.1.10.tar.gz` gives 302 then 200 with `Content-Length: 46973`; `curl -sSLO` on the same URL; `openssl dgst -sha512 -sign ~/.nextcloud/certificates/mcp_connector.key` over the downloaded file, then `openssl x509 -in mcp_connector.crt -pubkey -noout` and `openssl dgst -sha512 -verify` with that signature over the same file: `Verified OK`; `sha256sum` of the download and of `dist/mcp_connector-0.1.10.tar.gz`; `tar -xzOf` on the downloaded asset over `mcp_connector/appinfo/info.xml` counted against `admin@infranode.dev` gives 3, and over `mcp_connector/CHANGELOG.md` counted against the heading `[0.1.10]` at line start gives 1 |
| 2026-08-28 05:02Z | The store accepted the 0.1.10 release | `POST /api/v1/apps/releases` from the page context of the signed in store session answered HTTP 201 with an empty body, with the download URL of the row above and the freshly computed signature as the payload and `nightly` false |
| 2026-08-28 05:18Z | Step 8 is done for 0.1.10, four proofs and one that matters more than the four. The catalogue endpoint lists the release next to all ten earlier ones, the published asset downloads at its signed size, the image index carries both architectures, and the tag list holds eleven `v0.1.*` tags with `v0.1.10` among them. The proof this release exists for is the fifth: the store now serves the shortened Enterprise section with `admin@infranode.dev` in its own copy of the description, and the address the section carried before, `k.cherif@outlook.de`, is gone from it. A caution for whoever repeats this check: `0.1.10` sorts before `0.1.9` in a string sort, so a reversed sort of the release list shows `0.1.9` at the top and reads like a failed upload. Ask whether the string `0.1.10` is in the list instead of trusting the order | `curl -sS https://apps.nextcloud.com/api/v1/appapi_apps.json`, releases of `mcp_connector` count 11 and contain `0.1.10`, the store serving 27 ExApps; `curl -sSIL` on the release asset gives 302 then 200 with `Content-Length: 46973`; `docker manifest inspect ghcr.io/street1983nk/mcp_connector:0.1.10` names `linux/amd64` and `linux/arm64`; `curl` on `https://ghcr.io/v2/street1983nk/mcp_connector/tags/list` with an anonymous pull token lists eleven registry tags including `0.1.10`, which is the fourth proof the runbook asks for; the local `git tag --list 'v0.1.*'` gives the same eleven and is the weaker restatement, corrected here on 2026-08-28 after the review named it; and the `translations` of the same catalogue entry count `admin@infranode.dev` once and `k.cherif@outlook.de` zero times in the English and the German description. The app detail page renders its description client side, so it answers 200 and names `0.1.10` but carries no description text for a `curl` to read: the catalogue entry is the readable proof |
| 2026-08-28 05:40Z | Not a runbook step, a note that belongs in this table, and true for the state at 05:40Z only: the manifest in the repository has moved past the signed asset of 0.1.10. Two edits had landed after the tag `v0.1.10` existed at that minute, both on the owner's instruction and both only in the three store descriptions (a third edit and a second file followed at 05:58Z, see the row below): `b3267cd` shortened the trifecta paragraph to three sentences, and the review fix of the same day widened its last sentence from a shared folder to anywhere the account shares, because a Deck card lands in a board and a row lands in a table, never in a folder. Neither edit is in the asset the store serves for 0.1.10 and neither may be added to it: a release asset is immutable, and the store reads the manifest only at upload time. Both are carried by the next release and need their own changelog entry there. The store still serves the long paragraph until then, which is correct and not a failed upload | `git log --oneline v0.1.10..HEAD -- appinfo/info.xml` names the two commits, `git diff v0.1.10..HEAD -- appinfo/info.xml` touches only the three `<description>` blocks and no `<version>`, `<image-tag>` or `<author>` line, and the `translations` of `api/v1/appapi_apps.json` still carry the long wording, as they must until the next upload |
| 2026-08-28 06:05Z | The post-tag drift of 0.1.10 in full, superseding the count in the row above: three commits touch `appinfo/info.xml` since the tag and one touches `CHANGELOG.md`. `b3267cd` shortened the trifecta paragraph, `901b294` widened its last sentence from a shared folder to anywhere the account shares and corrected a claim in the 0.1.10 changelog block that the short enterprise wording states the non-existence as plainly as the long one did, which it does not, and `deafbf4` moved the `<author mail>` from `k.cherif@outlook.de` to `admin@infranode.dev` on an explicit owner decision, so the private address leaves the public manifest. The `CHANGELOG.md` edit means the repository changelog and the changelog inside the signed 0.1.10 asset now differ by that one claim, the same drift class the 0.1.9 release recorded and accepted: an asset is immutable, and the corrected text travels with the next release. Nothing in the published asset changed, and nothing may: the asset still carries the long paragraph and the old author address, and that is the state the store serves until 0.1.11 | `git log --oneline v0.1.10..HEAD -- appinfo/info.xml` names `b3267cd`, `901b294` and `deafbf4`, `git log --oneline v0.1.10..HEAD -- CHANGELOG.md` names `901b294`, `git diff v0.1.10..HEAD -- appinfo/info.xml` touches the three `<description>` blocks and the one `<author>` line and no `<version>` or `<image-tag>` line, and `tar -xzOf` on the downloaded asset over `mcp_connector/appinfo/info.xml` is byte identical to `git show v0.1.10:appinfo/info.xml`, counting the long paragraph once, the `<author mail>` attribute as the old `k.cherif@outlook.de` and `admin@infranode.dev` three times, which is the enterprise contact in the English, German and French description and the payload this release exists for: the address moved in the section, and only the author attribute waits for 0.1.11 |

### The update keeps the connections

Measured on 2026-08-19 on the HaRP topology of `compose.exapp.yml`, on the published
artifacts and not on a local build. The two tool listings in the table are records of that
day and are left as they were recorded; the number a release has to list is held by
`tests/contract/test_tool_surface.py`, never by this page.

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
   A fifth place travels along and no gate holds it: the `Version <x>.` status line of
   `README.md`, `README.de.md` and `README.fr.md`. `README.md` ships inside the signed
   release tarball, so a stale line there is published and immutable (the 0.1.8 tarball
   says 0.1.7 for exactly this reason, review finding WR-03 of phase 11). Raise all
   three by hand in this step.
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
4. **Push the branch, then tag and push, with exactly that version.** This is the
   irreversible step. The branch push comes first and is not optional: the store
   description links to `blob/main/...` docs and the screenshots load from
   `raw.githubusercontent.com/.../main/...`, so a tag whose commits are not on the
   public `main` publishes a release whose linked pages show an older state (the
   0.1.8 release found 42 unpushed commits at exactly this point).
   ```
   git push origin main
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

   **This step needs the store session, not necessarily a person at the keyboard.** The
   token belongs to the store account, it is not a repository secret and it is
   deliberately not stored in this working copy. Reading it out of a browser profile
   from outside is not a way in: the profile of a running browser holds its cookie
   database under an exclusive lock, and from Chrome 127 on those cookies are bound to
   the installation that wrote them. What does work, and is how both 0.1.1 and 0.1.2
   were submitted, is running the upload inside the page context of an already signed
   in browser session: open `https://apps.nextcloud.com/account/token`, read the token
   from the page and POST to `/api/v1/apps/releases` from within that page, so the
   token never leaves the browser. Without such a session, whoever holds the account
   either pastes the download URL and the signature into the form at
   `https://apps.nextcloud.com/developer/apps/releases/new` or runs the `curl` above
   with the token in the environment.

   Steps 1 to 6 leave nothing to redo: the signature is a pure function of the published
   asset and the key, so it is recomputed with the two commands of step 6 whenever it is
   needed, and it never has to be written down or passed along.
8. **Run the five proofs, and write each one into the table above with its date.**
   ```
   curl -sS https://apps.nextcloud.com/api/v1/appapi_apps.json           # release line <version>, same platform span
   curl -I  https://github.com/street1983nk/nextcloud-mcp-connector/releases/download/v<version>/mcp_connector-<version>.tar.gz
   TOKEN=$(curl -sS "https://ghcr.io/token?scope=repository:street1983nk/mcp_connector:pull&service=ghcr.io" | grep -o '"token":"[^"]*' | cut -d'"' -f4)
   curl -sS -H "Authorization: Bearer $TOKEN" \
     -H "Accept: application/vnd.oci.image.index.v1+json" \
     https://ghcr.io/v2/street1983nk/mcp_connector/manifests/<version>   # OCI index, amd64 and arm64
   curl -sS -H "Authorization: Bearer $TOKEN" \
     https://ghcr.io/v2/street1983nk/mcp_connector/tags/list             # every released tag
   curl -sS https://apps.nextcloud.com/api/v1/appapi_apps.json           # authors[0].mail of mcp_connector
   ```

   The fifth proof exists because the `authors` field of the manifest is public store surface
   that no gate holds: it carried the same address through ten releases without anyone checking
   it, and only the v1.4 review found it. Read the `mail` of `authors[0]` for `mcp_connector` in
   the catalogue and compare it against `<author mail>` in `appinfo/info.xml` at the tag. They
   must be the same string, and the row records which one it is.

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

## Being found in the store

Measured on 2026-08-22 against the live store search, because guessing here is expensive.

The search matches the app name, the summary and the description as substrings, and every
term of a multi word query has to appear somewhere in that text.

**Measure it with `%20`, never with `+`.** The store takes a `+` in the query string
literally, so `?search=mcp+server` searches for the string `mcp+server`, finds nothing and
looks exactly like a missing keyword. This cost one wrong conclusion on 2026-08-22, written
into this file and corrected an hour later. Use
`curl -sS "https://apps.nextcloud.com/?search=mcp%20server"`, and read the whole result
list, not the first page of it: a common word like `ai` answers with 374 apps.

| Query | Before 0.1.7 | After 0.1.7 |
|-------|--------------|-------------|
| `mcp` | first | first |
| `mcp server` | not found, the word `server` was nowhere in the text | **first** |
| `ChatGPT` | not found, the word was nowhere in the text | **first of two** |
| `model context protocol` | first | first |
| `ai assistant` | not measured | first |
| `claude` | fourth | fourth, behind `claudebot`, `aiquila` and `ktec_talkbot` |
| `ai` | buried | 54th of 374 |

One oddity, measured three times and not explained: `chatgpt` in lower case answers with one
app and it is not this one, while `ChatGPT` answers with two and this app is first. Case does
not matter for other terms of this app, `tables`, `talk` and `nextcloud` each answer the same
in both spellings, and the word is present in the catalogue text in both the summary and the
description. So this is a store side asymmetry, not a gap in the manifest, and no wording
change here can close it.

Two conclusions that outlast this release. First, the summary is the highest value real
estate in the manifest: it is short, it is indexed, and it is the only place where the words
a person types can be placed without bending the description out of shape. Second, a term
that is true of this app and missing from its text is a self inflicted wound, so a new
capability belongs in the summary or the description on the day it ships, not later.

The categories are the other half. The store has an `ai` category, this app was in
`integration` only, so nobody browsing AI ever saw it. `info.xsd` allows `category`
unbounded; since 0.1.7 the app is in `ai`, `integration` and `tools`.

What cannot be promised: a position. Presence in the result set follows from the text and
is under our control. The order does not: it depends on the store's ranking and on what
every other app is called. `claude` is the honest example, where an app literally named
`claudebot` will outrank a connector whatever we write.

Cache note, measured twice on 2026-08-22: an upload answers 201 immediately, but the store
serves the app detail page, the catalogue endpoint and the search index from caches that
refresh minutes apart. A change is not lost when it is not visible one minute after the
upload, and it must not be chased with another release. Version 0.1.5 and 0.1.6 were both
spent on that mistake.
