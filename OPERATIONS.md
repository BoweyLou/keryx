# Operations

## Local Commands

Use the [`Makefile`](Makefile) for the common workflows.

```bash
make install
make test
make index
make serve
make mcp
```

Preferred CLI name:

- `keryx`

Compatibility alias:

- `knowledge-gateway`

The default config is `local.config.yaml`. Override it when needed:

```bash
make index CONFIG=/path/to/config.yaml
```

## Runtime Layout

There are two separate runtimes by design.

1. Repo-local development runtime:
   - `.venv/`
   - used for development, tests, and manual local runs
2. launchd runtime:
   - `~/Library/Application Support/keryx/venv`
   - used by macOS LaunchAgents

The second runtime exists because launchd could not reliably access the repo-local virtualenv inside `~/Documents/...`.

## launchd

Install or refresh the background services:

```bash
make install-launchd
```

Service labels:

- `io.keryx.api`
- `io.keryx.mcp`

Check status:

```bash
make status-launchd
```

Restart after config or code changes:

```bash
make install-launchd
make restart-launchd
```

## Verification

HTTP API:

```bash
make health
```

Expected endpoint:

- `http://127.0.0.1:8765/health`

MCP:

```bash
make mcp-check
```

Expected endpoint:

- `http://127.0.0.1:8001/mcp`

## Tailscale Serve

Keryx can be exposed privately to other machines in your tailnet with Tailscale Serve.

Use `tailscale serve`, not `tailscale funnel`. Serve is tailnet-only; Funnel makes the service internet-accessible.

See [`SECURITY.md`](SECURITY.md) before enabling remote access.

Recommended shape:

```bash
tailscale serve --bg --https=10000 --yes http://127.0.0.1:8001
```

That exposes the MCP server at:

```text
https://your-device.your-tailnet.ts.net:10000/mcp
```

Keryx keeps MCP DNS-rebinding protection enabled. If you proxy through a tailnet hostname, add the hostname to your local config:

```yaml
mcp:
  allowed_hosts:
    - "your-device.your-tailnet.ts.net:*"
  allowed_origins:
    - "https://your-device.your-tailnet.ts.net:*"
```

Then restart the MCP service.

Verify locally:

```bash
KERYX_MCP_URL=https://your-device.your-tailnet.ts.net:10000/mcp make mcp-check
```

Configure Codex on another Tailscale-connected machine:

```bash
codex mcp add keryx --url https://your-device.your-tailnet.ts.net:10000/mcp
```

Disable the route:

```bash
tailscale serve --https=10000 off
```

## Logs

Tail the launchd logs:

```bash
make logs
```

Files:

- `~/Library/Logs/keryx/keryx-api.err.log`
- `~/Library/Logs/keryx/keryx-api.out.log`
- `~/Library/Logs/keryx/keryx-mcp.err.log`
- `~/Library/Logs/keryx/keryx-mcp.out.log`

## Updating The Published Runtime

The repo can change without affecting the launchd runtime until you reinstall it. After source changes:

```bash
make test
make install-launchd
```

That rebuilds and reinstalls the package into `~/Library/Application Support/keryx/venv` and then reloads both LaunchAgents.

## Git And Sharing

The repo currently excludes local-only artifacts through [.gitignore](.gitignore):

- `.env`
- `local.config.yaml`
- `.venv/`
- `.data/`
- `.pytest_cache/`

Before making the repo public later, check these areas again:

1. `config.example.yaml`
   Ensure it contains placeholders only.
2. `examples/`
   Ensure no private vault paths or local hostnames are embedded beyond localhost.
3. docs and comments
   Ensure no personal vault structure or note names are included unless you want them public.
4. Git history
   Confirm no sensitive file was ever committed before changing visibility.

## Troubleshooting

If launchd services stop starting, check:

1. `make status-launchd`
2. `make logs`
3. `curl http://127.0.0.1:8765/health`
4. confirm the runtime config exists:
   `~/Library/Application Support/keryx/local.config.yaml`
5. refresh the runtime:
   `make install-launchd`
