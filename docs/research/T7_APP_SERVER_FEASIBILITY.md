# T7 App Server Structured-Interactive Feasibility

- Date: 2026-09-14
- Decision: **NO-GO for a production Phase 5 integration**
- Tested CLI: `codex-cli 0.154.0`
- Official source tag: `rust-v0.154.0`
- Source commit: `6b9826e3aa83b1a5947db50f4332cb9c65f1b340`

## Decision summary

The official App Server can expose typed lifecycle, final-message, command, and
file-change items. The official remote CLI can also operate a real interactive
thread over that server, and a second connection can observe later turns in the
same thread after explicitly resuming it.

The candidate does not satisfy the Phase 5 `GO` gate for two independent
reasons:

1. the documented WebSocket transport used by the remote TUI is experimental
   and unsupported for production use; and
2. PatchTrace would have to implement and maintain an App Server client to
   initialize a connection, discover/correlate threads, resume the selected
   thread, consume notifications, and recover from connection and protocol
   failures. There is no documented passive event-export surface.

The interactive PTY therefore remains the supported compatibility path. This
result does not approve or reject a separately scoped `codex exec --json` mode.

## Evidence boundary

Research used current official documentation, the locally installed CLI's help
and generated schemas, the matching official source tag, and one disposable
end-to-end run. The observer stored only event kinds, lifecycle states,
identifiers, byte counts, hashes, exit codes, and file-change counts/kinds. It
excluded message text, command text/output, file paths/diffs, account data, and
configuration.

The throwaway observer is retained beside this note for review. It uses a
system-only `websocket-client` installation and is neither packaged nor added as
a project dependency.

## Five-question result

| Question | Observed answer | Limitation | Source |
| --- | --- | --- | --- |
| Do typed final-message, command-result, file-change, and lifecycle events exist? | **Yes.** `agentMessage`, `commandExecution`, and `fileChange` are typed thread items; `turn/started`, `item/completed`, and `turn/completed` provide lifecycle boundaries. Completed agent messages carry the final-answer phase, command items carry status/output/exit data, and file items carry structured changes. | The live observer sampled lifecycle and a completed final-answer item. Command and file shapes were confirmed from the generated version-matched schema rather than retained live payloads. | Official App Server documentation; local `generate-ts` and `generate-json-schema` output for 0.154.0. |
| Are events emitted for the same interactive session? | **Yes, after explicit subscription.** `codex --remote` operated the thread, while another initialized connection used `thread/resume` and received the next turn's item and lifecycle events with the same thread/turn IDs. | In the preconnected attempt, the observer received `thread/started` but no later events for that run. Matching source performs a best-effort automatic listener attachment, so the reason for the observed gap is unresolved and automatic attachment is not treated as verified. Explicit `thread/resume` is the successful demonstrated path. | Disposable runtime observation and matching official source listener logic. |
| Can PatchTrace obtain them officially without building its own client? | **No.** The protocol and schema are official, but observation requires a JSON-RPC App Server client. | The official remote CLI is the user-facing client; it does not provide a documented passive event stream for another local tool. | Official App Server client/protocol documentation and runtime handshake. |
| Are the required transport and fields stable for production? | **No.** The required WebSocket route is documented as experimental and unsupported for production. | Generated schemas reduce guessing for a pinned version but do not turn that transport into a supported production contract. | Official App Server transport documentation and local `[experimental]` CLI surface. |
| What is the minimum integration and maintenance burden? | **Disproportionate for Phase 5 while the transport is experimental.** | A production implementation would need process supervision, connection/auth initialization, thread selection and subscription, version/schema compatibility, notification correlation, reconnect/backpressure behavior, failure mapping, privacy filtering, and fixtures. The 145-line one-purpose observer excludes all of those production responsibilities. | Prototype size and observed connection/subscription behavior. |

## Version-matched schema evidence

The local CLI generated both TypeScript definitions and JSON Schema without
using a private format:

```text
codex app-server generate-ts --out <temporary-directory>/ts
codex app-server generate-json-schema --out <temporary-directory>/json-schema
```

Selected SHA-256 identities:

```text
v2 schema bundle:
f3487938786b729cb6773dbc9e83a7efab9c78c845db7094e8f539f373cbacc9

ServerNotification.ts:
dfd31c72d1319f069fcdf124bcae6368f15aa0dd0033350bf15519d3e3556d54

ItemCompletedNotification.ts:
f995b155f66203d5426881cc5920f1791ee1405b20a3cc46b5d62758198285cf

TurnCompletedNotification.ts:
1f56d73f2a773ab0c1d1171cbb7bbb7b1b136af5b33447663ba4faf33f42a25f
```

These hashes identify the inspected temporary outputs; the generated files are
not product artifacts or compatibility guarantees.

## End-to-end observation

The disposable test used an empty temporary Git repository and a local-only
listener:

```text
codex app-server --listen ws://127.0.0.1:<ephemeral-port>
codex --remote ws://127.0.0.1:<ephemeral-port> ...
```

The remote TUI successfully:

- ran a controlled command and displayed its expected output;
- created a controlled proof file with SHA-256
  `7300845114f3dd0ccaafb0be551c910c1231c39a6f88f24ac6d34814cd8fb0fc`;
- returned the controlled initial response; and
- accepted a follow-up in the same interactive thread.

After `thread/resume`, the sanitized observer captured this event sequence for
the follow-up:

```json
{"method":"turn/started","status":"inProgress","thread_id":"{thread}","turn_id":"{turn}"}
{"method":"item/started","item_type":"userMessage","thread_id":"{thread}","turn_id":"{turn}"}
{"method":"item/completed","item_type":"userMessage","thread_id":"{thread}","turn_id":"{turn}"}
{"method":"item/started","item_type":"agentMessage","phase":"final_answer","text_bytes":0,"thread_id":"{thread}","turn_id":"{turn}"}
{"method":"item/completed","item_type":"agentMessage","phase":"final_answer","text_bytes":16,"text_sha256":"53c453b0e1678fb89f903f772bd7dbdd39d22910dd88ac086edfc20c82e1104b","thread_id":"{thread}","turn_id":"{turn}"}
{"method":"turn/completed","status":"completed","thread_id":"{thread}","turn_id":"{turn}"}
```

The TUI and App Server were then stopped, and the listener port was confirmed
closed. The temporary run required trusting its empty test repository in the
local Codex UI. After the evidence was verified, cleanup removed only that
exact temporary-repository trust table from the local Codex configuration; the
side effect is not retained as PatchTrace product state.

## Source notes

The matching official source shows that thread listeners are associated with
initialized connection IDs, that a thread can have multiple connection IDs,
and that lifecycle notifications are sent to subscribed connections. The live
test confirms the relevant behavior for the detected version; source inspection
alone is not treated as a stability promise.

## Revisit triggers

Reconsider structured-interactive integration only if official documentation:

- promotes the required multi-client transport to a supported production
  surface;
- documents a passive subscription/export route or a materially smaller
  supported observer boundary; and
- gives compatible lifecycle and typed item guarantees for the fields
  PatchTrace needs.

## Official references

- [Codex App Server](https://developers.openai.com/codex/app-server/)
- [Codex source at `rust-v0.154.0`](https://github.com/openai/codex/tree/rust-v0.154.0/codex-rs/app-server)
