from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .interfaces import AuditEvent, AuditLogSink


def default_audit_dir(root: str | Path) -> Path:
    return Path(root) / "state" / "audit"


def _normalize_payload(payload: object) -> object:
    if is_dataclass(payload):
        return asdict(payload)
    if isinstance(payload, dict):
        return {str(key): _normalize_payload(value) for key, value in payload.items()}
    if isinstance(payload, list):
        return [_normalize_payload(item) for item in payload]
    if isinstance(payload, tuple):
        return [_normalize_payload(item) for item in payload]
    return payload


def append_jsonl_record(
    *,
    root: str | Path,
    stream_name: str,
    payload: dict[str, object],
    audit_dir: str | Path | None = None,
) -> Path:
    target_dir = Path(audit_dir) if audit_dir else default_audit_dir(root)
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / f"{stream_name}.jsonl"
    record = {
        "recorded_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        **_normalize_payload(payload),
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=True, sort_keys=True))
        handle.write("\n")
    return path


def read_latest_jsonl_record(
    *,
    root: str | Path,
    stream_name: str,
    audit_dir: str | Path | None = None,
) -> dict[str, Any] | None:
    target_dir = Path(audit_dir) if audit_dir else default_audit_dir(root)
    path = target_dir / f"{stream_name}.jsonl"
    if not path.exists():
        return None
    last_line = ""
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                last_line = stripped
    if not last_line:
        return None
    return json.loads(last_line)


class JsonlAuditLogSink(AuditLogSink):
    def __init__(self, *, root: str | Path, audit_dir: str | Path | None = None) -> None:
        self._root = Path(root)
        self._audit_dir = Path(audit_dir) if audit_dir else None

    def write(self, event: AuditEvent) -> None:
        append_jsonl_record(
            root=self._root,
            audit_dir=self._audit_dir,
            stream_name="audit_events",
            payload={
                "event_type": event.event_type,
                "reference_id": event.reference_id,
                "payload": event.payload,
            },
        )
