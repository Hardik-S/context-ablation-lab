"""Deterministic validation and paired descriptive analysis for ablation runs."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any


class InputError(ValueError):
    """Raised when a manifest or run collection violates the input contract."""


_HEX_SHA256 = re.compile(r"[0-9a-fA-F]{64}\Z")
_CONDITIONS = ("short", "expanded")


def _object(value: Any, label: str, keys: set[str]) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise InputError(f"{label} must be an object")
    if set(value) != keys:
        missing = sorted(keys - set(value))
        extra = sorted(set(value) - keys)
        details = []
        if missing:
            details.append(f"missing keys: {', '.join(missing)}")
        if extra:
            details.append(f"unexpected keys: {', '.join(extra)}")
        raise InputError(f"{label} has invalid shape ({'; '.join(details)})")
    return value


def _version(value: Any, label: str) -> None:
    if type(value) is not int or value != 1:
        raise InputError(f"{label}.version must be the integer 1")


def _identifier(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InputError(f"{label} must be a non-empty string")
    return value


def _sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or _HEX_SHA256.fullmatch(value) is None:
        raise InputError(f"{label} must be a 64-character SHA-256 hex digest")
    return value.lower()


def _sequence(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise InputError(f"{label} must be a list")
    return value


def analyze(manifest: dict, runs: dict) -> dict:
    """Validate matching experiment runs and return deterministic descriptive counts.

    This function only summarizes recorded booleans. It does not estimate
    significance, causality, costs, or any model behavior.
    """
    manifest = _object(manifest, "manifest", {"version", "conditions", "tasks", "replicates"})
    runs = _object(runs, "runs document", {"version", "runs"})
    _version(manifest["version"], "manifest")
    _version(runs["version"], "runs")

    conditions = _sequence(manifest["conditions"], "manifest.conditions")
    if conditions != list(_CONDITIONS):
        raise InputError("manifest.conditions must be ['short', 'expanded'] in that order")

    task_records = _sequence(manifest["tasks"], "manifest.tasks")
    if not task_records:
        raise InputError("manifest.tasks must contain at least one task")
    tasks: dict[str, str] = {}
    for index, raw in enumerate(task_records):
        item = _object(raw, f"manifest.tasks[{index}]", {"id", "sha256"})
        task_id = _identifier(item["id"], f"manifest.tasks[{index}].id")
        if task_id in tasks:
            raise InputError(f"duplicate task id: {task_id}")
        tasks[task_id] = _sha256(item["sha256"], f"manifest.tasks[{index}].sha256")

    replicate_records = _sequence(manifest["replicates"], "manifest.replicates")
    if not replicate_records:
        raise InputError("manifest.replicates must contain at least one replicate")
    replicates: list[str] = []
    seen_replicates: set[str] = set()
    for index, value in enumerate(replicate_records):
        replicate = _identifier(value, f"manifest.replicates[{index}]")
        if replicate in seen_replicates:
            raise InputError(f"duplicate replicate id: {replicate}")
        seen_replicates.add(replicate)
        replicates.append(replicate)

    normalized: dict[tuple[str, str, str], dict[str, Any]] = {}
    seen_run_ids: set[str] = set()
    run_keys = {
        "run_id", "task_id", "task_sha256", "condition", "replicate", "model",
        "harness", "context_sha256", "test_passed", "evidence",
    }
    for index, raw in enumerate(_sequence(runs["runs"], "runs.runs")):
        label = f"runs.runs[{index}]"
        item = _object(raw, label, run_keys)
        run_id = _identifier(item["run_id"], f"{label}.run_id")
        if run_id in seen_run_ids:
            raise InputError(f"duplicate run id: {run_id}")
        seen_run_ids.add(run_id)
        task_id = _identifier(item["task_id"], f"{label}.task_id")
        if task_id not in tasks:
            raise InputError(f"{label} refers to unknown task id: {task_id}")
        task_hash = _sha256(item["task_sha256"], f"{label}.task_sha256")
        if task_hash != tasks[task_id]:
            raise InputError(f"{label}.task_sha256 does not match the manifest")
        condition = item["condition"]
        if condition not in _CONDITIONS or not isinstance(condition, str):
            raise InputError(f"{label}.condition must be 'short' or 'expanded'")
        replicate = _identifier(item["replicate"], f"{label}.replicate")
        if replicate not in seen_replicates:
            raise InputError(f"{label} refers to unknown replicate: {replicate}")
        model = _identifier(item["model"], f"{label}.model")
        harness = _identifier(item["harness"], f"{label}.harness")
        context_hash = _sha256(item["context_sha256"], f"{label}.context_sha256")
        if type(item["test_passed"]) is not bool:
            raise InputError(f"{label}.test_passed must be a boolean")
        if not isinstance(item["evidence"], (str, list, dict)):
            raise InputError(f"{label}.evidence must be a string, list, or object")
        key = (task_id, replicate, condition)
        if key in normalized:
            raise InputError(f"duplicate run for task {task_id}, replicate {replicate}, condition {condition}")
        normalized[key] = {
            "run_id": run_id,
            "task_sha256": task_hash,
            "condition": condition,
            "replicate": replicate,
            "model": model,
            "harness": harness,
            "context_sha256": context_hash,
            "test_passed": item["test_passed"],
        }

    expected = {
        (task_id, replicate, condition)
        for task_id in tasks
        for replicate in replicates
        for condition in _CONDITIONS
    }
    missing = expected - normalized.keys()
    unexpected = normalized.keys() - expected
    if missing or unexpected:
        if missing:
            task_id, replicate, condition = sorted(missing)[0]
            raise InputError(f"missing run for task {task_id}, replicate {replicate}, condition {condition}")
        raise InputError("runs contain entries outside the manifest task-by-replicate design")

    paired = {"both_pass": 0, "both_fail": 0, "short_only_pass": 0, "expanded_only_pass": 0}
    for task_id in sorted(tasks):
        for replicate in sorted(replicates):
            short = normalized[(task_id, replicate, "short")]
            expanded = normalized[(task_id, replicate, "expanded")]
            for field in ("task_sha256", "model", "harness", "replicate"):
                if short[field] != expanded[field]:
                    raise InputError(
                        f"paired runs for task {task_id}, replicate {replicate} have mismatched {field}"
                    )
            if short["context_sha256"] == expanded["context_sha256"]:
                raise InputError(
                    f"paired runs for task {task_id}, replicate {replicate} must have different context hashes"
                )
            short_passed = short["test_passed"]
            expanded_passed = expanded["test_passed"]
            if short_passed and expanded_passed:
                paired["both_pass"] += 1
            elif not short_passed and not expanded_passed:
                paired["both_fail"] += 1
            elif short_passed:
                paired["short_only_pass"] += 1
            else:
                paired["expanded_only_pass"] += 1

    condition_stats = {}
    for condition in _CONDITIONS:
        outcomes = [item["test_passed"] for item in normalized.values() if item["condition"] == condition]
        count = len(outcomes)
        passed = sum(outcomes)
        condition_stats[condition] = {
            "count": count,
            "passed": passed,
            "failed": count - passed,
            "pass_rate": passed / count if count else None,
        }

    return {
        "conditions": condition_stats,
        "paired": {"count": sum(paired.values()), **paired},
    }
