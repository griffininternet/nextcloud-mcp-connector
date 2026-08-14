# App ID Freeze

**Status:** frozen
**Decision date:** 2026-08-14
**Scope:** every public identifier of this project (Nextcloud app id, display name, Python package, PyPI distribution, CLI entry point, Git repository)

## Decision

| Identifier | Frozen value |
|------------|--------------|
| Nextcloud app id | `mcp_connector` |
| Display name | MCP Connector |
| Python package | `mcp_connector` (`src/mcp_connector`) |
| PyPI distribution | `nextcloud-mcp-connector` |
| CLI entry point | `nc-mcp` (stdio) |
| Git repository | `street1983nk/nextcloud-mcp-connector` |
| License | AGPL-3.0-or-later |

## Rationale

1. **No "nextcloud" inside the app id.** The Nextcloud App Store rejects app ids that carry the
   Nextcloud trademark, so the store-facing id is `mcp_connector` and not `nextcloud_mcp_connector`.
2. **The bare PyPI name is taken.** `nextcloud-mcp-server` is already published by the community
   project of the same name, so the distribution is published as `nextcloud-mcp-connector`. The
   longer PyPI name is fine: it is a search term, not a store id.
3. **The Python package matches the app id.** `mcp_connector` keeps the import path, the app id
   and the ExApp container identity aligned, which removes one class of packaging mistakes when
   phase 2 wraps this server into an ExApp.
4. **The repository keeps the searchable name.** GitHub is the discovery surface, so the repository
   is named `nextcloud-mcp-connector` even though the app id is shorter.

## Availability evidence

All checks were executed on **2026-08-14** from the development host.

### 1. PyPI distribution name is free

```
curl -s -o /dev/null -w "%{http_code}" https://pypi.org/pypi/nextcloud-mcp-connector/json
404

curl -s -o /dev/null -w "%{http_code}" https://pypi.org/simple/nextcloud-mcp-connector/
404
```

Control check, the taken community name:

```
curl -s -o /dev/null -w "%{http_code}" https://pypi.org/pypi/nextcloud-mcp-server/json
200
```

Note on method: the human facing page `https://pypi.org/project/nextcloud-mcp-connector/` answers
`200` even for unknown projects, because an anti bot challenge page is served before the real
response. Use the JSON API or the simple index for machine checks, as done above.

### 2. No app with the id `mcp_connector` in the Nextcloud App Store

```
curl -s https://apps.nextcloud.com/api/v1/platform/34.0.0/apps.json
http 200, 378 apps, no app with id mcp_connector, no app id containing "mcp"

curl -s https://apps.nextcloud.com/api/v1/platform/30.0.0/apps.json
http 200, 423 apps, no app with id mcp_connector, no app id containing "mcp"

curl -s -o /dev/null -w "%{http_code}" https://apps.nextcloud.com/apps/mcp_connector
404          (control: https://apps.nextcloud.com/apps/notes answers 200)
```

The two platform queries cover both a current and an older server generation, so an app that is
only published for older Nextcloud releases would have shown up as well.

### 3. No pending certificate request for `mcp_connector`

```
gh api repos/nextcloud/app-certificate-requests/contents --jq 'length'
838

gh api repos/nextcloud/app-certificate-requests/contents --jq '.[].name' | grep -i mcp
(no match)

gh api "search/code?q=mcp_connector+repo:nextcloud/app-certificate-requests" --jq '.total_count'
0
```

### 4. The repository name was free

```
curl -s -o /dev/null -w "%{http_code}" https://api.github.com/repos/street1983nk/nextcloud-mcp-connector
404          (checked before the repository was created on 2026-08-14)
```

## Trademark review (2026-08-14, owner-approved)

Checked against the [Nextcloud trademark policy](https://nextcloud.com/trademarks/) and the App
Store rule that an app must not use "Nextcloud" in its name:

- **App id, display name, Python package, CLI**: compliant, none of them carries the mark.
  This is the surface the App Store review actually checks.
- **Git repository `nextcloud-mcp-connector`**: kept. The policy explicitly permits the mark in
  file, folder, directory and path names; a repository name is such a path, and the pattern is
  established community practice (for example `nextcloud-mcp-server`).
- **PyPI distribution `nextcloud-mcp-connector`**: kept deliberately. A distribution name is a
  search term rather than a store-facing product name, and the long-published community
  distribution `nextcloud-mcp-server` sets the precedent. Should Nextcloud GmbH ever object, the
  fallback name is `mcp-connector-for-nextcloud` ("X for Nextcloud" is the tolerated descriptive
  form); as long as nothing is published on PyPI that rename stays free of cost.

## Cost of a later rename

A rename is cheap only until the certificate signing request (CSR) is merged into
`nextcloud/app-certificate-requests`. After that merge the App Store certificate is bound to the
app id: every release is signed with a certificate that is issued for exactly this id.

Renaming after the CSR means:

- a new CSR and a new review round with the Nextcloud App Store team,
- a new certificate, so every published release has to be re-signed,
- a store entry that cannot be migrated, which drops ratings and install counts,
- installed instances that do not upgrade, because the old and the new app are different apps,
- a PyPI distribution rename with a shim release, plus a repository rename with redirects.

The id is therefore frozen now, before the CSR, and is treated as a public contract from this
point on.

## Related

- Project README: [../README.md](../README.md)
- Store rule on the id, license and release signing: Nextcloud App Store documentation
- Requirement `EXAPP-03` (freeze the app id in week 1), decisions D-01 and D-02
