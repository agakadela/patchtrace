#!/usr/bin/env python3
"""Throwaway Phase 5 T7 observer; not PatchTrace production code.

The script initializes one App Server connection. It can listen before the
Codex remote TUI starts or explicitly resume known thread IDs supplied on the
command line. It records only bounded metadata for the feasibility decision;
message text, command output, diffs, configuration, account data, and
filesystem paths are deliberately excluded.

It intentionally uses the system ``websocket-client`` installation from the
disposable research environment. It is not a PatchTrace dependency or a basis
for a supported adapter.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import websocket

ALLOWED_METHODS = {
    "thread/started",
    "turn/started",
    "turn/completed",
    "item/started",
    "item/completed",
}


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _summarize(message: dict[str, Any]) -> dict[str, Any] | None:
    method = message.get("method")
    if method not in ALLOWED_METHODS:
        return None

    params = message.get("params") or {}
    summary: dict[str, Any] = {"method": method}

    if method == "thread/started":
        thread = params.get("thread") or {}
        summary.update(
            {
                "thread_id": thread.get("id"),
                "session_id": thread.get("sessionId"),
                "source": thread.get("source"),
                "cli_version": thread.get("cliVersion"),
            }
        )
        return summary

    turn = params.get("turn") or {}
    summary["thread_id"] = params.get("threadId")
    summary["turn_id"] = params.get("turnId") or turn.get("id")
    if method.startswith("turn/"):
        summary["status"] = turn.get("status")
        return summary

    item = params.get("item") or {}
    summary["item_type"] = item.get("type")
    summary["status"] = item.get("status")
    if item.get("type") == "agentMessage":
        text = item.get("text") or ""
        summary["phase"] = item.get("phase")
        summary["text_bytes"] = len(text.encode("utf-8"))
        summary["text_sha256"] = _digest(text)
    elif item.get("type") == "commandExecution":
        summary["exit_code"] = item.get("exitCode")
        summary["output_present"] = bool(item.get("aggregatedOutput"))
    elif item.get("type") == "fileChange":
        changes = item.get("changes") or []
        summary["change_count"] = len(changes)
        summary["change_kinds"] = sorted(
            str(change.get("kind")) for change in changes if change.get("kind")
        )
    return summary


def main() -> int:
    if len(sys.argv) < 3:
        print(
            "usage: observer.py <ws-url> <output-jsonl> [thread-id ...]",
            file=sys.stderr,
        )
        return 2

    socket = websocket.create_connection(sys.argv[1], timeout=10, suppress_origin=True)
    try:
        socket.send(
            json.dumps(
                {
                    "method": "initialize",
                    "id": 1,
                    "params": {
                        "clientInfo": {
                            "name": "patchtrace_t7_observer",
                            "title": "PatchTrace T7 Observer",
                            "version": "0.0.0-throwaway",
                        }
                    },
                }
            )
        )
        initialization = json.loads(socket.recv())
        if initialization.get("id") != 1 or "result" not in initialization:
            raise RuntimeError(f"initialization failed: {initialization!r}")
        socket.send(json.dumps({"method": "initialized", "params": {}}))
        for request_id, thread_id in enumerate(sys.argv[3:], start=100):
            socket.send(
                json.dumps(
                    {
                        "method": "thread/resume",
                        "id": request_id,
                        "params": {"threadId": thread_id},
                    }
                )
            )
        socket.settimeout(180)

        output_path = Path(sys.argv[2])
        with output_path.open("w", encoding="utf-8") as output:
            while True:
                try:
                    message = json.loads(socket.recv())
                except websocket.WebSocketTimeoutException:
                    return 0
                summary = _summarize(message)
                if summary is None:
                    continue
                output.write(json.dumps(summary, sort_keys=True) + "\n")
                output.flush()
                if summary["method"] == "turn/completed":
                    return 0
    finally:
        socket.close()


if __name__ == "__main__":
    raise SystemExit(main())
