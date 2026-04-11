from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class RunRecord:
    condition: str
    seed: int
    rounds: list[dict[str, Any]] = field(default_factory=list)
    transcripts: list[dict[str, Any]] = field(default_factory=list)
    harvests: list[dict[str, Any]] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)


def run_record_to_json(record: RunRecord) -> str:
    return json.dumps(asdict(record), ensure_ascii=False, indent=2)


def write_run_record(path: Path, record: RunRecord) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(run_record_to_json(record), encoding="utf-8")
