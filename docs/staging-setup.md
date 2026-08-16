# Staging instance for the hosted connectors

**Status:** prepared, not yet run
**Scope:** one throwaway virtual machine that is reachable from the internet over TLS, so
that the Claude.ai connector and the ChatGPT connector can be measured end to end
(plan 03-09, requirement `AUTH-04`).

Everything before this point was proven against a topology on `127.0.0.1`. The two hosted
connectors cannot reach that, because they run in someone else's data centre and connect
inward. This document is the whole path from an empty machine to a URL that can be pasted
into both clients, in the order it has to happen.

## What this instance is not

It is a **throwaway**, and it is meant to be deleted the same day the measurement is done.

* **No real data.** Two accounts, `alice` and `bob`, both created by the bootstrap, both
  with generated passwords and nothing in them but a calendar, an address book and one
  placeholder file. Nothing personal is uploaded to this machine, and no account of a real
  Nextcloud is connected to it.
* **Not a production deployment.** The deploy daemon holds the Docker socket, which is
  effectively root on the host (T-02-31). That is acceptable for a machine that exists for
  a few hours and is then destroyed, and it is not acceptable as a permanent arrangement.
* **Not a reference for how to run this app.** The production notes live in
  [oauth-setup.md](./oauth-setup.md), section "Security notes for production". This file
  optimises for "reachable and measurable today", not for "operable next year".
* **Not something to keep around.** Dynamic client registration is open on it, so any
  client that finds the URL can register. That is the point during the measurement and a
  liability afterwards.

When the measurement is finished, go to [Teardown](#6-teardown) and do all four steps.

## 0. What to order

| Item | Value | Why |
|------|-------|-----|
| Virtual machine | 2 vCPU, 4 GB RAM, 20 GB disk | Nextcloud, HaRP, a registry and the ExApp container, plus one image build |
| Distribution | Debian 13 or Ubuntu 24.04 | `scripts/setup_staging.sh` installs packages with apt and refuses anything else by name |
| Network | one public IPv4 address, ports 80 and 443 reachable from the internet | port 80 carries the certificate challenge, port 443 carries every client |
| Name | a host name in a zone you control, for example `nc-staging.example.com` | the certificate and the OAuth identity of the app are both this name |

No database server, no mail, no backup. The instance holds nothing worth backing up.

## 1. Set the DNS record

The record must be a plain **A record, DNS-only**. On Cloudflare that is the grey cloud,
not the orange one. Behind the proxy the certificate challenge never arrives at the
machine, and the streaming response of the MCP transport passes through a third party.

With the script, from any machine that has the token:

```bash
export CF_DNS_TOKEN=...        # Zone -> DNS -> Edit on that zone, never passed as an argument
export CF_ZONE_ID=...          # "Zone ID" on the overview page of the zone
export NC_STAGING_DOMAIN=nc-staging.example.com
bash scripts/staging_dns.sh 203.0.113.10      # the address of the new machine
```

Run without the address argument, the script takes the public address of the machine it
runs on, which is what you want when you run it on the staging machine itself. It updates
an existing record instead of creating a second one, and it refuses to finish if the record
comes back proxied.

By hand it is the same record: type `A`, name `nc-staging`, content the address of the
machine, TTL 120, proxy **off**.

Check it before continuing:

```bash
getent hosts nc-staging.example.com
```

## 2. Get the repository onto the machine

```bash
ssh root@203.0.113.10
apt-get update && apt-get install -y git
git clone https://github.com/street1983nk/nextcloud-mcp-connector.git
cd nextcloud-mcp-connector
```

## 3. Run the bootstrap

```bash
export NC_STAGING_DOMAIN=nc-staging.example.com
bash scripts/setup_staging.sh
```

One command, ten to twenty minutes, most of it the image build. It is idempotent: if it
stops somewhere, fix what it named and run it again.

What it does, in this order:

1. checks that it runs as root, that the distribution is one it knows, that the name
   already points at this machine, that ports 80 and 443 are free and that a firewall, if
   there is one, lets both through. Every one of these stops the run with a sentence that
   names the fix, because all of them are cheaper to fix now than after a failed
   certificate order.
2. installs Docker, the compose plugin and buildx from the Docker apt repository.
3. generates the secrets into `.env.staging`: the HaRP shared key, the administrator
   password and the passwords of the two accounts. The file is written with mode 600 and is
   git ignored. A second run keeps the values it already generated.
4. starts the topology from `compose.staging.yml` and waits until `https://<name>` answers,
   which is also the proof that the certificate was issued.
5. runs `scripts/bootstrap_exapp.sh --staging`, which installs the apps, creates the two
   accounts, registers the deploy daemon, builds the image, registers the ExApp with the
   **public** URL as `NC_MCP_PUBLIC_URL` and writes `.env.staging.app`.
6. prints the three self checks below.

Unlike the local topology, the bruteforce guard stays enabled here, and no password has a
documented default.

## 4. Verify

The bootstrap runs these itself and prints `PASS` or `FAIL` per line. The same three by
hand, to have them in a terminal that can be quoted later:

```bash
export NC_STAGING_DOMAIN=nc-staging.example.com
BASE="https://${NC_STAGING_DOMAIN}/exapps/mcp_connector"

# 1. the protected resource document, without any authentication
curl -sS -o /dev/null -w '%{http_code}\n' "$BASE/.well-known/oauth-protected-resource/mcp"

# 2. the authorization server document
curl -sS -o /dev/null -w '%{http_code}\n' "$BASE/.well-known/oauth-authorization-server"

# 3. the transport without a token: 401, and the pointer a client follows next
curl -sS -o /dev/null -D - -X POST \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  --data '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' \
  "$BASE/mcp" | grep -i 'www-authenticate'
```

Expected: `200`, `200`, and a `401` whose `WWW-Authenticate` header carries
`resource_metadata="https://<name>/exapps/mcp_connector/.well-known/oauth-protected-resource/mcp"`.

The `resource` value inside document 1 has to be exactly the URL a user types, character
for character. This is the string that goes into Claude.ai and into ChatGPT:

```
https://nc-staging.example.com/exapps/mcp_connector/mcp
```

The account passwords for the sign in on the consent screen are in `.env.staging` on the
machine:

```bash
cat .env.staging
```

## 5. During the measurement

The access log is the instrument. It shows which discovery path a connector tries, in which
order, with which status code, and how long `/token` took:

```bash
docker compose --env-file .env.staging -f compose.staging.yml logs -f caddy
```

**The counter measurement for assumption A2.** The two rewrite rules for the canonical root
paths are the only optional part of this setup, and plan 03-09 exists partly to find out
whether the hosted connectors need them. Measure with them, then without them:

```bash
# comment out the two `route /.well-known/...` blocks in deploy/Caddyfile.staging, then:
docker compose --env-file .env.staging -f compose.staging.yml exec caddy \
  caddy reload --config /etc/caddy/Caddyfile
```

Both paths answer `404` afterwards, which is the state a self hoster without the rules is
in. Repeat the connection attempt from a client and note whether it still finds the
authorization server. Undo the comment and reload again to get back to the measured state.

Note for the report: log lines carry query strings, and an authorization request carries
`state` and `code_challenge` in its query. Quote paths and status codes, never a raw line
(T-03-81).

## 6. Teardown

All four steps, on the day the measurement is done.

1. Disconnect the connector in Claude.ai and in ChatGPT, and revoke the entries in
   Nextcloud under "Devices and sessions". This is also the last measurement of the plan:
   a client has to be able to build a fresh connection afterwards.
2. Destroy the topology together with its data, including the certificate store:

   ```bash
   docker compose --env-file .env.staging -f compose.staging.yml down -v
   ```

3. Delete the virtual machine at the provider. The two secret files never leave it, so
   deleting the machine is what disposes of them.
4. Delete the DNS record, or point it somewhere harmless. A name that still resolves to a
   machine somebody else got next is worse than no name.

## Variables

| Variable | Read by | Required | Meaning |
|----------|---------|----------|---------|
| `NC_STAGING_DOMAIN` | everything | yes | the public host name, without scheme and without path |
| `CF_DNS_TOKEN` | `scripts/staging_dns.sh` | for the DNS step | Cloudflare API token, `Zone -> DNS -> Edit`. From the environment only, never an argument, never a file in this repository |
| `CF_ZONE_ID` | `scripts/staging_dns.sh` | for the DNS step | the id of the zone the name belongs to |
| `NC_STAGING_IP` | `scripts/staging_dns.sh` | no | the address to write into the record, if it is not the address of the machine running the script |
| `NC_STAGING_ADMIN_USER` | `scripts/setup_staging.sh` | no | administrator account name, default `admin` |
| `NC_STAGING_SKIP_DNS_CHECK` | `scripts/setup_staging.sh` | no | skips the "does the name point here" check, for a machine behind NAT whose record is known to be right |
| `HP_LOG_LEVEL` | `compose.staging.yml` | no | `info` makes a failing registration debuggable |

Generated on the machine, never set by hand: `NC_STAGING_ADMIN_PASSWORD`, `HP_SHARED_KEY`,
`NC_EXAPP_ALICE_PASSWORD`, `NC_EXAPP_BOB_PASSWORD` in `.env.staging`, and `APP_SECRET` plus
the two app passwords in `.env.staging.app`. Both files are git ignored, and neither is
copied off the machine.

## When something does not work

| Symptom | Cause, in order of likelihood |
|---------|-------------------------------|
| `setup_staging.sh` stops at "does not resolve" or "points at" | the A record is missing, still points at the old machine, or has not propagated yet |
| The certificate never arrives, `https://` never answers | the record is proxied (orange cloud), port 80 is closed in a provider firewall, or the name points elsewhere. Look at `logs caddy` |
| "too many certificates already issued" | five orders for one name in a week. Wait, or use a second name. This is why the certificate volume exists and why the checks run before the topology starts |
| "heartbeat check failed" during the ExApp registration | the deploy daemon cannot reach Nextcloud under its public URL. `compose.staging.yml` gives the reverse proxy the public name as a network alias for exactly this reason |
| A client says it cannot find the authorization server | that is a measurement result, not a fault. Note it, then check whether the two rewrite rules are active |
| `/mcp` answers 401 without `resource_metadata` | the app does not know its public URL. `NC_MCP_PUBLIC_URL` has to be the public address; this was measured in plan 03-08 |

## Related

- The OAuth configuration itself: [oauth-setup.md](./oauth-setup.md)
- Installing the ExApp on a normal instance: [exapp-install.md](./exapp-install.md)
- What a user enters into a client: [client-setup.md](./client-setup.md)
