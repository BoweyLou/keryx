# Security And Privacy

Keryx is designed for local-first personal knowledge systems. Treat the Obsidian vault as sensitive by default.

## Default Exposure

The safe default is local-only:

- HTTP API: `http://127.0.0.1:8765`
- MCP server: `http://127.0.0.1:8001/mcp`

Do not bind these services to a public interface unless you have added authentication and reviewed the vault exposure model.

## Remote Access

For private remote access, use Tailscale Serve rather than Tailscale Funnel.

Recommended shape:

```bash
tailscale serve --bg --https=10000 --yes http://127.0.0.1:8001
```

Then configure the remote MCP client with the tailnet-only URL:

```bash
codex mcp add keryx --url https://your-device.your-tailnet.ts.net:10000/mcp
```

Do not use Tailscale Funnel for Keryx unless you intentionally want public internet exposure and have added stronger Keryx authentication.

## Host Header Protection

The MCP server keeps FastMCP DNS-rebinding protection enabled. If you proxy Keryx through a private tailnet hostname, explicitly allow that hostname in local config:

```yaml
mcp:
  allowed_hosts:
    - "your-device.your-tailnet.ts.net:*"
  allowed_origins:
    - "https://your-device.your-tailnet.ts.net:*"
```

Do not commit local hostnames, personal tailnet names, vault paths, or real tokens.

## Secrets

Keep secrets outside the vault and outside the repository.

Ignored local files include:

- `.env`
- `.env.local`
- `local.config.yaml`
- `.data/`
- `.venv/`

Use environment indirection for local tokens:

```yaml
security:
  local_token: "env:KB_LOCAL_TOKEN"
```

## Public Repo Checklist

Before publishing or force-refreshing the public repo, check:

```bash
git status --short --untracked-files=all
git grep -n -I -E 'personal-email|personal-hostname|vault-path|tskey-|BEGIN [A-Z ]*PRIVATE KEY' -- $(git ls-files)
git check-ignore -v local.config.yaml .env .data/knowledge-gateway.db .venv/pyvenv.cfg
```

Adapt the placeholder terms to match your own private names, hostnames, and absolute paths. Expected tracked findings should be placeholders only. The local config and database must remain ignored.

## Codex Cloud Note

Localhost and private tailnet URLs are appropriate for local Codex CLI sessions on trusted machines. Codex Cloud cannot reach your local `127.0.0.1` service and should not be pointed at a public Keryx endpoint without a deliberate authentication and redaction design.
