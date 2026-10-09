"""CLI contract tests using only the checked-in synthetic receipts."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]


def invoke_cli(tmp_path, manifest, runs, output_format="json"):
    manifest_path = tmp_path / "manifest.json"
    runs_path = tmp_path / "runs.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    runs_path.write_text(json.dumps(runs), encoding="utf-8")
    return invoke_cli_paths(manifest_path, runs_path, output_format)


def invoke_cli_paths(manifest_path, runs_path, output_format="json"):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "context_ablation_lab",
            "analyze",
            str(manifest_path),
            str(runs_path),
            "--format",
            output_format,
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture
def receipts():
    manifest = json.loads((ROOT / "examples" / "manifest.json").read_text(encoding="utf-8"))
    runs = json.loads((ROOT / "examples" / "runs.json").read_text(encoding="utf-8"))
    return manifest, runs


def test_valid_json_cli_exits_zero_and_is_byte_deterministic(tmp_path, receipts):
    manifest, runs = receipts
    first = invoke_cli(tmp_path, manifest, runs)
    second = invoke_cli(tmp_path, manifest, runs)

    assert first.returncode == 0
    assert first.stderr == ""
    assert first.stdout == second.stdout
    assert json.loads(first.stdout) == {
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


def test_valid_text_cli_shows_pair_counts_rates_and_discordance(tmp_path, receipts):
    manifest, runs = receipts
    result = invoke_cli(tmp_path, manifest, runs, output_format="text")
    repeated = invoke_cli(tmp_path, manifest, runs, output_format="text")

    assert result.returncode == 0
    assert result.stdout == repeated.stdout
    lowered = result.stdout.lower()
    for label in ("paired", "short", "expanded", "pass", "50.0%", "discordant"):
        assert label in lowered


def test_malformed_receipt_cli_exits_two(tmp_path, receipts):
    manifest, runs = receipts
    runs["runs"].pop(1)

    result = invoke_cli(tmp_path, manifest, runs)

    assert result.returncode == 2


@pytest.mark.parametrize(
    "invalid_fragment",
    [
        '"evidence": {"score": NaN}',
        '"evidence": "first", "evidence": "second"',
    ],
    ids=["non-finite-number", "duplicate-key"],
)
def test_nonstandard_or_ambiguous_json_is_rejected(tmp_path, receipts, invalid_fragment):
    manifest, runs = receipts
    manifest_path = tmp_path / "manifest.json"
    runs_path = tmp_path / "runs.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    valid_evidence = json.dumps(runs["runs"][0]["evidence"])
    raw_runs = json.dumps(runs).replace(f'"evidence": {valid_evidence}', invalid_fragment, 1)
    runs_path.write_text(raw_runs, encoding="utf-8")

    result = invoke_cli_paths(manifest_path, runs_path)

    assert result.returncode == 2
    assert result.stdout == ""
    assert "context-ablate:" in result.stderr
