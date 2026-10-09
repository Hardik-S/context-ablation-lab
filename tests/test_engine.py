"""Synthetic contract tests for paired context receipt analysis."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from context_ablation_lab.engine import InputError, analyze


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def receipts():
    manifest = json.loads((ROOT / "examples" / "manifest.json").read_text(encoding="utf-8"))
    runs = json.loads((ROOT / "examples" / "runs.json").read_text(encoding="utf-8"))
    return manifest, runs


def test_valid_fixture_reports_paired_counts_and_condition_rates(receipts):
    manifest, runs = receipts

    result = analyze(manifest, runs)

    assert result == {
        "conditions": {
            "short": {"count": 4, "passed": 2, "failed": 2, "pass_rate": 0.5},
            "expanded": {"count": 4, "passed": 2, "failed": 2, "pass_rate": 0.5},
        },
        "paired": {
            "count": 4,
            "both_pass": 1,
            "both_fail": 1,
            "short_only_pass": 1,
            "expanded_only_pass": 1,
        },
    }


def test_missing_condition_run_is_rejected(receipts):
    manifest, runs = receipts
    runs["runs"].pop(1)

    with pytest.raises(InputError):
        analyze(manifest, runs)


@pytest.mark.parametrize("duplicate", ["task", "run", "replicate"])
def test_duplicate_identifiers_are_rejected(receipts, duplicate):
    manifest, runs = receipts
    if duplicate == "task":
        manifest["tasks"][1]["id"] = manifest["tasks"][0]["id"]
    elif duplicate == "run":
        runs["runs"][1]["run_id"] = runs["runs"][0]["run_id"]
    else:
        manifest["replicates"][1] = manifest["replicates"][0]

    with pytest.raises(InputError):
        analyze(manifest, runs)


@pytest.mark.parametrize("mismatch", ["task_hash", "model", "harness"])
def test_pair_identity_mismatches_are_rejected(receipts, mismatch):
    manifest, runs = receipts
    task = manifest["tasks"][0]
    manifest = {
        "version": 1,
        "conditions": ["short", "expanded"],
        "tasks": [task],
        "replicates": ["replicate-1"],
    }
    pair = copy.deepcopy(runs["runs"][:2])
    if mismatch == "task_hash":
        pair[1]["task_sha256"] = "f" * 64
    else:
        pair[1][mismatch] = "different-synthetic-value"

    with pytest.raises(InputError):
        analyze(manifest, {"version": 1, "runs": pair})


@pytest.mark.parametrize("empty_field", ["tasks", "replicates"])
def test_empty_experiment_design_is_rejected(receipts, empty_field):
    manifest, runs = copy.deepcopy(receipts)
    manifest[empty_field] = []
    runs["runs"] = []

    with pytest.raises(InputError, match="at least one"):
        analyze(manifest, runs)


def test_identical_context_hashes_within_pair_are_rejected(receipts):
    manifest, runs = receipts
    runs["runs"][1]["context_sha256"] = runs["runs"][0]["context_sha256"]

    with pytest.raises(InputError):
        analyze(manifest, runs)


def test_run_with_unlisted_replicate_is_rejected(receipts):
    manifest, runs = receipts
    runs["runs"][1]["replicate"] = "replicate-unlisted"

    with pytest.raises(InputError, match="unknown replicate"):
        analyze(manifest, runs)


@pytest.mark.parametrize(
    ("which", "mutate"),
    [
        ("manifest", lambda value: value.update(version=True)),
        ("manifest", lambda value: value.update(version="1")),
        ("runs", lambda value: value.update(version=True)),
        ("runs", lambda value: value.update(version="1")),
        ("manifest", lambda value: value.update(tasks={})),
        ("manifest", lambda value: value.update(replicates="replicate-1")),
        ("runs", lambda value: value["runs"][0].update(test_passed=1)),
    ],
)
def test_exact_version_and_field_types_are_enforced(receipts, which, mutate):
    manifest, runs = copy.deepcopy(receipts)
    mutate(manifest if which == "manifest" else runs)

    with pytest.raises(InputError):
        analyze(manifest, runs)


def test_analyze_is_deterministic_and_preserves_documented_key_order(receipts):
    manifest, runs = receipts
    first = analyze(manifest, runs)
    second = analyze(copy.deepcopy(manifest), copy.deepcopy(runs))

    assert first == second
    assert list(first) == ["conditions", "paired"]
    assert list(first["conditions"]) == ["short", "expanded"]
    assert list(first["paired"]) == [
        "count",
        "both_pass",
        "both_fail",
        "short_only_pass",
        "expanded_only_pass",
    ]
    assert json.dumps(first, separators=(",", ":")) == json.dumps(second, separators=(",", ":"))
