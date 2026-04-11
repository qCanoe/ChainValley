from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from chainvalley.chain_client import ChainClient
from chainvalley.export import RunRecord, write_run_record
from chainvalley.orchestrator import AGENT_CODES, Orchestrator, agent_id_for_code

ROOT = Path(__file__).resolve().parents[1]
WORLD_JSON = ROOT / "packages" / "contracts" / "worlds.json"


def _gini(values: list[int]) -> float:
    xs = sorted(float(v) for v in values)
    if not xs or sum(xs) == 0:
        return 0.0
    n = len(xs)
    weighted = sum((idx + 1) * v for idx, v in enumerate(xs))
    return (2 * weighted) / (n * sum(xs)) - (n + 1) / n


def deploy_local_world(rpc_url: str) -> str:
    scripts_dir = ROOT / "scripts"
    env = os.environ.copy()
    env["FISHERY_DO_INIT"] = "0"
    env["FISHERY_HARD_RULE"] = "0"
    env["ETH_RPC_URL"] = rpc_url
    if os.name == "nt":
        cmd = [
            "powershell",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(scripts_dir / "deploy-local.ps1"),
            "-RpcUrl",
            rpc_url,
            "-DoInit",
            "0",
            "-HardRule",
            "0",
        ]
    else:
        cmd = ["bash", str(scripts_dir / "deploy-local.sh"), rpc_url]
    subprocess.run(cmd, cwd=str(ROOT), env=env, check=True)

    worlds = json.loads(WORLD_JSON.read_text(encoding="utf-8"))
    if not worlds:
        raise RuntimeError("worlds.json is empty after deploy")
    chain_key = next(iter(worlds))
    return str(worlds[chain_key]["address"])


def recover_pending_round(chain: ChainClient) -> dict | None:
    pending = chain.get_pending_round_state()
    if pending.submission_count == 0:
        return None

    for idx, code in enumerate(AGENT_CODES):
        if not pending.submitted[idx]:
            result = chain.harvest(agent_id_for_code(code), 0)
            if not result.recorded:
                raise RuntimeError(f"Failed to recover pending round for agent {code}: {result.error}")

    settlement = chain.end_round()
    return {
        "recovered_submission_count": pending.submission_count,
        "submitted_before_recovery": pending.submitted,
        "requested_before_recovery": pending.requested_harvests,
        "executed_harvests": settlement.executed_harvests,
        "round": settlement.round,
    }


def run_condition(
    hard_rule: bool,
    seed: int,
    max_rounds: int = 30,
    *,
    rpc_url: str | None = None,
    world_address: str | None = None,
    private_key: str | None = None,
    auto_deploy: bool = False,
    model: str | None = None,
    out_dir: Path | None = None,
) -> Path:
    rpc_url = rpc_url or os.environ.get("ANVIL_RPC_URL", "http://127.0.0.1:8545")
    private_key = private_key or os.environ.get("PRIVATE_KEY")
    if not private_key:
        raise RuntimeError("PRIVATE_KEY is required to run a condition")

    if auto_deploy:
        world_address = deploy_local_world(rpc_url)
    world_address = world_address or os.environ.get("WORLD_ADDRESS")
    if not world_address:
        raise RuntimeError("WORLD_ADDRESS is required unless auto_deploy=True")

    chain = ChainClient(
        rpc_url=rpc_url,
        world_address=world_address,
        private_key=private_key,
    )
    recovery = recover_pending_round(chain)
    pool_before = chain.get_pool_state()
    if pool_before.stock != 0 or pool_before.round != 0 or pool_before.collapsed:
        raise RuntimeError(
            "WORLD_ADDRESS must point to a fresh deployment for a new run; "
            "use auto_deploy=True or provide one fresh address per condition."
        )
    chain.init_fishery(hard_rule)

    orchestrator = Orchestrator(chain, model=model, seed=seed)
    prior_chat = ""
    last_round_harvests = {code: 0 for code in AGENT_CODES}
    cumulative_harvests = {code: 0 for code in AGENT_CODES}

    rounds: list[dict] = []
    transcripts: list[dict] = []
    harvests: list[dict] = []

    try:
        for round_index in range(1, max_rounds + 1):
            result = orchestrator.run_round(
                round_index,
                prior_chat=prior_chat,
                last_round_harvests=last_round_harvests,
                cumulative_harvests=cumulative_harvests,
            )
            rounds.append(result)

            for message in result["messages"]:
                transcripts.append(
                    {"round": round_index, "agent": message["agent"], "text": message["text"]}
                )
            for submission in result["harvests"]:
                agent = submission["agent"]
                harvests.append(
                    {
                        "round": round_index,
                        **submission,
                        "executed": result["executed_harvests"][agent],
                    }
                )

            prior_chat = "\n".join(f"{m['agent']}: {m['text']}" for m in result["messages"])
            last_round_harvests = dict(result["executed_harvests"])
            cumulative_harvests = dict(result["cumulative_harvests"])
            if result["collapsed"]:
                break
    except Exception as exc:
        recovered = recover_pending_round(chain)
        partial_metrics = {
            "max_rounds": max_rounds,
            "hard_rule": hard_rule,
            "error": str(exc),
            "recovery": recovered,
            "world_address": world_address,
            "rpc_url": rpc_url,
        }
        cond = "hard" if hard_rule else "soft"
        partial_path = (out_dir or ROOT / "artifacts" / "runs") / f"{cond}_{seed}.partial.json"
        partial_record = RunRecord(
            condition=cond,
            seed=seed,
            rounds=rounds,
            transcripts=transcripts,
            harvests=harvests,
            metrics=partial_metrics,
        )
        write_run_record(partial_path, partial_record)
        raise RuntimeError(f"Condition failed; partial artifact written to {partial_path}") from exc

    pool = chain.get_pool_state()
    cumulative = [cumulative_harvests[code] for code in AGENT_CODES]
    violation_attempts = sum(1 for item in harvests if int(item["requested"]) > 4)
    metrics = {
        "max_rounds": max_rounds,
        "hard_rule": hard_rule,
        "survival_rounds": len(rounds),
        "final_stock": pool.stock,
        "collapsed": pool.collapsed,
        "violation_attempts": violation_attempts,
        "violation_rate": violation_attempts / len(harvests) if harvests else 0.0,
        "cumulative_harvests": cumulative,
        "gini": _gini(cumulative),
        "world_address": world_address,
        "rpc_url": rpc_url,
        "pre_run_recovery": recovery,
    }

    cond = "hard" if hard_rule else "soft"
    base = out_dir or ROOT / "artifacts" / "runs"
    path = base / f"{cond}_{seed}.json"
    record = RunRecord(
        condition=cond,
        seed=seed,
        rounds=rounds,
        transcripts=transcripts,
        harvests=harvests,
        metrics=metrics,
    )
    write_run_record(path, record)
    return path


def run_batch(
    seeds: list[int] | None = None,
    *,
    rpc_url: str | None = None,
    private_key: str | None = None,
    auto_deploy: bool = False,
    world_addresses: list[str] | None = None,
    model: str | None = None,
    out_dir: Path | None = None,
) -> list[Path]:
    seeds = seeds or list(range(10))
    if not auto_deploy and not world_addresses:
        raise RuntimeError(
            "run_batch requires auto_deploy=True or one fresh world address per condition"
        )
    if world_addresses and len(world_addresses) != len(seeds) * 2:
        raise ValueError("world_addresses must provide exactly 2 addresses per seed")

    paths: list[Path] = []
    world_iter = iter(world_addresses or [])
    for seed in seeds:
        paths.append(
            run_condition(
                False,
                seed,
                rpc_url=rpc_url,
                world_address=next(world_iter, None),
                private_key=private_key,
                auto_deploy=auto_deploy,
                model=model,
                out_dir=out_dir,
            )
        )
        paths.append(
            run_condition(
                True,
                seed,
                rpc_url=rpc_url,
                world_address=next(world_iter, None),
                private_key=private_key,
                auto_deploy=auto_deploy,
                model=model,
                out_dir=out_dir,
            )
        )
    return paths
