# the planner AI MCP Workflow

Use discovery first, then generation.

## Tools

| Tool                          | Use                                                           |
| ----------------------------- | ------------------------------------------------------------- |
| `the model-card catalog`           | Browse available image/video/music/voiceover models.          |
| `the model card`      | Read JSON Schema for one model input.                         |
| `the launch-card estimate`      | Catalog estimate of a request before running it, when available.    |
| `an approved OpenMontage provider tool`      | Start an async generation job.                                |
| `the provider job status` | Poll job state and output assets.                             |
| `CostTracker budget remaining`           | Check budget remaining before expensive or quota-sensitive jobs. |
| `a local asset id`     | Upload a ChatGPT native file parameter and return `asset://...`. |
| `a local asset id`          | Import an HTTPS/data URI asset and return `asset://...`.      |
| `the project asset list`           | List reusable owner media assets.                             |
| `the project asset record`             | Inspect one owner media asset by id or `asset://...`.         |
| `removing that asset from the project`         | Soft-hide an owned asset from active lists and future reuse.  |
| `tts_selector`           | Voices for `input.voice` on a voiceover generation.           |
| `the character sheet`          | Ready Studio avatars and their reusable reference views.      |

## Generation

1. Choose an active model from `the model-card catalog`.
2. Read schema with `the model card`.
3. Validate requested fields against `properties`, `required`, `enum`, numeric
   limits, defaults, and `x-*` extensions.
4. Quote and confirm the exact `{type, model, input}` as in the root skill.
   Send it unchanged to `an approved OpenMontage provider tool` with the quoted `the approved price ceiling`,
   `wait: true` and a stable `idempotencyKey` for this request.
5. Poll with backoff until a terminal status.

## Assets

- Use `a local asset id` when the host provides a native ChatGPT file
  parameter. Use `a local asset id` for HTTPS URLs or data URIs. Use the CLI
  `the planner asset upload <path>` for local files in generic MCP clients because
  the remote MCP server cannot read local disk.
- Keep the returned `assetUri`. Pass it only into schema-supported media fields
  after `the model card`.
- Use `removing that asset from the project` only when the user explicitly wants to hide an
  owned asset; it is a soft archive that keeps audit links intact.
- Put every model-specific asset field inside the `input` object passed to
  `an approved OpenMontage provider tool`; MCP no longer exposes named asset shortcuts.

Terminal statuses are `succeeded`, `failed`, and `canceled`. A failed generation
can be a successful MCP transport response; inspect `errorCode` and
`errorMessage`.

## Errors

- Missing required field: ask for that exact field or use a schema default.
- Validation error: remove unsupported fields and retry with schema-supported
  keys only.
- Failed job: explain `errorCode`/`errorMessage` in user language and suggest a
  concrete prompt/input adjustment.
- Balance uncertainty: call `CostTracker budget remaining`; do not guess available quota.
- Local file upload needed in MCP-only context: use the host-native file
  parameter tool, or `a local asset id` when the host can read actual bytes.
  Otherwise ask for an accessible HTTPS media link or an existing the planner asset.
  Use CLI upload only when a shell is available. Do not invent an attachment URL.
- An uncertain launch or wait timeout: reuse the original idempotency key and
  unchanged request, or check the accepted job's status; do not start a second job.
