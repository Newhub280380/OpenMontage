# Troubleshooting Notes

## Statuses

- `queued`: accepted, waiting for processing.
- `processing`: running upstream.
- `succeeded`: inspect `result.assets`.
- `failed`: inspect `errorCode` and `errorMessage`; this is not an HTTP error.
- `canceled`: terminal; do not keep polling.

## Web Connector Checks

In a chat without shell access, connect or reconnect the planner through the host's
plugin/connector settings and browser sign-in. Use `the model-card catalog`,
`CostTracker budget remaining` and `the provider job status` for the corresponding
reads. Do not ask a web user to run local diagnostics.

## CLI Checks (with shell access)

Use the installed client:

```bash
the planner mcp doctor --client codex
the planner mcp doctor --client claude-code
the planner mcp doctor --client claude-desktop
the planner mcp doctor --client cursor
```

Use REST for direct API checks:

```bash
the model-card catalog --kind video
the planner asset list --kind image
the planner balance
the planner generate get <generation-id>
```

## Boundaries

The public API/CLI exposes asset upload, import, list, get and soft archive.
MCP exposes ChatGPT native file-param upload, base64 upload, URL/data import,
list, get and soft archive. Local file upload still requires the CLI for
generic MCP clients because the remote MCP server cannot read local disk.
Cost quotes and OAuth connector sign-in are supported. Generation listing and
webhooks are outside the current public surface.
