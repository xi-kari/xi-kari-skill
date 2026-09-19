# Codex semantic authoring adapter protocol

`scripts/xi_kari_codex_authoring_adapter.py` is the shipped Codex provider for
runtime-owned semantic stability authoring. It accepts one canonical UTF-8 JSON
object on standard input and returns an adapter-owned envelope containing the
complete semantic object and observed provider execution evidence on standard
output. Diagnostics are written to standard error. The executable
accepts no command-line arguments.

## Request envelope

The envelope protocol is
`xi-kari.v3.codex-semantic-authoring-adapter/v1` and has exactly these fields:

```json
{
  "protocol": "xi-kari.v3.codex-semantic-authoring-adapter/v1",
  "provider_binding": {},
  "semantic_request": {}
}
```

The XK0 capability snapshot selects this envelope with the formal semantic
adapter binding protocol `xi-kari.v3.semantic-authoring-adapter/v3` and profile
`production-codex`. That binding freezes the repository-shipped adapter path,
its SHA-256, its one-element invocation vector, the complete provider binding,
and the provider-binding SHA-256. The public `init` and `prepare` commands are
read-only production preflights. Only `execute` starts and observes the real
author before creating a formal run. The active contract is
`production-authoring-v3`; earlier profiles are rejected without migration.
A production fork or repair revalidates and freezes the parent
formal adapter and provider into the child, starts a fresh base-authoring
process, and persists its new request, prompt, raw output, event stream,
receipt, semantic read trace, and ontology read trace.

`semantic_request` is the existing
`xi-kari.v3.semantic-authoring-request` v1 variant payload created by the
runtime. It remains runtime-owned. The adapter validates its exact top-level
surface, variant stance and time window, frozen `problem_action` enum,
`advice_requested` boolean, `deliverable_type`, and its source paths. Its
`source_inputs.repository_root` must equal the provider binding and the Skill
root that ships the adapter. The reader and source-manifest paths must be the
canonical paths under that root.

The request envelope must be smaller than 256 KiB. `source_inputs` carries the
compact runtime-owned `concept_authority` binding with candidate and ontology
counts plus repository-file hashes. It must not carry the expanded
`concept_disposition` rows.

`provider_binding` uses protocol
`xi-kari.v3.codex-provider-binding/v1` and has exactly these fields:

- `repository_root`
- `executable_path` and `executable_sha256`
- `argv` and `argv_sha256`
- `model`, defaulting to `gpt-5.6-sol`, overridable via the `XI_KARI_PROVIDER_MODEL`
  environment variable
- `reasoning_effort`, empty by default (the provider default applies), overridable
  via `XI_KARI_REASONING_EFFORT`
- `approval_policy`, fixed to `never`
- `sandbox`, fixed to `workspace-write` in a new private author workspace;
  default temporary writable roots are explicitly excluded
- `ephemeral` and `ignore_user_config`, fixed to `true`; `strict_config`, recorded
  as a boolean
- `web_search`, fixed to `disabled`
- `timeout_seconds`, an integer from 1 through 7200, default 1200

The Codex path must be a canonical absolute path to an executable regular file.
No path component may be a symbolic link. The adapter verifies the executable
hash before and after execution.

The bound `argv` is deterministic for a given environment. `<codex>` is the
bound `executable_path`; `<model>` comes from `XI_KARI_PROVIDER_MODEL`
(default `gpt-5.6-sol`). When `XI_KARI_REASONING_EFFORT` is set, a
`model_reasoning_effort` config flag is appended after the model. When
`XI_KARI_PROVIDER_BASE_URL` is set, four `model_provider`/`model_providers.*`
config flags are appended so the run uses that endpoint with the locally
stored credential.

```text
<codex> exec
  --ephemeral
  --ignore-user-config
  --model <model>
  [--config model_reasoning_effort="<effort>"]
  [--config model_provider="xi_kari_local"
   --config model_providers.xi_kari_local.name="xi_kari_local"
   --config model_providers.xi_kari_local.base_url="<base-url>"
   --config model_providers.xi_kari_local.wire_api="<wire-api>"]
  --config web_search="disabled"
  --config approval_policy="never"
  --config sandbox_workspace_write.exclude_tmpdir_env_var=true
  --config sandbox_workspace_write.exclude_slash_tmp=true
  --config sandbox_workspace_write.writable_roots=[]
  --sandbox workspace-write
  --skip-git-repo-check
  --color never
```

On Windows the invocation also binds `windows.sandbox="elevated"` so the
requested workspace policy does not degrade to read-only when user config is
ignored. This does not grant write access to the source repository.

The adapter captures the JSONL event stream and appends these handoff arguments.
The last-message path is in the parent capture directory, outside the author's
writable workspace.

```text
--json
--output-last-message <capture-directory>/last-message.txt
-
```

Codex runs in a fresh process group with a new private author workspace as its
working directory. The first prompt line is the explicit invocation
`$xi-kari-skill`. The source repository remains outside the writable workspace;
the model receives no repository or installation write capability. Web search is
disabled because XK9 variants operate on the runtime-frozen evidence context.

## Output and authority boundary

The author writes the complete semantic JSON to the fixed workspace filename
`semantic-output.json`; the last message is exactly `SEMANTIC_OUTPUT_READY`.
Neither a summary, inline JSON nor a model-selected path substitutes for that
file. The runtime reads the file from disk, rejects symlink/reparse paths,
enforces byte and UTF-8 limits, rejects duplicate JSON keys and
non-finite values, validates it against
`schemas/xk-codex-semantic-authoring-output.schema.json`, checks the requested
variant fields, and rejects runtime, receipt, phase, validator, or terminal
authority fields anywhere in the object.

Only the semantic fields consumed by the XK9 authoring seam are allowed,
including complete `reader_sections` and the frozen delivery type. The model
cannot provide provider execution metadata. The adapter adds independently
observed provider process IDs, the captured event stream, and the complete
semantic file bytes and hashes to its response. It does not accept a model-authored
receipt, completion claim, process identity, phase record, or terminal record.
The parent runtime remains the sole owner of adapter inputs, execution receipts,
and XK0-XK12 authority.

For each variant, the runtime receipt protocol
`xi-kari.v3.semantic-authoring-receipt/v3` binds the semantic-request hash and
byte count separately from the complete outer-envelope hash and byte count. It
also binds the provider-binding, provider-executable, and provider-argv hashes,
plus the adapter PID observed by the parent runtime. These values are rebuilt
from the XK0 binding and runtime-owned variant request during fresh validation;
they are never read from the model payload. Any run without a valid signed
`terminal_state=complete`, including an unsigned 13-phase promotion candidate,
verifies the adapter and provider files against the frozen paths and hashes.
Once the signed XK12 terminal state is complete, validation uses the frozen
binding and sealed receipts without requiring the external provider executable
to remain present.

## Failure and cleanup

The adapter fails closed with empty standard output for malformed input,
provider drift, a nonzero Codex exit, timeout, oversized diagnostics or model
output, unsafe last-message paths, schema violations, semantic-surface drift, or
model-authored authority. It kills and reaps the complete Codex process group on
success and failure. On POSIX, an independent pipe watchdog kills that group and
removes the temporary workspace if the adapter itself disappears, including by
`SIGKILL`.
