# MCP Client Examples

## Generic Streamable HTTP

Run:

```bash
. .venv/bin/activate
keryx mcp --config local.config.yaml
```

The MCP server exposes tools such as:

- `search_notes`
- `open_note`
- `capture_note`
- `append_session_note`
- `get_project_context`
- `create_decision`
- `create_task`
- `list_recent_notes`
- `refresh_index`
- `generate_summary`
- `link_notes`

## Hermes-Style Client Config

Example shape:

```json
{
  "mcpServers": {
    "keryx": {
      "transport": {
        "type": "streamable-http",
        "url": "http://127.0.0.1:8001/mcp"
      }
    }
  }
}
```

## Claude Code / Codex-Style Local Tooling

If the client supports external MCP servers, point it at the same local URL and use the exposed tools instead of direct vault filesystem writes. The gateway is intended to be the stable interface regardless of the upstream agent.

For Codex on the same machine:

```bash
codex mcp add keryx --url http://127.0.0.1:8001/mcp
```

## Tailnet-Only MCP

For another machine in the same Tailscale tailnet, expose Keryx with Tailscale Serve:

```bash
tailscale serve --bg --https=10000 --yes http://127.0.0.1:8001
```

Then configure the remote MCP client with the tailnet URL:

```bash
codex mcp add keryx --url https://your-device.your-tailnet.ts.net:10000/mcp
```

Do not use Tailscale Funnel unless you intentionally want public internet exposure and have added stronger Keryx authentication.
