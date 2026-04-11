from __future__ import annotations

import json
from pathlib import Path

from chainvalley.export import RunRecord, write_run_record


def run_condition(
    hard_rule: bool,
    seed: int,
    max_rounds: int = 30,
    *,
    out_dir: Path | None = None,
) -> Path:
    """Run one experiment condition (placeholder until orchestrator is wired end-to-end)."""
    cond = "hard" if hard_rule else "soft"
    base = out_dir or Path("artifacts") / "runs"
    path = base / f"{cond}_{seed}.json"
    record = RunRecord(
        condition=cond,
        seed=seed,
        rounds=[],
        transcripts=[],
        harvests=[],
        metrics={
            "max_rounds": max_rounds,
            "hard_rule": hard_rule,
            "note": "placeholder until orchestrator runs full rounds",
        },
    )
    write_run_record(path, record)
    return path


def run_batch(
    seeds: list[int] | None = None,
    out_dir: Path | None = None,
) -> list[Path]:
    """10 seeds × 2 conditions (soft/hard), per §4.3 (stub)."""
    seeds = seeds or list(range(10))
    paths: list[Path] = []
    for seed in seeds:
        paths.append(run_condition(False, seed, out_dir=out_dir))
        paths.append(run_condition(True, seed, out_dir=out_dir))
    return paths
